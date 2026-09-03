---
type: concept
tags: [a2a, opaque-execution, principle, privacy]
status: developing
summary: A2A 五大指导原则之一——agent 作为对等方协作时只基于声明的能力和交换的信息，无需共享内部想法、计划或工具实现。
---
# Opaque Execution

Opaque Execution（不透明执行）是 [[Agent2Agent]] 的五大**指导原则**之一（与 Simple、Enterprise Ready、Async First、Modality Agnostic 并列）。它规定：agent 之间作为对等方协作时，**只基于声明的能力和交换的信息**，无需共享各自的内部想法、计划或工具实现。

## 它约束什么

A2A 面向的是「独立、往往不透明的 AI agent 系统」——它们由不同框架、语言、厂商构建。Opaque Execution 是这种异构生态能协作的前提：一个 agent 请另一个干活时，双方不暴露内部状态/记忆/工具实现，只通过 [[Agent Card]] 声明的能力和 [[A2A 消息与内容模型|Message/Artifact]] 交换的信息协作。

这体现在端到端流程里（见 [[A2A 委派端到端流程]]）：派活方经 [[A2A 协议操作|Send Message]] 建 [[A2A Task]] 时，不需要、也拿不到对方的内部实现——只按声明能力交互、按交换信息推进。

## 与 MCP 的呼应

MCP 侧有一个结构相近但作用域不同的隔离设计：[[客户端-主机-服务器架构|MCP server]] 不能读取整个对话、也不能「看进」其他 server。二者都强调「协作方之间的不透明边界」，但 A2A 的 Opaque Execution 是 agent↔agent 对等层面的原则，MCP 的隔离是 host 对 server 强制的边界（对照见 [[A2A 与 MCP 的关系]]）。

常见叫法：Opaque Execution、不透明执行、不透明协作、opaque agent、不共享内部状态、按声明能力协作、A2A 指导原则之一。

## 关联
- 所属协议: [[Agent2Agent]]
- 发现文档: [[Agent Card]]
- 体现于: [[A2A 委派端到端流程]]
- 与 MCP 对照: [[A2A 与 MCP 的关系]]
- 原文: [[A2A Specification]]
