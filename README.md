# BranchOS

BranchOS is an architecture-first planning skill for agentic work.

It does not create Git branches. It creates a virtual branch graph: bounded task contexts with explicit purposes, inputs, allowed capabilities, deliverables, status, and merge contracts. The goal is to stop agents from rushing linearly into complex work and give skills, MCP tools, scripts, and subagents a clean structure to operate inside.

## What It Does

For a medium or complex task, BranchOS adds an inner operating layer:

```text
Root task
  standing branches: persistent concerns such as intent, architecture, verification
  working branches: dynamic task branches created from the actual objective
  branch packets: scoped handoffs before dispatching tools, skills, or agents
  merge contracts: checks before branch outputs enter the final synthesis
  checkpoints: task_start, pre_dispatch, pre_merge, final_response
```

BranchOS is designed to sit after your runtime bootstraps its context and before it dispatches specialized capabilities.

```text
runtime boot
  -> BranchOS task_start
  -> root planning cycle
  -> branch packets before dispatch
  -> merge contracts before synthesis
  -> final_response checkpoint
  -> runtime postflight or memory sync
```

## Repository Structure

```text
skills/branchos/
  SKILL.md                         # portable skill instructions
  references/                      # progressive-disclosure protocols
  templates/                       # branch map, branch packet, merge report
  scripts/validate_branch_state.py # stdlib validator

adapters/local/
  branchos_checkpoint.py           # local checkpoint adapter
  integration_adapter.md           # runtime placement notes

.agents/branchos/                  # local runtime state, usually gitignored
  branch_state.yaml                # project-local state, JSON-compatible YAML
  branch_events.ndjson             # compact project-local branch events

examples/github_intro/
  branch_state_start.yaml
  branch_state_pre_merge.yaml
  branch_state_final.yaml
  branch_packet_architecture.md
  merge_report.md
  run_test.sh
```

The skill layer is portable. Runtime-specific hooks and local paths belong in an adapter layer.

## Example Task

The GitHub intro test uses this task:

> Design a research-grade bird-acoustic analysis pipeline that ingests field recordings, detects bird vocalizations, computes ecological indicators, validates model quality, and produces a reproducible report.

BranchOS turns that into:

- standing branches for user intent, architecture, and verification;
- working branches for data ingestion, model strategy, ecological indicators, and reporting;
- branch packets before dispatching specialist work;
- merge contracts before synthesizing the final system architecture.

## Run The Demo

```bash
bash examples/github_intro/run_test.sh
```

For a complete visual walkthrough, see `docs/branchos_visual_report.md`.

Expected result:

```text
[1/5] task_start fixture: ok
[2/5] pre_dispatch fixture: ok
[3/5] pre_merge fixture: ok
[4/5] final_response fixture: ok
[5/5] unresolved final_response guard: ok
BranchOS GitHub intro test passed.
```

You can also run checkpoints manually:

```bash
python3 skills/branchos/scripts/validate_branch_state.py examples/github_intro/branch_state_start.yaml --checkpoint task_start
python3 skills/branchos/scripts/validate_branch_state.py examples/github_intro/branch_state_start.yaml --checkpoint pre_dispatch
python3 skills/branchos/scripts/validate_branch_state.py examples/github_intro/branch_state_pre_merge.yaml --checkpoint pre_merge
python3 skills/branchos/scripts/validate_branch_state.py examples/github_intro/branch_state_final.yaml --checkpoint final_response
```

The demo also checks that `final_response` fails when working branches remain unresolved.

## Expected Output

BranchOS should produce three main artifacts during real use:

1. `branch_state.yaml`: the current virtual branch graph and branch statuses.
2. `branch packet`: a scoped dispatch packet for a skill, MCP tool, script, or subagent.
3. `merge report`: a compact synthesis of merged, blocked, and pruned branches.

The final response should be based only on merged branches and explicitly reported blocked branches. Branch outputs should not silently override locked constraints.

## Design Boundaries

- BranchOS is not Git branching.
- BranchOS is not a workflow runtime.
- BranchOS does not replace runtime boot, phase logging, postflight sync, or memory systems.
- BranchOS should not write global memory files directly.
- Branch count is chosen by the agent from task complexity, with standing branches separated from dynamic working branches.
