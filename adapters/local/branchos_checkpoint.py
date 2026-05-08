#!/usr/bin/env python3
"""Local BranchOS checkpoint adapter.

This script validates a project-local BranchOS state file and appends a compact
local branch event. It intentionally does not write global memory or sync logs.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CHECKPOINTS = {"task_start", "pre_dispatch", "pre_merge", "final_response"}
OPEN_STATUSES = {"proposed", "active", "blocked", "reviewing", "ready_to_merge", "hotfix"}


def initialization_hint(workspace: Path, init_script: Path) -> str:
    return (
        "Do not initialize BranchOS with touch or echo '{}'. Run: "
        f"python3 {shlex.quote(str(init_script))} --workspace {shlex.quote(str(workspace))} "
        '--objective "<current task objective>" --complexity medium'
    )


def workspace_root() -> Path:
    return Path.cwd()


def local_now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_state(path: Path, workspace: Path, init_script: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(
            f"BranchOS state file not found: {path}. "
            + initialization_hint(workspace, init_script)
        ) from exc
    if not text.strip():
        raise SystemExit(
            f"BranchOS state file is empty: {path}. "
            + initialization_hint(workspace, init_script)
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Cannot parse state file as JSON-compatible YAML: {path}: {exc}. "
            + initialization_hint(workspace, init_script)
        ) from exc
    if not isinstance(data, dict):
        raise SystemExit(f"State file must contain an object: {path}")
    return data


def needs_initialization_hint(validation: dict[str, Any]) -> bool:
    errors = " ".join(str(error) for error in validation.get("errors", []))
    markers = (
        "schema_version must be 1",
        "root_task must be an object",
        "task_start requires at least one",
        "branch_budget must be an object",
    )
    return any(marker in errors for marker in markers)


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def all_branches(state: dict[str, Any]) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for key in ("standing_branches", "working_branches"):
        value = state.get(key, [])
        if isinstance(value, list):
            branches.extend(branch for branch in value if isinstance(branch, dict))
    return branches


def branch_label(branch: dict[str, Any]) -> str:
    branch_id = str(branch.get("id") or "UNKNOWN")
    name = str(branch.get("name") or "Unnamed")
    status = str(branch.get("status") or "unknown")
    return f"{branch_id} {name} ({status})"


def checkpoint_summary(state: dict[str, Any], checkpoint: str) -> dict[str, Any]:
    branches = all_branches(state)
    standing = [branch for branch in state.get("standing_branches", []) if isinstance(branch, dict)]
    working = [branch for branch in state.get("working_branches", []) if isinstance(branch, dict)]
    status_counts: dict[str, int] = {}
    for branch in branches:
        status = str(branch.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "checkpoint": checkpoint,
        "root_task": {
            "id": state.get("root_task", {}).get("id"),
            "objective": state.get("root_task", {}).get("objective"),
            "current_phase": state.get("root_task", {}).get("current_phase"),
            "complexity": state.get("root_task", {}).get("complexity"),
        },
        "branch_counts": {
            "standing": len(standing),
            "working": len(working),
            "total": len(branches),
            "by_status": status_counts,
        },
        "standing_branches": [branch_label(branch) for branch in standing],
        "working_branches": [branch_label(branch) for branch in working],
        "merge_queue": state.get("merge_queue", []),
        "pruned": state.get("pruned", []),
    }


def recent_events(path: Path, limit: int = 8) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events[-limit:]


def checkpoint_delta(state: dict[str, Any], events_path: Path) -> dict[str, Any]:
    branches = all_branches(state)
    open_branches = [
        branch_label(branch)
        for branch in branches
        if str(branch.get("status") or "unknown") in OPEN_STATUSES
    ]
    merged_branches = [
        branch_label(branch)
        for branch in branches
        if str(branch.get("status") or "unknown") == "merged"
    ]
    blocked_branches = [
        branch_label(branch)
        for branch in branches
        if str(branch.get("status") or "unknown") == "blocked"
    ]
    return {
        "merged_branches": merged_branches,
        "open_branches": open_branches,
        "blocked_branches": blocked_branches,
        "recent_events": recent_events(events_path),
    }


def main() -> int:
    root = workspace_root()
    parser = argparse.ArgumentParser(description="Run a local BranchOS checkpoint.")
    parser.add_argument("--checkpoint", required=True, choices=sorted(CHECKPOINTS))
    parser.add_argument("--state", type=Path, default=root / ".agents" / "branchos" / "branch_state.yaml")
    parser.add_argument("--events", type=Path, default=root / ".agents" / "branchos" / "branch_events.ndjson")
    parser.add_argument("--validator", type=Path, default=root / "skills" / "branchos" / "scripts" / "validate_branch_state.py")
    parser.add_argument("--summary", default="")
    parser.add_argument("--emit-summary", action="store_true", help="Include a compact branch map summary in the JSON output.")
    parser.add_argument("--emit-delta", action="store_true", help="Include a compact current-state delta and recent branch events.")
    args = parser.parse_args()

    init_script = root / "skills" / "branchos" / "scripts" / "init_branch_state.py"
    state = load_state(args.state, root, init_script)
    task_id = str(state.get("root_task", {}).get("id") or "session")
    command = [
        sys.executable,
        str(args.validator),
        str(args.state),
        "--checkpoint",
        args.checkpoint,
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    try:
        validation: dict[str, Any] = json.loads(completed.stdout)
    except json.JSONDecodeError:
        validation = {
            "status": "error",
            "errors": ["validator did not return JSON"],
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    event = {
        "timestamp": local_now(),
        "event": args.checkpoint,
        "task_id": task_id,
        "status": validation.get("status", "error"),
        "summary": args.summary or f"BranchOS checkpoint {args.checkpoint}",
        "errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
    }
    append_event(args.events, event)
    result = {"event_written": str(args.events), **validation}
    if needs_initialization_hint(validation):
        result["initialization_hint"] = initialization_hint(root, init_script)
    if args.emit_summary:
        result["branchos_summary"] = checkpoint_summary(state, args.checkpoint)
    if args.emit_delta:
        result["branchos_delta"] = checkpoint_delta(state, args.events)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
