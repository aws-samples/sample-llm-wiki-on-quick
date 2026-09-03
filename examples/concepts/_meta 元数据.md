---
type: concept
tags: [mcp, meta, protocol-fields, metadata]
status: developing
summary: MCP 请求/响应里附加元数据的 _meta 字段——承载每请求的协议版本、client 能力、日志级别、订阅 ID 等，是无状态协议自包含请求的载体。
---
# _meta 元数据

`_meta` 是 [[Model Context Protocol]] 里让 client 和 server 给交互附加元数据的属性/参数。因为协议是[[无状态协议|无状态]]的，每个请求靠 `_meta` 自带协议级信息，无需依赖连接状态。

## key 名格式

两段：可选 **prefix** + **name**。prefix 是点分 label 加斜杠（建议反向 DNS，如 `com.example/`）；prefix 第二个 label 为 `modelcontextprotocol` 或 `mcp` 的**保留**给 MCP（如 `io.modelcontextprotocol/`、`dev.mcp/`），但 `com.example.mcp/` 不保留（第二段是 `example`）。

## 保留 key

| Key | 用途 |
|---|---|
| `progressToken` | 让请求加入进度通知 |
| `io.modelcontextprotocol/protocolVersion` | 请求的协议版本（必需） |
| `io.modelcontextprotocol/clientInfo` | client 名与版本（可选） |
| `io.modelcontextprotocol/clientCapabilities` | client 能力（必需，见[[能力协商]]） |
| `io.modelcontextprotocol/logLevel` | server 该请求的最低日志级别（可选） |
| `io.modelcontextprotocol/subscriptionId` | 把通知关联到发起它的订阅 |
| `traceparent` / `tracestate` / `baggage` | OpenTelemetry trace context（prefix 要求的例外） |

缺任一必需字段的请求是畸形的，server **MUST** 以 `-32602`（Invalid params）拒绝，HTTP 返回 400。响应侧 server **SHOULD** 在每个 result 的 `_meta` 带 `serverInfo`。注意 clientInfo/serverInfo 自报、不被协议验证、**SHOULD NOT** 用于安全决策。

常见叫法：_meta、元数据字段、meta 字段、每请求协议字段、protocolVersion/clientCapabilities、保留 key。

## 关联
- 所属协议: [[Model Context Protocol]]
- 承载的机制: [[能力协商]]
- 相关性质: [[无状态协议]]
