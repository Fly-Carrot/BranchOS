#!/usr/bin/env python3
"""Local BranchOS checkpoint adapter.

This script validates a project-local BranchOS state file and appends a compact
local branch event. It intentionally does not write global memory or sync logs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CHECKPOINTS = {"task_start", "pre_dispatch", "pre_merge", "final_response"}


def workspace_root() -> Path:
    return Path.cwd()


def local_now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse state file as JSON-compatible YAML: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"State file must contain an object: {path}")
    return data


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    root = workspace_root()
    parser = argparse.ArgumentParser(description="Run a local BranchOS checkpoint.")
    parser.add_argument("--checkpoint", required=True, choices=sorted(CHECKPOINTS))
    parser.add_argument("--state", type=Path, default=root / ".agents" / "branchos" / "branch_state.yaml")
    parser.add_argument("--events", type=Path, default=root / ".agents" / "branchos" / "branch_events.ndjson")
    parser.add_argument("--validator", type=Path, default=root / "skills" / "branchos" / "scripts" / "validate_branch_state.py")
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    state = load_state(args.state)
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
    print(json.dumps({"event_written": str(args.events), **validation}, ensure_ascii=False, indent=2))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
