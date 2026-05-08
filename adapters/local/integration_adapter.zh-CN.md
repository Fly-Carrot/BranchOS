# 本地 BranchOS Adapter

[English](integration_adapter.md) | [简体中文](integration_adapter.zh-CN.md)

BranchOS 在 skill 层是可移植的。runtime-specific boot、memory 和 sync system 应该通过这样的本地 adapter 接入。

## 放置位置

在 runtime 已经加载项目上下文之后、专门能力分发之前运行 BranchOS：

```text
runtime boot
  -> BranchOS task_start
  -> root planning cycle
  -> pre_dispatch before skill/tool/agent calls
  -> pre_merge before synthesis
  -> final_response before final answer
  -> runtime postflight or memory sync
```

不要为每个虚拟分支运行一次 runtime boot。虚拟分支不是 runtime session。

## Checkpoints

```bash
python3 skills/branchos/scripts/init_branch_state.py --objective "<current task objective>" --complexity medium
python3 adapters/local/branchos_checkpoint.py --checkpoint task_start --emit-summary
python3 skills/branchos/scripts/prepare_dispatch.py --name "<dispatch branch>" --scope "<bounded scope>" --expected-output "<expected result>" --capability scripts:"<tool>"
python3 adapters/local/branchos_checkpoint.py --checkpoint pre_dispatch --emit-summary
python3 skills/branchos/scripts/resolve_branch.py --branch-id B001 --status ready_to_merge --output "<branch result summary>"
python3 adapters/local/branchos_checkpoint.py --checkpoint pre_merge --emit-summary
python3 skills/branchos/scripts/resolve_branch.py --branch-id B001 --status merged --output "<merged branch result>"
python3 adapters/local/branchos_checkpoint.py --checkpoint final_response --emit-summary --emit-delta
```

默认情况下，这个 adapter 读取：

- `.agents/branchos/branch_state.yaml`
- `.agents/branchos/branch_events.ndjson`

这两个路径都是项目本地状态，不是 global memory。
不要用 `touch` 或 `echo '{}'` 创建 `branch_state.yaml`；请使用上面的 init script。

使用 JSON 中的 `branchos_summary` 查看任务开始时的分支地图；使用 `branchos_delta` 查看最终分支报告。

更完整的 harness 放置方式见：[`../../docs/harness_integration.zh-CN.md`](../../docs/harness_integration.zh-CN.md)
