#!/usr/bin/env python3
"""Resolve a Branch Builder branch after dispatch or review."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


FINAL_STATUSES = {"merged", "blocked", "pruned"}


def local_now() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Branch Builder state file not found: {path}. Run init_branch_state.py first.") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot parse Branch Builder state file: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Branch Builder state must be a JSON object: {path}")
    return data


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def branch_groups(state: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    for key in ("working_branches", "standing_branches"):
        branches = [branch for branch in as_list(state.get(key)) if isinstance(branch, dict)]
        groups.append((key, branches))
    return groups


def update_budget(state: dict[str, Any]) -> None:
    budget = state.setdefault("branch_budget", {})
    standing = [branch for branch in as_list(state.get("standing_branches")) if isinstance(branch, dict)]
    active_working = [
        branch
        for branch in as_list(state.get("working_branches"))
        if isinstance(branch, dict)
        and branch.get("status") in {"proposed", "active", "reviewing", "ready_to_merge"}
    ]
    budget["standing_count"] = len(standing)
    budget["active_working_count"] = len(active_working)
    budget.setdefault("soft_cap", 8)
    budget.setdefault("over_budget_reason", "")


def remove_from_merge_queue(state: dict[str, Any], branch_id: str) -> None:
    queue = as_list(state.get("merge_queue"))
    state["merge_queue"] = [item for item in queue if item != branch_id]


def add_to_merge_queue(state: dict[str, Any], branch_id: str) -> None:
    queue = as_list(state.get("merge_queue"))
    if branch_id not in queue:
        queue.append(branch_id)
    state["merge_queue"] = queue


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve a Branch Builder branch.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--branch-id", required=True)
    parser.add_argument(
        "--status",
        required=True,
        choices=["reviewing", "ready_to_merge", "merged", "blocked", "pruned"],
    )
    parser.add_argument("--output", action="append", default=[])
    parser.add_argument("--conflict", action="append", default=[])
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    state_path = (args.state or workspace / ".agents" / "branch-builder" / "branch_state.yaml").expanduser().resolve()
    events_path = (args.events or workspace / ".agents" / "branch-builder" / "branch_events.ndjson").expanduser().resolve()
    state = load_state(state_path)

    found = False
    now = local_now()
    for key, branches in branch_groups(state):
        for branch in branches:
            if branch.get("id") != args.branch_id:
                continue
            found = True
            branch["status"] = args.status
            branch["last_updated"] = now
            if args.output:
                branch.setdefault("outputs", [])
                branch["outputs"].extend(args.output)
            if args.conflict:
                branch.setdefault("conflicts", [])
                branch["conflicts"].extend(args.conflict)
            state[key] = branches
            break
        if found:
            break
    if not found:
        raise SystemExit(f"Branch not found: {args.branch_id}")

    if args.status == "ready_to_merge":
        add_to_merge_queue(state, args.branch_id)
    elif args.status in FINAL_STATUSES:
        remove_from_merge_queue(state, args.branch_id)
    update_budget(state)
    write_state(state_path, state)

    event = {
        "timestamp": now,
        "event": "resolve_branch",
        "task_id": str(state.get("root_task", {}).get("id") or "session"),
        "workspace": str(workspace),
        "status": "ok",
        "branch_id": args.branch_id,
        "branch_status": args.status,
        "summary": args.summary or f"Resolved Branch Builder branch {args.branch_id} as {args.status}",
        "errors": [],
    }
    append_event(events_path, event)
    result = {
        "status": "ok",
        "branch_id": args.branch_id,
        "branch_status": args.status,
        "state": str(state_path),
        "events": str(events_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
