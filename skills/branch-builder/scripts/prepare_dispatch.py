#!/usr/bin/env python3
"""Create or update a Branch Builder working branch before specialized dispatch."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


CAPABILITY_KEYS = ("skills", "mcps", "scripts", "subagents", "commands")


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


def next_branch_id(state: dict[str, Any]) -> str:
    highest = 0
    for branch in as_list(state.get("working_branches")):
        if not isinstance(branch, dict):
            continue
        branch_id = str(branch.get("id", ""))
        if len(branch_id) == 4 and branch_id.startswith("B") and branch_id[1:].isdigit():
            highest = max(highest, int(branch_id[1:]))
    return f"B{highest + 1:03d}"


def parse_capability(items: list[str]) -> dict[str, list[str]]:
    capabilities: dict[str, list[str]] = {key: [] for key in CAPABILITY_KEYS}
    for item in items:
        if ":" in item:
            key, value = item.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
        else:
            key = "commands"
            value = item.strip()
        if not value:
            continue
        if key not in capabilities:
            raise SystemExit(
                f"Unsupported capability key {key!r}. Use one of: {', '.join(CAPABILITY_KEYS)}."
            )
        capabilities[key].append(value)
    return capabilities


def merge_contract(target: str, purpose: str) -> dict[str, Any]:
    return {
        "merge_into": target,
        "must_satisfy": [
            purpose,
            "Dispatched work stays inside the branch packet scope.",
            "No locked user constraint is overridden.",
        ],
        "must_include": [
            "dispatch result",
            "artifacts or evidence",
            "conflict check",
            "next merge recommendation",
        ],
        "conflict_check": "Compare dispatch output against root constraints and sibling branches before merge.",
        "new_branch_triggers": [
            "tool failure",
            "unexpected output",
            "new dependency",
            "scope expansion",
            "validation gap",
        ],
    }


def branch_packet(args: argparse.Namespace, capabilities: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "scope": args.scope,
        "non_goals": args.non_goal,
        "expected_output": args.expected_output,
        "return_format": args.return_format,
        "allowed_capabilities": capabilities,
        "route_note": args.route_note,
    }


def make_branch(args: argparse.Namespace, branch_id: str, capabilities: dict[str, list[str]], now: str) -> dict[str, Any]:
    purpose = args.purpose or f"Prepare bounded dispatch for {args.name}."
    return {
        "id": branch_id,
        "name": args.name,
        "type": args.branch_type,
        "status": "active",
        "parent": args.parent,
        "depends_on": args.depends_on,
        "purpose": purpose,
        "inputs": args.input,
        "allowed_capabilities": capabilities,
        "deliverables": args.deliverable,
        "merge_contract": merge_contract(args.merge_into, purpose),
        "outputs": [],
        "conflicts": [],
        "last_updated": now,
        "branch_packet": branch_packet(args, capabilities),
    }


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


def validate_pre_dispatch(state_path: Path, validator: Path) -> tuple[bool, list[str]]:
    completed = subprocess.run(
        [sys.executable, str(validator), str(state_path), "--checkpoint", "pre_dispatch"],
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, ["validator did not return JSON", completed.stderr.strip()]
    return completed.returncode == 0, list(payload.get("errors", []))


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Prepare a Branch Builder branch packet before dispatch.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path)
    parser.add_argument("--events", type=Path)
    parser.add_argument("--validator", type=Path, default=script_dir / "validate_branch_state.py")
    parser.add_argument("--branch-id", default="")
    parser.add_argument("--name", required=True)
    parser.add_argument("--purpose", default="")
    parser.add_argument("--scope", required=True)
    parser.add_argument("--expected-output", required=True)
    parser.add_argument("--capability", action="append", default=[], help="Capability as key:value, e.g. scripts:Rscript.")
    parser.add_argument("--non-goal", action="append", default=[])
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--deliverable", action="append", default=[])
    parser.add_argument("--depends-on", action="append", default=[])
    parser.add_argument("--route-note", default="")
    parser.add_argument("--return-format", default="Brief branch result with artifacts, errors, and merge recommendation.")
    parser.add_argument("--branch-type", choices=["working", "research", "implementation", "verification", "synthesis", "hotfix"], default="working")
    parser.add_argument("--parent", default="ROOT")
    parser.add_argument("--merge-into", default="ROOT")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    state_path = (args.state or workspace / ".agents" / "branch-builder" / "branch_state.yaml").expanduser().resolve()
    events_path = (args.events or workspace / ".agents" / "branch-builder" / "branch_events.ndjson").expanduser().resolve()
    state = load_state(state_path)
    capabilities = parse_capability(args.capability)
    if not any(capabilities.values()):
        raise SystemExit("At least one --capability is required before pre_dispatch.")

    branch_id = args.branch_id or next_branch_id(state)
    now = local_now()
    working = [branch for branch in as_list(state.get("working_branches")) if isinstance(branch, dict)]
    new_branch = make_branch(args, branch_id, capabilities, now)
    replaced = False
    for index, branch_item in enumerate(working):
        if branch_item.get("id") == branch_id:
            working[index] = {**branch_item, **new_branch}
            replaced = True
            break
    if not replaced:
        working.append(new_branch)
    state["working_branches"] = working
    root = state.setdefault("root_task", {})
    if isinstance(root, dict):
        root["current_phase"] = "dispatch"
    update_budget(state)
    write_state(state_path, state)

    ok, errors = validate_pre_dispatch(state_path, args.validator.expanduser().resolve())
    event = {
        "timestamp": now,
        "event": "prepare_dispatch",
        "task_id": str(state.get("root_task", {}).get("id") or "session"),
        "workspace": str(workspace),
        "status": "ok" if ok else "error",
        "branch_id": branch_id,
        "summary": f"Prepared dispatch branch packet for {args.name}",
        "errors": errors,
    }
    append_event(events_path, event)
    result = {
        "status": "ok" if ok else "error",
        "action": "updated_branch" if replaced else "created_branch",
        "branch_id": branch_id,
        "state": str(state_path),
        "events": str(events_path),
        "validation_errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
