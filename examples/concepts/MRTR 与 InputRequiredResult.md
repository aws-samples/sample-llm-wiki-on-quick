---
type: concept
tags: [mcp, mrtr, input-required, message-pattern]
status: developing
summary: MCP 三种消息模式之一——server 需要额外 client 输入时返回 resultType 为 input_required 的结果，client 在重试原请求时带上输入应答。
---
# MRTR 与 InputRequiredResult

**Multi Round-Trip Requests（MRTR，多轮往返请求）**是 [[Model Context Protocol]] 的三种[[MCP 消息模式|消息模式]]之一：当 server 需要额外的 client 输入（sampling、elicitation 或 roots）才能完成一个请求时使用。

## 怎么工作

- server 返回一个 `InputRequiredResult`——`resultType: "input_required"`，其 `inputRequests` 字段携带所需额外信息的请求。
- client 在**重试原请求**时用 `inputResponses` 提供所请求的信息。
- 所有 result 都带必需的 `resultType`：普通结果为 `"complete"`，MRTR 中间结果为 `"input_required"`；早期版本 server 省略该字段时 client **MUST** 视为 `"complete"`。

## 为什么这样设计

这是本版（2026-07-28）的重大变更（见 [[MCP 关键变更]]）：MRTR 取代了先前「server 发起请求」的做法（`roots/list`、`sampling/createMessage`、`elicitation/create`）。因为协议变[[无状态协议|无状态]]，server 不能主动向 client 推请求，只能在响应里声明「我还需要什么」，由 client 重试时补上——server 若需跨重试关联一次 elicitation，把自己的标识符编码进 `requestState`。

常见叫法：MRTR、Multi Round-Trip Requests、多轮往返请求、InputRequiredResult、input_required、server 索取输入、多轮请求模式。

## 关联
- 所属协议: [[Model Context Protocol]]
- 消息模式: [[MCP 消息模式]]
- 变更出处: [[MCP 关键变更]]
- 相关性质: [[无状态协议]]
