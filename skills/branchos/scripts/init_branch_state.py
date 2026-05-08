#!/usr/bin/env python3
"""Initialize or repair a workspace-local BranchOS branch_state file."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_OBJECTIVE = "Activate BranchOS planning layer for the current task."


def local_now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def stamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def default_task_id() -> str:
    return f"BRANCHOS-{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}"


def soft_cap(complexity: str) -> int:
    return {"simple": 4, "medium": 8, "complex": 14}[complexity]


def merge_contract(target: str, purpose: str) -> dict[str, Any]:
    return {
        "merge_into": target,
        "must_satisfy": [
            purpose,
            "No locked user constraint is overridden.",
        ],
        "must_include": [
            "branch status",
            "completed output or explicit blocker",
            "conflict check",
        ],
        "conflict_check": "Compare against root constraints and sibling branch outputs before merge.",
        "new_branch_triggers": [
            "new risk",
            "unresolved dependency",
            "conflict with another branch",
            "missing validation",
        ],
    }


def branch(
    branch_id: str,
    name: str,
    purpose: str,
    deliverables: list[str],
    *,
    now: str,
) -> dict[str, Any]:
    return {
        "id": branch_id,
        "name": name,
        "type": "standing",
        "status": "active",
        "parent": "ROOT",
        "depends_on": [],
        "purpose": purpose,
        "inputs": ["root_task.objective", "root_task.locked_constraints"],
        "allowed_capabilities": {},
        "deliverables": deliverables,
        "merge_contract": merge_contract("ROOT", purpose),
        "outputs": [],
        "conflicts": [],
        "last_updated": now,
    }


def make_state(task_id: str, objective: str, complexity: str) -> dict[str, Any]:
    now = local_now()
    standing = [
        branch(
            "S001",
            "Intent and Constraints",
            "Keep the user's objective, locked constraints, and success criteria visible throughout the task.",
            ["confirmed objective", "locked constraints", "success criteria"],
            now=now,
        ),
        branch(
            "S002",
            "Architecture Boundary",
            "Maintain the task architecture, branch boundaries, dependencies, and routing decisions.",
            ["branch map", "routing notes", "dependency notes"],
            now=now,
        ),
        branch(
            "S003",
            "Verification",
            "Track validation requirements, merge readiness, regressions, and unresolved blockers.",
            ["validation checklist", "merge readiness notes", "blocked/open-loop report"],
            now=now,
        ),
    ]
    return {
        "schema_version": 1,
        "root_task": {
            "id": task_id,
            "objective": objective,
            "complexity": complexity,
            "current_phase": "route",
            "locked_constraints": [],
            "success_criteria": [
                "BranchOS state is valid before task_start checkpoint.",
                "Specialized dispatch uses branch packets when BranchOS is active.",
                "Final synthesis reports unresolved working branches.",
            ],
        },
        "standing_branches": standing,
        "working_branches": [],
        "merge_queue": [],
        "pruned": [],
        "branch_budget": {
            "standing_count": len(standing),
            "active_working_count": 0,
            "soft_cap": soft_cap(complexity),
            "over_budget_reason": "",
        },
    }


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, "missing"
    if not text.strip():
        return None, "empty"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"parse_error: {exc}"
    if not isinstance(data, dict):
        return None, "not_object"
    return data, None


def validate_task_start(state_path: Path, validator: Path) -> tuple[bool, list[str]]:
    completed = subprocess.run(
        [sys.executable, str(validator), str(state_path), "--checkpoint", "task_start"],
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, ["validator did not return JSON", completed.stderr.strip()]
    return completed.returncode == 0, list(payload.get("errors", []))


def backup_existing(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.invalid.{stamp()}")
    shutil.copy2(path, backup)
    return backup


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_event(events_path: Path, event: dict[str, Any]) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Initialize or repair BranchOS branch state.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--validator", type=Path, default=script_dir / "validate_branch_state.py")
    parser.add_argument("--task-id", default=default_task_id())
    parser.add_argument("--objective", default=DEFAULT_OBJECTIVE)
    parser.add_argument("--complexity", choices=["simple", "medium", "complex"], default="medium")
    parser.add_argument("--force", action="store_true", help="Overwrite even when an existing valid state is present.")
    parser.add_argument(
        "--no-repair-invalid",
        action="store_true",
        help="Fail instead of replacing a missing, empty, malformed, or invalid state file.",
    )
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    state_path = (args.state or workspace / ".agents" / "branchos" / "branch_state.yaml").expanduser()
    events_path = (args.events or workspace / ".agents" / "branchos" / "branch_events.ndjson").expanduser()
    state_path = state_path.resolve()
    events_path = events_path.resolve()
    validator = args.validator.expanduser().resolve()

    existing, load_error = load_json(state_path)
    existing_valid = False
    validation_errors: list[str] = []
    if existing is not None and state_path.exists():
        existing_valid, validation_errors = validate_task_start(state_path, validator)

    if existing_valid and not args.force:
        action = "existing_valid_state"
        backup_path = None
    else:
        if args.no_repair_invalid and not args.force:
            reason = load_error or "; ".join(validation_errors) or "invalid"
            print(
                json.dumps(
                    {
                        "status": "error",
                        "action": "not_repaired",
                        "state": str(state_path),
                        "reason": reason,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1
        backup_path = backup_existing(state_path)
        write_state(state_path, make_state(args.task_id, args.objective, args.complexity))
        action = "created_state" if load_error == "missing" else "repaired_or_replaced_state"
        existing_valid, validation_errors = validate_task_start(state_path, validator)

    event = {
        "timestamp": local_now(),
        "event": "init",
        "task_id": args.task_id,
        "workspace": str(workspace),
        "status": "ok" if existing_valid else "error",
        "summary": f"BranchOS state initialization: {action}",
        "state": str(state_path),
        "backup": str(backup_path) if backup_path else "",
        "errors": validation_errors,
    }
    append_event(events_path, event)
    result = {
        "status": "ok" if existing_valid else "error",
        "action": action,
        "workspace": str(workspace),
        "state": str(state_path),
        "events": str(events_path),
        "backup": str(backup_path) if backup_path else "",
        "task_id": args.task_id,
        "validation_errors": validation_errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if existing_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
