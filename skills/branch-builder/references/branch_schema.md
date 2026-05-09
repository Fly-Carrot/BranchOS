# Branch Schema

Branch Builder stores branch state as YAML or JSON-compatible YAML. Use JSON-compatible YAML when no YAML parser is guaranteed.

## Root Fields

- `schema_version`: Branch Builder state schema version. Use `1`.
- `root_task`: root objective and locked constraints.
- `standing_branches`: persistent branches that represent durable concerns.
- `working_branches`: dynamic branches for the current task.
- `merge_queue`: branches ready for merge review.
- `pruned`: branches removed from active work.
- `branch_budget`: soft caps and current counts.

## Root Task

Required fields:

- `id`: stable task id.
- `objective`: concise task objective.
- `complexity`: `simple`, `medium`, or `complex`.
- `current_phase`: current root phase or runtime stage.
- `locked_constraints`: constraints that branch outputs may not override.
- `success_criteria`: conditions for task completion.

## Branch Object

Required fields:

- `id`: stable branch id, such as `B001`.
- `name`: human-readable branch name.
- `type`: one of the Branch Builder branch types.
- `status`: one of the Branch Builder branch states.
- `parent`: `ROOT` or another branch id.
- `depends_on`: branch ids that must be resolved first.
- `purpose`: why this branch exists.
- `inputs`: source material or upstream branches.
- `allowed_capabilities`: skills, MCP tools, subagents, scripts, or manual reasoning allowed in this branch.
- `deliverables`: concrete outputs expected from the branch.
- `merge_contract`: checks required before merging.
- `branch_packet`: dispatch packet used when specialized capabilities are called.
- `outputs`: committed branch findings or artifacts.
- `conflicts`: unresolved contradictions with other branches or locked constraints.
- `last_updated`: ISO timestamp or runtime-local timestamp.

## Merge Contract

Minimum fields:

- `merge_into`: target branch or `ROOT`.
- `must_satisfy`: conditions that prove the purpose is complete.
- `must_include`: fields or evidence required in the branch output.
- `conflict_check`: what must be checked before merge.
- `new_branch_triggers`: conditions that require creating a new branch instead of merging.

## Branch Packet

Required before specialized dispatch:

- `scope`: what the capability may do.
- `non_goals`: what the capability must not do.
- `expected_output`: exact return expectation.
- `return_format`: expected structure or prose format.

## Branch Budget

Recommended fields:

- `standing_count`: number of persistent standing branches.
- `active_working_count`: current active dynamic branches.
- `soft_cap`: recommended active dynamic cap.
- `over_budget_reason`: required when active dynamic branches exceed the soft cap.
