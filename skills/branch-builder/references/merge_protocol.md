# Merge Protocol

Merging is the control point that prevents branch outputs from polluting the root task.

## Pre-Merge Checks

Before merging a branch, verify:

- the branch purpose is satisfied;
- required deliverables are present;
- `merge_contract.must_satisfy` is met;
- locked constraints are not overridden;
- conflicts are empty or explicitly accepted;
- no new branch trigger is active.

## Merge Result

A merge should produce:

- accepted findings or artifacts;
- rejected or deferred claims;
- conflicts resolved or carried as open loops;
- downstream branches affected by the merge;
- a short merge note.

## Blocked Branches

Blocked branches may be reported in the final answer if:

- the blocker is real and cannot be resolved in the current runtime;
- the missing evidence, permission, or tool access is named;
- the root task can still produce a partial answer without pretending the branch merged.

## Rebase and Hotfix

Use `rebase` when user instructions or source facts change the assumptions of multiple branches.

Use `hotfix` when a specific branch output is wrong, incomplete, or contradictory.
