# Local BranchOS Adapter

[English](integration_adapter.md) | [Simplified Chinese](integration_adapter.zh-CN.md)

BranchOS is portable at the skill layer. Runtime-specific boot, memory, and sync systems should integrate through a local adapter like this one.

## Placement

Run BranchOS after your runtime has loaded the project context and before specialized dispatch:

```text
runtime boot
  -> BranchOS task_start
  -> root planning cycle
  -> pre_dispatch before skill/tool/agent calls
  -> pre_merge before synthesis
  -> final_response before final answer
  -> runtime postflight or memory sync
```

Do not run runtime boot once per virtual branch. A virtual branch is not a runtime session.

## Checkpoints

```bash
python3 skills/branchos/scripts/init_branch_state.py --objective "<current task objective>" --complexity medium
python3 adapters/local/branchos_checkpoint.py --checkpoint task_start --emit-summary
python3 adapters/local/branchos_checkpoint.py --checkpoint pre_dispatch --emit-summary
python3 adapters/local/branchos_checkpoint.py --checkpoint pre_merge --emit-summary
python3 adapters/local/branchos_checkpoint.py --checkpoint final_response --emit-summary --emit-delta
```

By default, this adapter reads:

- `.agents/branchos/branch_state.yaml`
- `.agents/branchos/branch_events.ndjson`

Both paths are local project state, not global memory.
Do not create `branch_state.yaml` with `touch` or `echo '{}'`; use the init script above.

Use the JSON `branchos_summary` field for task-start branch visibility and
`branchos_delta` for final branch-report visibility.

Detailed harness placement: [`../../docs/harness_integration.md`](../../docs/harness_integration.md)
