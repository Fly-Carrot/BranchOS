# GitHub Intro Test: BranchOS On A Research Pipeline Task

This document is a public-facing walkthrough of how BranchOS behaves on a medium-to-complex task.

## Test Task

Design a research-grade bird-acoustic analysis pipeline that ingests field recordings, detects bird vocalizations, computes ecological indicators, validates model quality, and produces a reproducible report.

## Operating Mode

BranchOS does not start by writing the answer. It first creates a virtual branch graph:

- `S001 Intent and Constraints`: keeps locked requirements visible.
- `S002 Architecture Boundary`: defines module boundaries and data flow.
- `S003 Verification`: owns quality checks and merge safety.
- `B001 Data Ingestion`: maps audio and metadata intake.
- `B002 Model Strategy`: decides detection and classification approach.
- `B003 Ecological Indicators`: defines ecological outputs and interpretation.
- `B004 Reporting`: produces the reproducible report surface.

The standing branches remain active as persistent lenses. The working branches move from `active` to `ready_to_merge` to `merged`.

## Dispatch Shape

Before calling a specialized capability, BranchOS creates a branch packet. The demo packet is:

`examples/github_intro/branch_packet_architecture.md`

That packet tells the capability what it may do, what it must not do, what it should return, and what merge contract it must satisfy.

## Checkpoints

The runnable test validates three checkpoints:

```bash
bash examples/github_intro/run_test.sh
```

Expected output:

```text
[1/5] task_start fixture: ok
[2/5] pre_dispatch fixture: ok
[3/5] pre_merge fixture: ok
[4/5] final_response fixture: ok
[5/5] unresolved final_response guard: ok
BranchOS GitHub intro test passed.
```

## Expected Final Synthesis

The final answer should not be a loose brainstorm. It should be a synthesis of merged branches:

- accepted architecture modules;
- accepted data and model assumptions;
- validation requirements;
- blocked or deferred decisions;
- next implementation step.

See:

`examples/github_intro/merge_report.md`

## What This Test Proves

- BranchOS can represent a complex task as standing and working branches.
- Specialized dispatch is scoped by a branch packet.
- Merge readiness is explicit.
- Final response validation fails if working branches remain unresolved.
- The validator uses only the Python standard library.
