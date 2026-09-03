---
type: concept
tags: [a2a, architecture, protobuf, bindings]
status: developing
summary: A2A 规范的三层组织——Canonical Data Model（proto 数据模型）、Abstract Operations（绑定无关操作）、Protocol Bindings（JSON-RPC/gRPC/HTTP-REST 映射）。
---
# A2A 三层规范结构

[[Agent2Agent]] 规范分三层，协同给出完整协议定义：

- **Layer 1 — Canonical Data Model（规范数据模型）**：所有实现都必须理解的核心数据结构与消息格式，以 Protocol Buffer 消息表达、**协议无关**。见 [[A2A Task]]、[[A2A 消息与内容模型]]、[[Agent Card]]。
- **Layer 2 — Abstract Operations（抽象操作）**：A2A agent 必须支持的基本能力与行为，独立于具体协议暴露方式。见 [[A2A 协议操作]]。
- **Layer 3 — Protocol Bindings（协议绑定）**：把抽象操作和数据结构映射到具体绑定——JSON-RPC、gRPC、HTTP+JSON/REST、自定义绑定，含方法名、端点模式、协议特定行为。

## 为什么分层

核心语义跨所有绑定保持一致；新绑定无需改动数据模型即可加入；开发者可独立于绑定关切推理 A2A 操作；靠共享的规范数据模型维持互操作性。

**权威源**：`spec/a2a.proto` 是所有数据对象与请求/响应消息的唯一规范定义；SDK 绑定、JSON schema 等派生形式 MUST 从 proto 重新生成而非手改。这一点与 [[Model Context Protocol|MCP]] 以 TypeScript schema 为权威源类似。

常见叫法：A2A 三层结构、三层规范、Data Model/Operations/Bindings、canonical data model、protocol bindings、proto 权威源、分层协议定义。

## 关联
- 所属协议: [[Agent2Agent]]
- 数据模型层: [[A2A Task]]、[[A2A 消息与内容模型]]、[[Agent Card]]
- 操作层: [[A2A 协议操作]]
- 原文: [[A2A Specification]]
