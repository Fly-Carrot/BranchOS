# Harness 集成

[English](harness_integration.md) | [简体中文](harness_integration.zh-CN.md)

Branch Builder 是规划层，不是 runtime。它应该接入已经负责 boot、上下文加载、权限、memory、日志和最终同步的 harness。

## 核心契约

对于 medium 或 complex 任务，在 harness 已经加载项目上下文之后、专门能力分发之前启用 Branch Builder。

Branch Builder 负责：

- 虚拟分支图
- branch packet
- checkpoint validation
- branch event log
- merge contract
- final branch delta

harness 负责：

- runtime boot
- context 与 memory 加载
- 生命周期 phase log
- 工具权限
- postflight sync
- durable memory write-back

不要为每个虚拟分支运行 runtime boot。不要为每个虚拟分支运行完整任务生命周期。根任务只有一个生命周期；Branch Builder 在这个生命周期内部维护轻量的本地分支状态。

## 通用 Snippet

这是 harness-agnostic 模式：

```text
Branch Builder planning layer:
- For medium or complex tasks, after harness boot and context loading, evaluate whether Branch Builder should be activated.
- Branch Builder is a virtual task-branch planning system, not Git branching.
- Do not run runtime boot per virtual branch.
- Do not emit the full root lifecycle per virtual branch.
- The root task runs one lifecycle; Branch Builder maintains lightweight local branch state and branch events.

When Branch Builder is active:
1. Activate the Branch Builder protocol package.
2. 初始化或加载 harness 本地 branch state，推荐路径为 `.agents/branch-builder/branch_state.yaml`。不要使用 `touch` 或 `echo '{}'`。
3. Run the local Branch Builder checkpoint at task start:
   `python3 skills/branch-builder/scripts/init_branch_state.py --objective "<current task objective>" --complexity medium`
   `python3 adapters/local/branch_builder_checkpoint.py --checkpoint task_start --emit-summary`
4. During planning, let the agent create standing branches and dynamic working branches according to task complexity.
5. Before calling a specialized skill, MCP tool, orchestration layer, script, or subagent, create a branch packet and run:
   `python3 skills/branch-builder/scripts/prepare_dispatch.py --name "<dispatch branch>" --scope "<bounded scope>" --expected-output "<expected result>" --capability scripts:"<tool>"`
   `python3 adapters/local/branch_builder_checkpoint.py --checkpoint pre_dispatch --emit-summary`
6. Before merging branch outputs into the root synthesis, run:
   `python3 skills/branch-builder/scripts/resolve_branch.py --branch-id B001 --status ready_to_merge --output "<branch result summary>"`
   `python3 adapters/local/branch_builder_checkpoint.py --checkpoint pre_merge --emit-summary`
7. Before final response or harness postflight, run:
   `python3 skills/branch-builder/scripts/resolve_branch.py --branch-id B001 --status merged --output "<merged branch result>"`
   `python3 adapters/local/branch_builder_checkpoint.py --checkpoint final_response --emit-summary --emit-delta`
8. 把 Branch Builder checkpoint error 作为 branch-layer open loop 报告；不要让它阻塞 harness 的 canonical postflight。
9. Report the branch map at task start and the branch delta at task end through your harness's normal logging or sync path.

Routing relationship:
- Branch Builder decides the task architecture and branch packets.
- Your orchestration layer may execute branch packets for medium or complex work when appropriate.
- MCP, skills, scripts, and subagents should be routed through the relevant Branch Builder branch packet when Branch Builder is active.
- If Branch Builder is not installed in the current workspace, say so explicitly and fall back to the normal harness workflow.
```

## Shared-Fabric 风格映射

如果你的 harness 有 canonical boot 和 `route -> plan -> review -> dispatch -> execute -> report` 这样的根生命周期，可以这样放置 Branch Builder：

```text
canonical boot
  -> context load
  -> Branch Builder activation check
  -> Branch Builder task_start checkpoint
  -> route / plan / review
  -> pre_dispatch before each specialized capability
  -> execute branch packets
  -> pre_merge before root synthesis
  -> final_response checkpoint
  -> canonical postflight sync
```

