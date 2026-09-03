---
type: concept
tags: [mcp, changelog, versioning, deprecation]
status: developing
summary: MCP 2026-07-28 相对 2025-11-25 的关键变更——协议无状态化、移除 session、新增 server/discover、subscriptions/listen、MRTR、tasks 转扩展，以及 Roots/Sampling/Logging 弃用。
---
# MCP 关键变更

[[Model Context Protocol]] 2026-07-28 版相对上一版 2025-11-25 的主要变更。完整清单见 [[MCP Specification (2026-07-28)]]。

## 重大变更

1. **移除协议级 session** 和 `Mcp-Session-Id` 头；需跨调用状态的 server 改用显式的、server 铸造的句柄作普通工具参数传递。
2. **协议无状态化**——移除 `initialize`/`notifications/initialized` 握手，每请求在 `_meta` 携带协议版本和 client 能力（见 [[无状态协议]]、[[_meta 元数据]]）；版本不匹配返回 `UnsupportedProtocolVersionError`。
3. **新增 `server/discover`**——server MUST 实现，通告支持的版本、能力和身份（见 [[能力协商]]）。
4. **`subscriptions/listen`** 取代 HTTP GET 端点和 `resources/subscribe`/`unsubscribe`——单条长连 POST-response 流承载 opt-in 的变更通知（见 [[MCP 消息模式]]）。
5. **移除 `ping`、`logging/setLevel`、`notifications/roots/list_changed`**——日志级别改为每请求经 `_meta` 的 `logLevel` 设置。
6. **tasks 移出核心进官方扩展**（`io.modelcontextprotocol/tasks`）——用 `tasks/get` 轮询取代阻塞式 `tasks/result`，新增 `tasks/update`。
7. **引入 MRTR 模式**——取代 server 发起请求的旧做法（见 [[MRTR 与 InputRequiredResult]]）。
8. **所有 result 带必需 `resultType`**（`"complete"`/`"input_required"`）。
9. **移除 SSE 流可恢复性与消息重投**——流断则丢失在途请求，client 须以新 id 重发。

## 弃用（最短 12 个月窗口）

- **Roots、Sampling、Logging** 三特性弃用——建议迁移：Roots→工具参数/资源 URI；Sampling→直连 LLM provider API；Logging→stderr 或 OpenTelemetry。
- **HTTP+SSE 传输**弃用——迁往 Streamable HTTP。
- `includeContext` 的 `"thisServer"`/`"allServers"` 值弃用。
- **OAuth 2.0 Dynamic Client Registration**（RFC 7591）弃用——改用 Client ID Metadata Documents。注意这与 [[AWS Agent Registry]] 里 IDE 连接用的 DCR 是同一机制，MCP 官方已转向 CIMD。

## 治理

采纳特性生命周期与弃用政策（Active / Deprecated / Removed 三态）；PR 式 SEP 工作流。

常见叫法：MCP 关键变更、changelog、key changes、2026-07-28 变更、无状态化变更、弃用特性、deprecated features、SEP。

## 关联
- 所属协议: [[Model Context Protocol]]
- 原文: [[MCP Specification (2026-07-28)]]
- 无状态化: [[无状态协议]]
- 相关: [[MCP 消息模式]]、[[MRTR 与 InputRequiredResult]]、[[能力协商]]
