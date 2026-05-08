---
name: branchos
description: Use for medium-to-complex tasks that need architecture-first planning through a virtual branch graph. BranchOS creates and maintains task branches, branch packets, merge contracts, and branch-state checkpoints before routing skills, MCP tools, or subagents. It is not Git branching and does not replace runtime-specific boot, phase logging, or postflight synchronization.
metadata:
  short-description: Architecture-first virtual task branching
---

# BranchOS

BranchOS is a meta-planning skill. It turns a complex user objective into a virtual branch graph, then keeps that graph alive while the task proceeds.

A virtual branch is not a Git branch. It is a bounded task context with a purpose, inputs, allowed capabilities, deliverables, status, and merge contract.

## When To Use

Use BranchOS when the task:

- has medium or higher complexity;
- spans multiple domains, files, tools, skills, MCP servers, or agents;
- benefits from parallel exploration or staged validation;
- includes uncertainty, competing approaches, or meaningful failure modes;
- requires research, implementation, verification, and synthesis.

Do not use BranchOS for simple one-step answers, tiny edits, or tasks where a short checklist is enough.

## Core Workflow

1. Confirm the root objective and locked constraints.
2. Decide whether BranchOS is warranted; if yes, initialize or load a valid branch state.
3. Let the agent choose the branch structure from the task shape. Do not force a fixed template.
4. Separate standing branches from dynamic working branches.
5. Before routing a skill, MCP tool, script, or subagent, create a working branch packet. Use `scripts/prepare_dispatch.py` when available.
6. During work, update branch outputs, conflicts, and status.
7. Before merging, check the branch's merge contract.
8. Produce the final answer from merged branches and explicitly blocked branches only.

## Branch Types

- `standing`: persistent project-level concern such as constraints, architecture, verification, integration, or user intent.
- `working`: current-task branch created to solve a bounded part of the objective.
- `research`: evidence-gathering branch.
- `implementation`: build or edit branch.
- `verification`: test, critique, review, or validation branch.
- `synthesis`: integration branch that merges branch outputs.
- `hotfix`: correction branch for errors, regressions, or misread user intent.
- `rebase`: branch-state update triggered by new user constraints or changed assumptions.

## Branch States

- `proposed`
- `active`
- `blocked`
- `reviewing`
- `ready_to_merge`
- `merged`
- `pruned`

## Budget Rule

Branch count is decided by the agent from task complexity.

Standing branches do not count against the dynamic budget. Dynamic working branches have a soft cap:

- medium task: 4-8 active working branches;
- complex task: 8-14 active working branches;
- more than 14 active working branches requires a short reason and a prune/merge check first.

## Required Checkpoints

Use these checkpoints when the runtime or project provides a hook/adapter:

- `task_start`: load or initialize branch state.
- `pre_dispatch`: ensure each specialized capability call has a branch packet.
- `pre_merge`: validate the merge contract.
- `final_response`: ensure unresolved branches are merged, pruned, or reported as blocked/open loops.

Do not repair a `pre_dispatch` failure by rerunning `init_branch_state.py --force`; that resets the branch graph. Create or update the working branch packet instead:

```bash
python3 scripts/prepare_dispatch.py --workspace <workspace> --name "<dispatch branch>" --scope "<bounded scope>" --expected-output "<expected result>" --capability scripts:"<tool or command>"
```

## References

Read only what is needed:

- `references/branch_schema.md` for branch state fields.
- `references/branch_lifecycle.md` for branch operations and state changes.
- `references/routing_protocol.md` before dispatching skills, MCP tools, or subagents.
- `references/merge_protocol.md` before merging branch outputs.
- `references/anti_overplanning_rules.md` when branch count or ceremony feels too heavy.

## Local State

Preferred project-local paths:

- `.agents/branchos/branch_state.yaml`
- `.agents/branchos/branch_events.ndjson`

Never create the state file with `touch` or `echo '{}'`; an empty object is not a valid BranchOS branch graph. If state is missing, empty, or invalid, initialize or repair it with:

```bash
python3 scripts/init_branch_state.py --workspace <workspace> --objective "<current task objective>" --complexity medium
```

These are task/project state files, not global memory. Long-lived decisions should be summarized through the runtime's canonical postflight or memory mechanism.
