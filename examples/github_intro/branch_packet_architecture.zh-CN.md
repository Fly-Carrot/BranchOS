# Branch Packet

[English](branch_packet_architecture.md) | [简体中文](branch_packet_architecture.zh-CN.md)

Branch ID: S002  
Branch Name: Architecture Boundary  
Parent: ROOT  
Status: active

## 目的

为研究级鸟类声学分析管线设计模块边界和数据流。

## 范围

定义数据接入、预处理、检测/分类、生态指标、验证和报告模块。

## 非目标

- 不选择具体 vendor cloud stack。
- 不实现代码。
- 不改变“原始野外录音必须保持 immutable”的锁定要求。

## 输入

- 根任务：设计鸟类声学分析管线。
- 锁定约束：raw audio 只读；输出必须可复现。
- 相关分支：B001 data ingestion、B002 model strategy、B003 ecological indicators、B004 reporting。

## 锁定约束

- 原始录音是 immutable source data。
- 中间输出必须可追溯到 audio file、timestamp、model version 和 configuration。
- 最终报告必须区分 measured outputs 与 ecological interpretation。

## 允许调用的能力

- 架构推理。
- 文档起草。
- 可选：咨询 domain 或 verification 分支。

## 预期输出

一份简洁的架构方案，包含模块边界、数据流、接口和未解决决策。

## 合并契约

只有当输出满足以下条件时才允许合并：

- 命名每个主要模块；
- 解释模块之间的数据流；
- 保留 raw-data immutability；
- 标明 validation hooks；
- 不覆盖锁定约束。

## 返回格式

Markdown sections：Modules、Data Flow、Interfaces、Validation Hooks、Open Decisions。
