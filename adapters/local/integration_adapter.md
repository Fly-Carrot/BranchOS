# Local BranchOS Adapter

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
python3 adapters/local/branchos_checkpoint.py --checkpoint task_start
python3 adapters/local/branchos_checkpoint.py --checkpoint pre_dispatch
python3 adapters/local/branchos_checkpoint.py --checkpoint pre_merge
python3 adapters/local/branchos_checkpoint.py --checkpoint final_response
```

By default, this adapter reads:

- `.agents/branchos/branch_state.yaml`
- `.agents/branchos/branch_events.ndjson`

Both paths are local project state, not global memory.