关键边界是：Branch Builder 不替代 boot 或 postflight。它只用本地分支状态增强它们。

- 开始输出可以包含 `[BRANCH_BUILDER_ACTIVE]`、root task、standing branches、working branches 和 next checkpoint。
- 结束输出可以包含 `[BRANCH_BUILDER_REPORT]`、created branches、updated branches、merged branches、pruned branches、blocked branches 和 artifacts。
- postflight 可以通过 harness 支持的 sync 机制附加 Branch Builder artifacts。

## Global Agent Fabric 模式

在 shared-fabric 架构中，推荐把 Branch Builder 一次性安装到 shared planning-layer root，而不是复制到每个项目：

```bash
python3 adapters/shared_fabric/install_branch_builder_shared_fabric.py \
  --global-root /path/to/global-agent-fabric \
  --update-global-rule \
  --export-antigravity
```

安装后的 protocol package 位于：

```text
<global-agent-fabric>/skills/generated/branch-builder
```

workspace 只保留任务本地状态：

```text
<workspace>/.agents/branch-builder/branch_state.yaml
<workspace>/.agents/branch-builder/branch_events.ndjson
```

任意 workspace 都可以使用共享 checkpoint 脚本：

```bash
python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/init_branch_state.py \
  --workspace /path/to/workspace \
  --objective "<current task objective>" \
  --complexity medium

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/branch_builder_checkpoint.py \
  --workspace /path/to/workspace \
  --checkpoint task_start \
  --emit-summary

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/prepare_dispatch.py \
  --workspace /path/to/workspace \
  --name "<dispatch branch>" \
  --scope "<bounded scope>" \
  --expected-output "<expected result>" \
  --capability scripts:"<tool>"

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/branch_builder_checkpoint.py \
  --workspace /path/to/workspace \
  --checkpoint pre_dispatch \
  --emit-summary

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/resolve_branch.py \
  --workspace /path/to/workspace \
  --branch-id B001 \
  --status ready_to_merge \
  --output "<branch result summary>"

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/branch_builder_checkpoint.py \
  --workspace /path/to/workspace \
  --checkpoint pre_merge \
  --emit-summary

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/resolve_branch.py \
  --workspace /path/to/workspace \
  --branch-id B001 \
  --status merged \
  --output "<merged branch result>"

python3 /path/to/global-agent-fabric/skills/generated/branch-builder/scripts/branch_builder_checkpoint.py \
  --workspace /path/to/workspace \
  --checkpoint final_response \
  --emit-summary \
  --emit-delta
```

重要 runtime 规则：

```text
不要仅仅因为当前 workspace 缺少 `skills/branch-builder` 就声明 Branch Builder 不可用。
必须先检查 harness 是否有共享 Branch Builder planning-layer package，例如：
`<global-agent-fabric>/skills/generated/branch-builder`。
```

这是 multi-workspace 系统的推荐模式：Branch Builder 全局安装，branch state 项目本地保存。

## 输出契约

任务开始时，harness 可以展示：

```text
[BRANCH_BUILDER_ACTIVE]
Root task: Design a research-grade bird-acoustic analysis pipeline.
Standing branches: S001 Intent, S002 Architecture, S003 Verification
Working branches: B001 Data Ingestion, B002 Model Strategy, B003 Ecological Indicators, B004 Reporting
Next checkpoint: pre_dispatch
```

任务结束时，harness 可以展示：

```text
[BRANCH_BUILDER_REPORT]
Merged: B001 Data Ingestion, B002 Model Strategy, B003 Ecological Indicators, B004 Reporting
Open: S001 Intent, S002 Architecture, S003 Verification
Blocked: none
Pruned: none
Artifacts: .agents/branch-builder/branch_state.yaml, .agents/branch-builder/branch_events.ndjson, merge_report.md
```

如果 standing branches 代表长期视角，它们可以保持 active。working branches 在最终答案前应该被 merged、blocked 或 pruned。

## 可移植性规则

把 shared-fabric、Maestro、CI、dashboard 或 memory 相关行为放在 local adapter 或 harness snippet 中。Branch Builder core 保持可移植：skill instructions、branch schema、checkpoint script、templates 和 examples。
