---
type: synthesis
tags: [a2a, mcp, comparison, agent, protocol]
status: developing
summary: A2A 与 MCP 是互补协议——MCP 管 agent 如何「使用」工具/资源，A2A 管 agent 之间如何「结伴/委派」；二者在 AWS Agent Registry 里并列为记录类型。
---
# A2A 与 MCP 的关系

一处跨页综合，基于 [[A2A Specification]] 的 Appendix B、[[MCP Specification (2026-07-28)]] 以及 [[AWS Agent Registry (AWS Blog)]]。两个协议本 vault 都有完整页——[[Agent2Agent]] 与 [[Model Context Protocol]]——本页把它们放在一起看。

## 一句话区分

- **[[Model Context Protocol|MCP]]**：管一个 agent 如何**连接并使用**工具、API、数据源等外部资源。是 agent *使用*某能力的「how-to」（纵向：agent ↓ 工具）。
- **[[Agent2Agent|A2A]]**：管独立、往往不透明的 agent 之间如何作为**对等方通信协作**——发现彼此、协商模态、管理共享任务。是 agent 之间*结伴/委派*工作（横向：agent ↔ agent）。

A2A 规范 Appendix B 原文明确二者「互补」，并给出协同图景：一个 A2A Client agent 请求 A2A Server agent 执行复杂任务，Server agent 反过来可能用 MCP 与若干底层工具/API/数据源交互来完成该 A2A 任务。

## 对照表

| 维度 | MCP | A2A |
|---|---|---|
| 解决的关系 | agent → 工具/资源（纵向） | agent ↔ agent（横向对等） |
| 核心比喻 | 使用能力的「how-to」 | 结伴/委派工作 |
| 权威源 | TypeScript schema | Protocol Buffer（`a2a.proto`） |
| 传输基础 | JSON-RPC 2.0 | HTTP + JSON-RPC 2.0 / gRPC / HTTP-REST（多绑定） |
| 状态性 | [[无状态协议\|无状态]]（本版移除 session） | 有状态 [[A2A Task\|Task]]，经历生命周期 |
| 发现机制 | `server/discover` RPC | [[Agent Card]]（well-known URI / 目录） |
| 不透明性 | server 不能看进对话/其他 server | [[Opaque Execution]]：agent 不共享内部状态/工具 |
| 异步长任务 | Tasks 扩展（本版移出核心） | 原生 Async First（流式 + [[Push Notifications]]） |

## 两处值得注意的呼应

1. **同为 Registry 记录类型**——在 [[AWS Agent Registry]] 的[[四种记录类型]]里，MCP 和 Agent（A2A agent card）并列。Registry 因此同时是「工具目录」和「agent 目录」——恰好对应两个协议的两种关系。
2. **都靠 Agent Card / server metadata 发现**——A2A 的 [[Agent Card]] 可经「Registries/Catalogs」发现，而 Registry 本身把每个实例暴露为 [[Model Context Protocol|MCP]] server 供查询。发现层把两个协议缝到了一起。

## 关联
- 协议一: [[Model Context Protocol]]
- 协议二: [[Agent2Agent]]
- 共同编目于: [[AWS Agent Registry]]
- 记录类型: [[四种记录类型]]
- 来源: [[A2A Specification]]、[[MCP Specification (2026-07-28)]]
