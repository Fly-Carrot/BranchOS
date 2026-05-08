# Branch Lifecycle

BranchOS uses Git-like words as task-state operations only. These operations never create real Git branches.

## Operations

- `branch`: create a new virtual task branch when a goal, risk, dependency, or capability route needs its own boundary.
- `checkout`: enter a branch context before doing work for that branch.
- `commit`: record a branch output, finding, artifact, or blocked state.
- `merge`: bring branch output into the target branch after checking the merge contract.
- `rebase`: update branch assumptions after user constraints or source facts change.
- `prune`: remove branches that are redundant, speculative, stale, or superseded.
- `hotfix`: create a correction branch for a bug, contradiction, or misunderstood intent.

## Lifecycle Defaults

1. New branches start as `proposed`.
2. A branch becomes `active` when the agent starts working in that context.
3. A branch becomes `reviewing` when deliverables exist but merge checks are incomplete.
4. A branch becomes `ready_to_merge` only when the merge contract appears satisfied.
5. A branch becomes `merged` after the parent accepts its output.
6. A branch becomes `blocked` when required input, permission, tool access, or evidence is missing.
7. A branch becomes `pruned` when it no longer improves the root task.

## Standing Branches

Standing branches are durable lenses, not tasks that must be closed every turn. Typical standing branches:

- user intent and locked constraints;
- architecture and module boundaries;
- routing and capability selection;
- verification and risk;
- synthesis and handoff.

Keep standing branches stable across a project, but update their outputs when the project evolves.

## Working Branches

Working branches should be bounded, deliverable-driven, and mergeable. If a working branch grows into multiple unrelated concerns, split it. If two working branches always move together, merge them.
