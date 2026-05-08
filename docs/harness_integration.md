# Harness Integration

BranchOS is a planning layer, not a runtime. It should plug into whatever harness already owns boot, context loading, permissions, memory, logs, and final sync.

## Core Contract

For medium or complex tasks, activate BranchOS after the harness has loaded project context and before specialized dispatch.

BranchOS owns:

- virtual branch graph
- branch packets
- checkpoint validation
- branch event log
- merge contracts
- final branch delta

Your harness owns:

- runtime boot
- context and memory loading
- lifecycle phase logs
- tool permissions
- postflight sync
- durable memory write-back

Do not run runtime boot per virtual branch. Do not run your full task lifecycle per virtual branch. The root task gets one lifecycle; BranchOS maintains lightweight local branch state inside that lifecycle.

## Generic Snippet

Use this as the harness-agnostic pattern:

```text
BranchOS planning layer:
- For medium or complex tasks, after harness boot and context loading, evaluate whether BranchOS should be activated.
- BranchOS is a virtual task-branch planning system, not Git branching.
- Do not run runtime boot per virtual branch.
- Do not emit the full root lifecycle per virtual branch.
- The root task runs one lifecycle; BranchOS maintains lightweight local branch state and branch events.

When BranchOS is active:
1. Load the BranchOS skill.
2. Create or load the harness-local branch state, recommended at `.agents/branchos/branch_state.yaml`.
3. Run the local BranchOS checkpoint at task start:
   `python3 adapters/local/branchos_checkpoint.py --checkpoint task_start --emit-summary`
4. During planning, let the agent create standing branches and dynamic working branches according to task complexity.
5. Before calling a specialized skill, MCP tool, orchestration layer, script, or subagent, create a branch packet and run:
   `python3 adapters/local/branchos_checkpoint.py --checkpoint pre_dispatch --emit-summary`
6. Before merging branch outputs into the root synthesis, run:
   `python3 adapters/local/branchos_checkpoint.py --checkpoint pre_merge --emit-summary`
7. Before final response or harness postflight, run:
   `python3 adapters/local/branchos_checkpoint.py --checkpoint final_response --emit-summary --emit-delta`
8. Report the branch map at task start and the branch delta at task end through your harness's normal logging or sync path.

Routing relationship:
- BranchOS decides the task architecture and branch packets.
- Your orchestration layer may execute branch packets for medium or complex work when appropriate.
- MCP, skills, scripts, and subagents should be routed through the relevant BranchOS branch packet when BranchOS is active.
- If BranchOS is not installed in the current workspace, say so explicitly and fall back to the normal harness workflow.
```

## Shared-Fabric-Style Mapping

If your harness has a canonical boot plus a root lifecycle such as `route -> plan -> review -> dispatch -> execute -> report`, place BranchOS like this:

```text
canonical boot
  -> context load
  -> BranchOS activation check
  -> BranchOS task_start checkpoint
  -> route / plan / review
  -> pre_dispatch before each specialized capability
  -> execute branch packets
  -> pre_merge before root synthesis
  -> final_response checkpoint
  -> canonical postflight sync
```

The important boundary is that BranchOS does not replace boot or postflight. It enriches them with local branch state:

- Start output can include `[BRANCHOS_ACTIVE]`, root task, standing branches, working branches, and next checkpoint.
- End output can include `[BRANCHOS_REPORT]`, created branches, updated branches, merged branches, pruned branches, blocked branches, and artifacts.
- Postflight can attach BranchOS artifacts through the harness's supported sync mechanism.

## Output Contract

At task start, the harness can surface:

```text
[BRANCHOS_ACTIVE]
Root task: Design a research-grade bird-acoustic analysis pipeline.
Standing branches: S001 Intent, S002 Architecture, S003 Verification
Working branches: B001 Data Ingestion, B002 Model Strategy, B003 Ecological Indicators, B004 Reporting
Next checkpoint: pre_dispatch
```

At task end, the harness can surface:

```text
[BRANCHOS_REPORT]
Merged: B001 Data Ingestion, B002 Model Strategy, B003 Ecological Indicators, B004 Reporting
Open: S001 Intent, S002 Architecture, S003 Verification
Blocked: none
Pruned: none
Artifacts: .agents/branchos/branch_state.yaml, .agents/branchos/branch_events.ndjson, merge_report.md
```

Standing branches may remain active if they represent durable lenses rather than one-off work products. Working branches should be merged, blocked, or pruned before the final answer.

## Portability Rule

Keep shared-fabric, Maestro, CI, dashboard, or memory-specific behavior in a local adapter or harness snippet. Keep BranchOS core portable: skill instructions, branch schema, checkpoint script, templates, and examples.
