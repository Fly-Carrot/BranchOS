# Routing Protocol

BranchOS routes capabilities through branch packets.

## Before Dispatch

Create a branch packet before calling a specialized skill, MCP tool, script, or subagent. The packet must include:

- branch id and name;
- purpose and scope;
- locked constraints relevant to the branch;
- inputs available to the branch;
- allowed capabilities;
- expected output;
- merge contract;
- explicit non-goals.

## Capability Rules

- Prefer the narrowest capability that can complete the branch deliverable.
- Do not let a dispatched capability expand the branch scope without creating a new branch or rebase note.
- If multiple capabilities are plausible, record the route rationale in the branch output.
- If subagents are not allowed by the current runtime or user instruction, produce the branch packet as a handoff instead of spawning.

## Dispatch Outcomes

After a capability returns:

- write the branch output;
- record artifacts or evidence;
- update conflicts and open questions;
- set status to `reviewing`, `ready_to_merge`, or `blocked`.
