---
type: concept
tags: [mcp, elicitation, client-feature, mrtr]
status: developing
summary: MCP 里 client 向 server 提供的主要功能——server 发起、向用户索取额外信息；本版通过 MRTR 的 input_required 模式实现，是 Sampling/Roots 弃用后仅存的 client 侧功能。
---
# Elicitation

Elicitation 是 [[Model Context Protocol]] 里 **client 向 server 提供**的功能：由 server 发起、向用户索取额外信息。在 client-server 的功能分工里，server 通过 [[MCP 服务器原语|原语]]（Resources/Prompts/Tools）向 client 提供上下文与能力，而反方向——client 向 server 提供的功能——主要就是 Elicitation。

## 本版怎么实现

2026-07-28 版协议变[[无状态协议|无状态]]后，server 不能主动向 client 推请求，Elicitation 因此改由 [[MRTR 与 InputRequiredResult]] 模式承载：

- server 在响应里返回 `InputRequiredResult`（`resultType: "input_required"`），其 `inputRequests` 声明需要的输入。
- client 在**重试原请求**时用 `inputResponses` 补上用户提供的信息。
- server 若需跨重试关联同一次 elicitation，把自己的标识符编码进 `requestState`。

这取代了旧版 server 主动调 `elicitation/create` 的做法（见 [[MCP 关键变更]]）。

## 与 Sampling、Roots 的关系

MRTR 承载的 client 输入有三类：sampling、elicitation、roots。但其中 **Sampling 和 Roots 已在本版弃用**（见 [[MCP 关键变更]]，建议迁移：Sampling→直连 LLM provider API，Roots→工具参数/资源 URI），因此 Elicitation 是 client 侧仅存的、仍推荐使用的功能。client 在[[能力协商|能力]]里通过 `_meta.io.modelcontextprotocol/clientCapabilities` 声明是否支持 elicitation 处理。

常见叫法：Elicitation、索取输入、向用户索取额外信息、client 侧功能、client 向 server 提供的功能、elicitation/create、input_required 输入类型。

## 关联
- 所属协议: [[Model Context Protocol]]
- 实现模式: [[MRTR 与 InputRequiredResult]]
- 分工对照: [[MCP 服务器原语]]
- 声明机制: [[能力协商]]
- 变更出处: [[MCP 关键变更]]
- 原文: [[MCP Specification (2026-07-28)]]
