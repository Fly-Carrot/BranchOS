---
name: branch-builder
description: 用于需要架构优先规划的 medium-to-complex 根任务。Branch Builder 每个 root task 最多激活一次，用来创建并维护虚拟任务分支、branch packets、merge contracts 和 branch-state checkpoints，再路由 skills、MCP tools 或 subagents。它不是 Git branching，不是可反复调用的普通 tool skill，也不替代 runtime-specific boot、phase logging 或 postflight synchronization。
metadata:
  short-description: 架构优先的虚拟任务分支系统
---

# Branch Builder

Branch Builder 是一个用 skill format 打包的 root-task planning layer。它把复杂用户目标转化为虚拟分支图，并在任务推进过程中持续维护这个图。

把它当成 activation protocol：对一个 root task 初始化一次，然后通过 checkpoints 更新分支状态。不要像普通 specialist skill 那样反复调用它。

虚拟分支不是 Git 分支。它是一个有边界的任务上下文，包含目的、输入、允许调用的能力、交付物、状态和合并契约。

## 何时使用

当任务满足以下条件时使用 Branch Builder：

- 复杂度为 medium 或更高；
- 跨越多个领域、文件、工具、skills、MCP servers 或 agents；
- 适合并行探索或阶段性验证；
- 包含不确定性、竞争方案或有意义的 failure modes；
- 需要 research、implementation、verification 和 synthesis。

不要为简单一步回答、小修改或短 checklist 足够处理的任务启用 Branch Builder。

## 核心流程

1. 确认 root objective 和 locked constraints。
2. 判断是否需要 Branch Builder；如果需要，初始化或加载合法的 branch state。
3. 让 agent 根据任务形状自行决定分支结构，不强制固定模板。
4. 区分 standing branches 和 dynamic working branches。
5. 在路由 skill、MCP tool、script 或 subagent 之前创建 working branch packet。可用时使用 `scripts/prepare_dispatch.py`。
6. 工作过程中持续更新 branch outputs、conflicts 和 status。使用 `scripts/resolve_branch.py` 在 `pre_merge` 前标记为 `ready_to_merge`，最终回复前标记为 `merged`、`blocked` 或 `pruned`。
7. 合并前检查对应分支的 merge contract。
8. 最终答案只能来自 merged branches 和明确 blocked branches。

## 分支类型

- `standing`：持久项目视角，例如 constraints、architecture、verification、integration 或 user intent。
- `working`：为当前任务创建的 bounded branch。
- `research`：证据收集分支。
- `implementation`：构建或编辑分支。
- `verification`：测试、批判、review 或验证分支。
- `synthesis`：整合分支输出的合成分支。
- `hotfix`：修正错误、回归或误读用户意图。
- `rebase`：由新用户约束或假设变化触发的 branch-state update。

## 分支状态

- `proposed`
- `active`
- `blocked`
- `reviewing`
- `ready_to_merge`
- `merged`
- `pruned`

## 分支预算

分支数量由 agent 根据任务复杂度决定。

standing branches 不计入动态预算。dynamic working branches 的软上限为：

- medium task：4-8 个 active working branches；
- complex task：8-14 个 active working branches；
- 超过 14 个 active working branches 时，必须先给出原因并触发 prune/merge check。

## 必要 Checkpoints

当 runtime 或项目提供 hook/adapter 时使用这些 checkpoints：

- `task_start`：加载或初始化 branch state。
- `pre_dispatch`：确保每次 specialized capability call 都有 branch packet。
- `pre_merge`：验证 merge contract。
- `final_response`：确保 unresolved branches 已被 merged、pruned，或报告为 blocked/open loops。

checkpoint 脚本会输出稳定的 `status_marker`。把这些 marker 当成 boot/sync receipt 使用：

- `[BRANCH_BUILDER_READY]`：state 已成功初始化或修复。
- `[BRANCH_BUILDER_ACTIVE]`：`task_start` 通过，规划层已激活。
- `[BRANCH_BUILDER_CHECKPOINT_OK]`：`pre_dispatch` 或 `pre_merge` 通过。
- `[BRANCH_BUILDER_REPORT]`：`final_response` 通过，可以安全报告 branch delta。
- `[BRANCH_BUILDER_OPEN]`：`final_response` 发现 unresolved working branches。
- `[BRANCH_BUILDER_ERROR]`：checkpoint 因其他原因失败。

只有当脚本输出对应 marker 后，才报告 Branch Builder 已激活或最终分支闭环成功。

不要用 `init_branch_state.py --force` 修复 `pre_dispatch` failure；那会重置分支图。应该创建或更新 working branch packet：

```bash
python3 scripts/prepare_dispatch.py --workspace <workspace> --name "<dispatch branch>" --scope "<bounded scope>" --expected-output "<expected result>" --capability scripts:"<tool or command>"
```

如果 `final_response` 报告 unresolved working branches，不要用 `init --force` 抹掉错误。应该收束每个 working branch：

```bash
python3 scripts/resolve_branch.py --workspace <workspace> --branch-id B001 --status merged --output "<branch result summary>"
```

Branch Builder checkpoint error 是规划层信号，应该报告出来，但不应该阻止宿主 harness 继续运行自己的 postflight 或 memory sync。

## References

按需读取：

- `references/branch_schema.md`：branch state fields。
- `references/branch_lifecycle.md`：branch operations 和 state changes。
- `references/routing_protocol.md`：dispatch skills、MCP tools 或 subagents 之前阅读。
- `references/merge_protocol.md`：合并 branch outputs 之前阅读。
- `references/anti_overplanning_rules.md`：当分支数量或流程显得过重时阅读。

## 本地状态

推荐项目本地路径：

- `.agents/branch-builder/branch_state.yaml`
- `.agents/branch-builder/branch_events.ndjson`

不要用 `touch` 或 `echo '{}'` 创建 state file；空对象不是合法的 Branch Builder 分支图。如果 state 缺失、为空或格式无效，用下面命令初始化或修复：

```bash
python3 scripts/init_branch_state.py --workspace <workspace> --objective "<current task objective>" --complexity medium
```

这些是 task/project state files，不是 global memory。长期决策应该通过 runtime 自己的 postflight 或 memory mechanism 总结写回。
