#!/usr/bin/env python3
"""Install Branch Builder into a Global Agent Fabric shared skill root.

The installer copies the portable Branch Builder planning-layer package into
`<global-root>/skills/generated/branch-builder`, registers it as a critical shared
asset, and can add a managed global-rule block so Gemini/Antigravity runtimes
check the shared protocol source before declaring Branch Builder unavailable in a workspace.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


RULE_START = "## BRANCH_BUILDER_SHARED_PLANNING_LAYER_START"
RULE_END = "## BRANCH_BUILDER_SHARED_PLANNING_LAYER_END"
OLD_RULE_START = "## BRANCHOS_SHARED_PLANNING_LAYER_START"
OLD_RULE_END = "## BRANCHOS_SHARED_PLANNING_LAYER_END"
REGISTRY_START = "  # branch-builder-managed:start"
REGISTRY_END = "  # branch-builder-managed:end"
OLD_REGISTRY_START = "  # branchos-managed:start"
OLD_REGISTRY_END = "  # branchos-managed:end"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def copy_skill(source: Path, target: Path) -> None:
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Branch Builder protocol source missing SKILL.md: {source}")
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    shutil.copytree(source, target, ignore=ignore)


def replace_block(text: str, start: str, end: str, block: str) -> str:
    if start in text and end in text:
        before = text.split(start, 1)[0].rstrip()
        after = text.split(end, 1)[1].lstrip()
        return f"{before}\n\n{block}\n\n{after}".rstrip() + "\n"
    return text.rstrip() + "\n\n" + block.rstrip() + "\n"


def replace_managed_block(text: str, start: str, end: str, old_start: str, old_end: str, block: str) -> str:
    if start in text and end in text:
        return replace_block(text, start, end, block)
    if old_start in text and old_end in text:
        return replace_block(text, old_start, old_end, block)
    return replace_block(text, start, end, block)


def update_registry(registry_path: Path, global_root: Path, project_root: Path) -> None:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    text = registry_path.read_text(encoding="utf-8") if registry_path.exists() else "version: 1\ncritical_assets:\n"
    if "critical_assets:" not in text:
        text = text.rstrip() + "\ncritical_assets:\n"

    block = "\n".join(
        [
            REGISTRY_START,
            '  - id: "branch-builder"',
            '    type: "planning_layer"',
            f'    source_repo: "{project_root}"',
            f'    source_path: "{global_root / "skills" / "generated" / "branch-builder"}"',
            '    role: "shared_virtual_task_branch_planner"',
            '    usage: "Activate once per medium/complex root task, plan work as virtual task branches, route branch packets to tools/skills/subagents, and validate merges before synthesis."',
            "    writes_to:",
            '      - "workspace-local .agents/branch-builder/branch_state.yaml"',
            '      - "workspace-local .agents/branch-builder/branch_events.ndjson"',
            REGISTRY_END,
        ]
    )
    registry_path.write_text(
        replace_managed_block(text, REGISTRY_START, REGISTRY_END, OLD_REGISTRY_START, OLD_REGISTRY_END, block),
        encoding="utf-8",
    )


def update_generated_skill_count(sources_path: Path, global_root: Path) -> None:
    if not sources_path.exists():
        return
    count = len(list((global_root / "skills" / "generated").glob("*/SKILL.md")))
    lines = sources_path.read_text(encoding="utf-8").splitlines()
    rendered: list[str] = []
    in_generated = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("id:") and "generated-shared-fabric-skills" in stripped:
            in_generated = True
            rendered.append(line)
            continue
        if in_generated and stripped.startswith("skill_count:"):
            prefix = line[: len(line) - len(line.lstrip())]
            rendered.append(f"{prefix}skill_count: {count}")
            in_generated = False
            continue
        if in_generated and stripped.startswith("id:"):
            in_generated = False
        rendered.append(line)
    sources_path.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")


def render_global_rule(global_root: Path) -> str:
    skill_root = global_root / "skills" / "generated" / "branch-builder"
    init = skill_root / "scripts" / "init_branch_state.py"
    prepare = skill_root / "scripts" / "prepare_dispatch.py"
    resolve = skill_root / "scripts" / "resolve_branch.py"
    checkpoint = skill_root / "scripts" / "branch_builder_checkpoint.py"
    return "\n".join(
        [
            RULE_START,
            "",
            "MANDATORY: Branch Builder 共享规划层（Shared Planning Layer）—— 对 medium / complex 根任务，在 canonical boot 与上下文加载之后、专门能力分发之前，必须评估是否启用 Branch Builder。Branch Builder 是一次性 root-task planning protocol，不是传统可反复调用的 skill，也不是 Git 分支；它不替代 shared-fabric 的 preflight、六阶段 phase logging 或 postflight sync。",
            "",
            f"- Shared Branch Builder protocol source: `{skill_root}`",
            f"- Shared Branch Builder init script: `{init}`",
            f"- Shared Branch Builder prepare-dispatch script: `{prepare}`",
            f"- Shared Branch Builder resolve-branch script: `{resolve}`",
            f"- Shared Branch Builder checkpoint script: `{checkpoint}`",
            "- Workspace-local state remains under `<workspace>/.agents/branch-builder/branch_state.yaml` and `<workspace>/.agents/branch-builder/branch_events.ndjson`.",
            "- Do not claim Branch Builder is unavailable merely because the current workspace lacks `skills/branch-builder` or `.agents/branch-builder/branch_builder_checkpoint.py`; check the shared protocol source first.",
            "- If the shared protocol source exists, activate Branch Builder from Global Agent Fabric and create/load only the workspace-local branch state.",
            "- If `init_branch_state.py` receives a new explicit `--objective` that differs from the existing root task, it archives the previous state and starts a fresh task unless `--continue-existing` is passed.",
            "- Never initialize Branch Builder with `touch` or `echo '{}'`; missing, empty, or invalid state must be initialized or repaired with the shared init script.",
            "- Run Branch Builder state-changing commands serially. Do not parallelize `init_branch_state.py`, `prepare_dispatch.py`, `resolve_branch.py`, or `branch_builder_checkpoint.py`; checkpoints must read the state written by the previous command.",
            "- Never repair a `pre_dispatch` failure with `init --force`. `pre_dispatch` needs a working branch packet; create or update it with the shared prepare-dispatch script.",
            "- Before `pre_merge`, resolve merge-ready working branches with the shared resolve-branch script as `ready_to_merge`; before `final_response`, resolve open working branches as `merged`, `blocked`, or `pruned`.",
            "- A Branch Builder `final_response` error should be reported as `[BRANCH_BUILDER_OPEN]` or `[BRANCH_BUILDER_ERROR]`, but it must not prevent canonical `postflight_sync.py` from running.",
            "- Branch Builder checkpoint scripts emit stable `status_marker` values. Report `[BRANCH_BUILDER_ACTIVE]` only after `task_start` returns that marker; report `[BRANCH_BUILDER_REPORT]` only after `final_response` returns that marker.",
            "- Every Branch Builder checkpoint that succeeds must be followed by a user-visible Branch Builder receipt in the assistant response. Do not leave the branch map only inside hidden shell/tool output.",
            "- A Branch Builder receipt must include: `status_marker`, root objective, current phase, standing branches, working branches, merge queue, pruned branches, and unresolved/open branches when present.",
            "- At task start, print the receipt immediately after `[BRANCH_BUILDER_ACTIVE]`. Before final response, print the final receipt immediately after `[BRANCH_BUILDER_REPORT]`, `[BRANCH_BUILDER_OPEN]`, or `[BRANCH_BUILDER_ERROR]`.",
            "- Do not run `preflight_check.py` or `sync_all.py` per virtual branch.",
            "- Do not emit the full `route -> plan -> review -> dispatch -> execute -> report` lifecycle per virtual branch. The root task gets one canonical lifecycle; Branch Builder maintains branch state inside it.",
            "",
            "When Branch Builder is active:",
            "1. Activate the Branch Builder protocol package from the shared source once for the root task.",
            f"2. Create or repair `<workspace>/.agents/branch-builder/branch_state.yaml`: `python3 {init} --workspace <workspace> --objective \"<current task objective>\" --complexity medium`.",
            f"3. Run task-start checkpoint: `python3 {checkpoint} --workspace <workspace> --checkpoint task_start --emit-summary`.",
            "4. After `task_start`, copy the returned `status_marker` and `branch_builder_summary` into a concise user-visible receipt.",
            f"5. Before specialized skill/MCP/script/Maestro/subagent dispatch, create a working branch packet: `python3 {prepare} --workspace <workspace> --name \"<dispatch branch>\" --scope \"<bounded scope>\" --expected-output \"<expected result>\" --capability scripts:\"<tool or command>\"`, then run: `python3 {checkpoint} --workspace <workspace> --checkpoint pre_dispatch --emit-summary`.",
            f"6. Before merging branch outputs into root synthesis, mark merge-ready branches: `python3 {resolve} --workspace <workspace> --branch-id <B###> --status ready_to_merge --output \"<branch result>\"`, then run: `python3 {checkpoint} --workspace <workspace> --checkpoint pre_merge --emit-summary`.",
            f"7. Before final response and canonical postflight, resolve each open working branch: `python3 {resolve} --workspace <workspace> --branch-id <B###> --status <merged|blocked|pruned> --output \"<branch result>\"`, then run: `python3 {checkpoint} --workspace <workspace> --checkpoint final_response --emit-summary --emit-delta`.",
            "8. After `final_response`, copy the returned `status_marker`, `branch_builder_summary`, and `branch_builder_delta` into the final answer before `[SYNC_OK]`.",
            "9. If neither shared nor local Branch Builder exists, say so explicitly and fall back to the normal shared-fabric workflow.",
            "",
            RULE_END,
        ]
    )


def update_global_rule(rule_path: Path, global_root: Path) -> None:
    text = rule_path.read_text(encoding="utf-8") if rule_path.exists() else ""
    rule_path.write_text(
        replace_managed_block(text, RULE_START, RULE_END, OLD_RULE_START, OLD_RULE_END, render_global_rule(global_root)),
        encoding="utf-8",
    )


def run_export(global_root: Path, *, backup: bool) -> None:
    script = global_root / "scripts" / "sync" / "sync_antigravity_customizations.py"
    command = [sys.executable, str(script), "--global-root", str(global_root), "--export"]
    if backup:
        command.append("--backup")
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Branch Builder into Global Agent Fabric.")
    parser.add_argument("--global-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=repo_root())
    parser.add_argument("--update-global-rule", action="store_true")
    parser.add_argument("--export-antigravity", action="store_true")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()

    global_root = args.global_root.expanduser().resolve()
    project_root = args.project_root.expanduser().resolve()
    skill_source = project_root / "skills" / "branch-builder"
    skill_target = global_root / "skills" / "generated" / "branch-builder"
    legacy_skill_target = global_root / "skills" / "generated" / "branchos"

    copy_skill(skill_source, skill_target)
    if legacy_skill_target.exists() and legacy_skill_target != skill_target:
        shutil.rmtree(legacy_skill_target)
    update_registry(global_root / "skills" / "registry.yaml", global_root, project_root)
    update_generated_skill_count(global_root / "skills" / "sources.yaml", global_root)
    if args.update_global_rule:
        update_global_rule(global_root / "rules" / "global" / "gemini-global.md", global_root)
    if args.export_antigravity:
        run_export(global_root, backup=args.backup)

    summary = {
        "status": "ok",
        "global_root": str(global_root),
        "installed_protocol": str(skill_target),
        "registry": str(global_root / "skills" / "registry.yaml"),
        "global_rule_updated": bool(args.update_global_rule),
        "antigravity_exported": bool(args.export_antigravity),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
