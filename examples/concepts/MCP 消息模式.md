---
type: concept
tags: [mcp, message-patterns, json-rpc]
status: developing
summary: MCP 核心协议支持的三种消息交互模式——请求响应、多轮往返请求（MRTR）、订阅通知；全部基于 JSON-RPC 2.0。
---
# MCP 消息模式

[[Model Context Protocol]] 的所有消息遵循 JSON-RPC 2.0，核心协议支持三种消息模式：

1. **Request and Response（请求响应）**——client 发请求，server 以 result 或 error 应答。请求 MUST 带非 null 的 string/integer id；result 含 `resultType`；error 含 `code`+`message`。
2. **Multi Round-Trip Requests（MRTR，多轮往返请求）**——server 需要额外 client 输入才能完成请求。详见 [[MRTR 与 InputRequiredResult]]。
3. **Subscribe and Notify（订阅通知）**——client 通过 `subscriptions/listen` 订阅 server 的通知流，通知以 `subscriptionId` 标记。这是本版取代旧 `resources/subscribe` 和 HTTP GET 端点的机制（见 [[MCP 关键变更]]）。

## 消息类型

- **Requests**：client→server 发起操作，带 id。
- **Responses**：Result（成功，带 `resultType`：`"complete"` 或 `"input_required"`）或 Error（带 `code`/`message`/可选 `data`）。
- **Notifications**：单向消息，无 id，接收方 MUST NOT 响应。

常见叫法：MCP 消息模式、message patterns、三种消息模式、请求响应、订阅通知、subscribe and notify、JSON-RPC 消息。

## 关联
- 所属协议: [[Model Context Protocol]]
- MRTR 细节: [[MRTR 与 InputRequiredResult]]
- 变更出处: [[MCP 关键变更]]
