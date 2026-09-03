---
type: concept
tags: [a2a, protocol, agent-card, agent, json-rpc, grpc]
status: stable
summary: 让独立、可能不透明的 AI agent 作为对等方通信协作的开放协议——发现彼此、协商模态、管理共享任务；agent card 也是 AWS Agent Registry 的一种记录类型。
---
# Agent2Agent

一个开放标准（简称 A2A），用于让**独立、可能不透明的 AI agent 系统**作为对等方通信与协作。在 agent 由不同框架、语言、厂商构建的生态里，A2A 提供共同语言与交互模型，让 agent 发现彼此能力、协商交互模态、管理协作任务、**在无需访问彼此内部状态/记忆/工具的前提下**安全交换信息。权威依据是 [[A2A Specification]] 的 `a2a.proto`。

## 协议本体

- **三层结构**——[[A2A 三层规范结构]]：Canonical Data Model（proto）/ Abstract Operations / Protocol Bindings（JSON-RPC、gRPC、HTTP+JSON-REST）。
- **核心操作**——[[A2A 协议操作]]：Send Message、流式消息、Get/List/Cancel/Subscribe Task、Push Notification Config。
- **任务模型**——[[A2A Task]]：有状态的基本工作单元，终态为 COMPLETED/FAILED/CANCELED/REJECTED。
- **内容模型**——[[A2A 消息与内容模型]]：Message（带 role 的通信轮次）、Part（最小内容单元）、Artifact（任务产出）。
- **发现**——[[Agent Card]]：server 发布的 JSON 元数据，经 well-known URI 或目录发现，可用 JWS 签名。
- **异步**——[[Push Notifications]]：经 webhook 交付的异步任务更新，体现「Async First」。

**指导原则**：Simple（复用 HTTP/JSON-RPC/SSE）、Enterprise Ready、Async First、Modality Agnostic、[[Opaque Execution]]。

## 在企业治理场景里的角色

本 vault 也从 [[AWS Agent Registry (AWS Blog)]] 了解 A2A 在企业治理里的用法：

- **agent card 作为记录类型**——A2A 的 agent card 定义 agent 及其技能，是 [[AWS Agent Registry]] 支持编目的[[四种记录类型]]之一（记录类型名为「Agent」）。Agent Card 规范里的「Registries/Catalogs」发现机制正对应这个场景。
- **发布与同步**——publisher 可通过 Console/CLI/API 发布 A2A Agent；registry 也能从外部 A2A server 用 OAuth/IAM/无认证同步元数据。
- CI/CD 流水线可生成含 agent 元数据、能力、规格的 agent card。

## 与 MCP 的关系

A2A（agent↔agent 横向协作）与 [[Model Context Protocol]]（agent→工具纵向使用）是互补协议。详见 synthesis 页 [[A2A 与 MCP 的关系]]。

常见叫法：Agent2Agent、A2A、A2A 协议、agent card、agent 间协作协议、智能体互联协议、对等 agent 协议。

## 关联
- 原文规范: [[A2A Specification]]
- 三层结构: [[A2A 三层规范结构]]
- 协议操作: [[A2A 协议操作]]
- 任务模型: [[A2A Task]]
- 内容模型: [[A2A 消息与内容模型]]
- 发现: [[Agent Card]]
- 异步更新: [[Push Notifications]]
- 与 MCP 对比: [[A2A 与 MCP 的关系]]
- 指导原则: [[Opaque Execution]]
- 编目于: [[AWS Agent Registry]]
- 作为记录类型: [[四种记录类型]]
