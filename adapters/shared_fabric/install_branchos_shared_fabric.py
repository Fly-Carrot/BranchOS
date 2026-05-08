#!/usr/bin/env python3
"""Install BranchOS into a Global Agent Fabric shared skill root.

The installer copies the portable BranchOS skill into
`<global-root>/skills/generated/branchos`, registers it as a critical shared
asset, and can add a managed global-rule block so Gemini/Antigravity runtimes
check the shared skill before declaring BranchOS unavailable in a workspace.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


RULE_START = "## BRANCHOS_SHARED_PLANNING_LAYER_START"
RULE_END = "## BRANCHOS_SHARED_PLANNING_LAYER_END"
REGISTRY_START = "  # branchos-managed:start"
REGISTRY_END = "  # branchos-managed:end"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def copy_skill(source: Path, target: Path) -> None:
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"BranchOS skill source missing SKILL.md: {source}")
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


def update_registry(registry_path: Path, global_root: Path, project_root: Path) -> None:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    text = registry_path.read_text(encoding="utf-8") if registry_path.exists() else "version: 1\ncritical_assets:\n"
    if "critical_assets:" not in text:
        text = text.rstrip() + "\ncritical_assets:\n"

    block = "\n".join(
        [
            REGISTRY_START,
            '  - id: "branchos"',
            '    type: "skill"',
            f'    source_repo: "{project_root}"',
            f'    source_path: "{global_root / "skills" / "generated" / "branchos"}"',
            '    role: "shared_virtual_task_branch_planner"',
            '    usage: "Plan medium and complex work as virtual task branches, route branch packets to tools/skills/subagents, and validate merges before synthesis."',
            "    writes_to:",
            '      - "workspace-local .agents/branchos/branch_state.yaml"',
            '      - "workspace-local .agents/branchos/branch_events.ndjson"',
            REGISTRY_END,
        ]
    )
    registry_path.write_text(replace_block(text, REGISTRY_START, REGISTRY_END, block), encoding="utf-8")


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
    skill_root = global_root / "skills" / "generated" / "branchos"
    init = skill_root / "scripts" / "init_branch_state.py"
    prepare = skill_root / "scripts" / "prepare_dispatch.py"
    checkpoint = skill_root / "scripts" / "branchos_checkpoint.py"
    return "\n".join(
        [
            RULE_START,
            "",
            "MANDATORY: BranchOS 共享规划层（Shared Planning Layer）—— 对 medium / complex 任务，在 canonical boot 与上下文加载之后、专门能力分发之前，必须评估是否启用 BranchOS。BranchOS 是虚拟任务分支系统，不是 Git 分支，也不替代 shared-fabric 的 preflight、六阶段 phase logging 或 postflight sync。",
            "",
            f"- Shared BranchOS skill source: `{skill_root}`",
            f"- Shared BranchOS init script: `{init}`",
            f"- Shared BranchOS prepare-dispatch script: `{prepare}`",
            f"- Shared BranchOS checkpoint script: `{checkpoint}`",
            "- Workspace-local state remains under `<workspace>/.agents/branchos/branch_state.yaml` and `<workspace>/.agents/branchos/branch_events.ndjson`.",
            "- Do not claim BranchOS is unavailable merely because the current workspace lacks `skills/branchos` or `.agents/branchos/branchos_checkpoint.py`; check the shared skill source first.",
            "- If the shared skill source exists, load BranchOS from Global Agent Fabric and create/load only the workspace-local branch state.",
            "- Never initialize BranchOS with `touch` or `echo '{}'`; missing, empty, or invalid state must be initialized or repaired with the shared init script.",
            "- Never repair a `pre_dispatch` failure with `init --force`. `pre_dispatch` needs a working branch packet; create or update it with the shared prepare-dispatch script.",
            "- Do not run `preflight_check.py` or `sync_all.py` per virtual branch.",
            "- Do not emit the full `route -> plan -> review -> dispatch -> execute -> report` lifecycle per virtual branch. The root task gets one canonical lifecycle; BranchOS maintains branch state inside it.",
            "",
            "When BranchOS is active:",
            "1. Load the BranchOS skill from the shared skill source.",
            f"2. Create or repair `<workspace>/.agents/branchos/branch_state.yaml`: `python3 {init} --workspace <workspace> --objective \"<current task objective>\" --complexity medium`.",
            f"3. Run task-start checkpoint: `python3 {checkpoint} --workspace <workspace> --checkpoint task_start --emit-summary`.",
            f"4. Before specialized skill/MCP/script/Maestro/subagent dispatch, create a working branch packet: `python3 {prepare} --workspace <workspace> --name \"<dispatch branch>\" --scope \"<bounded scope>\" --expected-output \"<expected result>\" --capability scripts:\"<tool or command>\"`, then run: `python3 {checkpoint} --workspace <workspace> --checkpoint pre_dispatch --emit-summary`.",
            f"5. Before merging branch outputs into root synthesis, run: `python3 {checkpoint} --workspace <workspace> --checkpoint pre_merge --emit-summary`.",
            f"6. Before final response and canonical postflight, run: `python3 {checkpoint} --workspace <workspace> --checkpoint final_response --emit-summary --emit-delta`.",
            "7. If neither shared nor local BranchOS exists, say so explicitly and fall back to the normal shared-fabric workflow.",
            "",
            RULE_END,
        ]
    )


def update_global_rule(rule_path: Path, global_root: Path) -> None:
    text = rule_path.read_text(encoding="utf-8") if rule_path.exists() else ""
    rule_path.write_text(replace_block(text, RULE_START, RULE_END, render_global_rule(global_root)), encoding="utf-8")


def run_export(global_root: Path, *, backup: bool) -> None:
    script = global_root / "scripts" / "sync" / "sync_antigravity_customizations.py"
    command = [sys.executable, str(script), "--global-root", str(global_root), "--export"]
    if backup:
        command.append("--backup")
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install BranchOS into Global Agent Fabric.")
    parser.add_argument("--global-root", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=repo_root())
    parser.add_argument("--update-global-rule", action="store_true")
    parser.add_argument("--export-antigravity", action="store_true")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()

    global_root = args.global_root.expanduser().resolve()
    project_root = args.project_root.expanduser().resolve()
    skill_source = project_root / "skills" / "branchos"
    skill_target = global_root / "skills" / "generated" / "branchos"

    copy_skill(skill_source, skill_target)
    update_registry(global_root / "skills" / "registry.yaml", global_root, project_root)
    update_generated_skill_count(global_root / "skills" / "sources.yaml", global_root)
    if args.update_global_rule:
        update_global_rule(global_root / "rules" / "global" / "gemini-global.md", global_root)
    if args.export_antigravity:
        run_export(global_root, backup=args.backup)

    summary = {
        "status": "ok",
        "global_root": str(global_root),
        "installed_skill": str(skill_target),
        "registry": str(global_root / "skills" / "registry.yaml"),
        "global_rule_updated": bool(args.update_global_rule),
        "antigravity_exported": bool(args.export_antigravity),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
