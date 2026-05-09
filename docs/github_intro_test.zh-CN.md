# GitHub Intro Test：Branch Builder 处理研究管线任务

[English](github_intro_test.md) | [简体中文](github_intro_test.zh-CN.md)

本文面向公开展示，说明 Branch Builder 在一个 medium-to-complex 任务上如何运行。

## 测试任务

设计一个研究级鸟类声学分析管线：输入野外录音，检测鸟类鸣声，计算生态指标，验证模型质量，并生成可复现报告。

## 运行模式

Branch Builder 不会一开始就直接写答案。它会先创建虚拟分支图：

- `S001 Intent and Constraints`：保持锁定需求可见。
- `S002 Architecture Boundary`：定义模块边界和数据流。
- `S003 Verification`：负责质量检查和合并安全。
- `B001 Data Ingestion`：映射音频和元数据接入。
- `B002 Model Strategy`：决定检测和分类策略。
- `B003 Ecological Indicators`：定义生态输出和解释边界。
- `B004 Reporting`：生成可复现报告界面。

standing branches 会作为长期视角保持 active。working branches 会从 `active` 进入 `ready_to_merge`，最后变成 `merged`。

## 分发形态

在调用专门能力之前，Branch Builder 会创建 branch packet。示例 packet 是：

`examples/github_intro/branch_packet_architecture.md`

这个 packet 会告诉被调用能力：可以做什么、不能做什么、应该返回什么，以及必须满足什么 merge contract。

## Checkpoints

可运行测试命令：

```bash
bash examples/github_intro/run_test.sh
```

预期输出：

```text
[1/5] task_start fixture: ok
[2/5] pre_dispatch fixture: ok
[3/5] pre_merge fixture: ok
[4/5] final_response fixture: ok
[5/5] unresolved final_response guard: ok
Branch Builder GitHub intro test passed.
```

## 预期最终合成

最终答案不应该是松散 brainstorm，而应该是 merged branches 的合成：

- 已接受的架构模块；
- 已接受的数据和模型假设；
- 验证要求；
- blocked 或 deferred decisions；
- 下一步实现切片。

参见：

`examples/github_intro/merge_report.md`

## 这个测试证明了什么

- Branch Builder 可以把复杂任务表示为 standing branches 和 working branches。
- 专门能力分发由 branch packet 限定边界。
- merge readiness 是显式状态。
- 如果 working branches 仍未解决，final response validation 会失败。
- validator 只使用 Python standard library。
