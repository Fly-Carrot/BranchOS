#!/usr/bin/env python3
"""Validate a Branch Builder branch_state.yaml file.

The preferred state file is JSON-compatible YAML so this validator can use only
the Python standard library.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_ROOT_FIELDS = {
    "id",
    "objective",
    "complexity",
    "current_phase",
    "locked_constraints",
    "success_criteria",
}
REQUIRED_BRANCH_FIELDS = {
    "id",
    "name",
    "type",
    "status",
    "parent",
    "depends_on",
    "purpose",
    "inputs",
    "allowed_capabilities",
    "deliverables",
    "merge_contract",
    "outputs",
    "conflicts",
    "last_updated",
}
BRANCH_STATES = {
    "proposed",
    "active",
    "blocked",
    "reviewing",
    "ready_to_merge",
    "merged",
    "pruned",
}
BRANCH_TYPES = {
    "standing",
    "working",
    "research",
    "implementation",
    "verification",
    "synthesis",
    "hotfix",
    "rebase",
}
CHECKPOINTS = {"task_start", "pre_dispatch", "pre_merge", "final_response"}


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"{path} must be JSON-compatible YAML for this validator: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object.")
    return data


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def branch_groups(state: dict[str, Any]) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for key in ("standing_branches", "working_branches"):
        for branch in as_list(state.get(key)):
            if isinstance(branch, dict):
                branches.append(branch)
    return branches


def has_dispatch_capability(branch: dict[str, Any]) -> bool:
    capabilities = branch.get("allowed_capabilities")
    if not isinstance(capabilities, dict):
        return False
    return any(bool(value) for value in capabilities.values())


def require_fields(errors: list[str], obj: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(field for field in fields if field not in obj)
    if missing:
        errors.append(f"{label} missing required field(s): {', '.join(missing)}")


def validate_root(state: dict[str, Any], errors: list[str]) -> None:
    if state.get("schema_version") != 1:
        errors.append("schema_version must be 1.")
    root = state.get("root_task")
    if not isinstance(root, dict):
        errors.append("root_task must be an object.")
        return
    require_fields(errors, root, REQUIRED_ROOT_FIELDS, "root_task")
    if root.get("complexity") not in {"simple", "medium", "complex"}:
        errors.append("root_task.complexity must be simple, medium, or complex.")
    if not isinstance(root.get("locked_constraints", []), list):
        errors.append("root_task.locked_constraints must be a list.")
    if not isinstance(root.get("success_criteria", []), list):
        errors.append("root_task.success_criteria must be a list.")


def validate_branch(branch: dict[str, Any], errors: list[str]) -> None:
    label = f"branch {branch.get('id', '<unknown>')}"
    require_fields(errors, branch, REQUIRED_BRANCH_FIELDS, label)
    if branch.get("status") not in BRANCH_STATES:
        errors.append(f"{label} has invalid status: {branch.get('status')}")
    if branch.get("type") not in BRANCH_TYPES:
        errors.append(f"{label} has invalid type: {branch.get('type')}")
    for field in ("depends_on", "inputs", "deliverables", "outputs", "conflicts"):
        if field in branch and not isinstance(branch[field], list):
            errors.append(f"{label}.{field} must be a list.")
    if not isinstance(branch.get("allowed_capabilities", {}), dict):
        errors.append(f"{label}.allowed_capabilities must be an object.")
    merge_contract = branch.get("merge_contract")
    if not isinstance(merge_contract, dict):
        errors.append(f"{label}.merge_contract must be an object.")
        return
    for field in ("merge_into", "must_satisfy", "must_include", "conflict_check", "new_branch_triggers"):
        if field not in merge_contract:
            errors.append(f"{label}.merge_contract missing {field}.")
    for field in ("must_satisfy", "must_include", "new_branch_triggers"):
        if field in merge_contract and not isinstance(merge_contract[field], list):
            errors.append(f"{label}.merge_contract.{field} must be a list.")


def validate_budget(state: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    budget = state.get("branch_budget", {})
    if not isinstance(budget, dict):
        errors.append("branch_budget must be an object.")
        return
    active_working = [
        branch
        for branch in as_list(state.get("working_branches"))
        if isinstance(branch, dict) and branch.get("status") in {"proposed", "active", "reviewing", "ready_to_merge"}
    ]
    active_count = len(active_working)
    soft_cap = budget.get("soft_cap", 8)
    if not isinstance(soft_cap, int) or soft_cap < 1:
        errors.append("branch_budget.soft_cap must be a positive integer.")
        return
    if active_count > soft_cap and not str(budget.get("over_budget_reason", "")).strip():
        warnings.append(
            f"active working branches ({active_count}) exceed soft_cap ({soft_cap}) without over_budget_reason."
        )


def validate_checkpoint(state: dict[str, Any], checkpoint: str | None, errors: list[str]) -> None:
    if checkpoint is None:
        return
    branches = branch_groups(state)
    if checkpoint == "task_start":
        if not branches:
            errors.append("task_start requires at least one standing or working branch.")
    elif checkpoint == "pre_dispatch":
        dispatchable = [
            branch
            for branch in branches
            if branch.get("status") in {"active", "reviewing"}
            and has_dispatch_capability(branch)
        ]
        if not dispatchable:
            errors.append("pre_dispatch requires an active/reviewing branch with allowed_capabilities.")
        for branch in dispatchable:
            packet = branch.get("branch_packet")
            label = f"branch {branch.get('id', '<unknown>')}"
            if not isinstance(packet, dict):
                errors.append(f"{label} requires branch_packet before dispatch.")
                continue
            for field in ("scope", "non_goals", "expected_output", "return_format"):
                if field not in packet:
                    errors.append(f"{label}.branch_packet missing {field}.")
    elif checkpoint == "pre_merge":
        queue = as_list(state.get("merge_queue"))
        if not queue:
            errors.append("pre_merge requires at least one merge_queue entry.")
    elif checkpoint == "final_response":
        unresolved = [
            branch.get("id", "<unknown>")
            for branch in as_list(state.get("working_branches"))
            if isinstance(branch, dict)
            and branch.get("status") in {"proposed", "active", "reviewing", "ready_to_merge"}
        ]
        if unresolved:
            errors.append(
                "final_response has unresolved working branches: " + ", ".join(unresolved)
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Branch Builder branch state.")
    parser.add_argument("state_file", type=Path)
    parser.add_argument("--checkpoint", choices=sorted(CHECKPOINTS))
    args = parser.parse_args()

    state = load_state(args.state_file)
    errors: list[str] = []
    warnings: list[str] = []

    validate_root(state, errors)
    for branch in branch_groups(state):
        validate_branch(branch, errors)
    validate_budget(state, errors, warnings)
    validate_checkpoint(state, args.checkpoint, errors)

    result = {
        "status": "error" if errors else "ok",
        "checkpoint": args.checkpoint or "",
        "errors": errors,
        "warnings": warnings,
        "branch_counts": {
            "standing": len(as_list(state.get("standing_branches"))),
            "working": len(as_list(state.get("working_branches"))),
            "merge_queue": len(as_list(state.get("merge_queue"))),
            "pruned": len(as_list(state.get("pruned"))),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
