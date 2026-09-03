---
type: source
tags: [mcp, protocol, specification, json-rpc, stateless]
status: stable
summary: MCP 官方规范 2026-07-28 版原文摘要——client-host-server 架构、JSON-RPC 消息、无状态化、能力协商、服务器原语（Prompts/Resources/Tools）、消息模式与本版重大变更。
---
# MCP Specification (2026-07-28)

> 忠实转述 `raw/articles/mcp-specification-2026-07-28.md`，不加解读。解读见 [[Model Context Protocol]] 及相关 concept 页。
>
> 来源: https://modelcontextprotocol.io/specification/2026-07-28
> 仓库: github.com/modelcontextprotocol/modelcontextprotocol，docs/specification/2026-07-28/
> 下载日期: 2026-09-02。官方规范原文，按 index / architecture / basic / server / changelog 顺序拼接。

## 总览（index）

MCP 是一个开放协议，让 LLM 应用与外部数据源和工具无缝集成——无论构建 AI IDE、增强聊天界面还是自定义 AI 工作流，MCP 提供连接 LLM 与所需上下文的标准方式。规范以 TypeScript schema（`schema.ts`）为权威依据。文档中大写的 MUST / SHOULD / MAY 等按 BCP 14（RFC 2119 + RFC 8174）解释。

MCP 让应用能：与语言模型共享上下文信息、向 AI 系统暴露工具和能力、构建可组合的集成与工作流。协议用 [JSON-RPC](https://www.jsonrpc.org/) 2.0 消息在三方之间通信：

- **Hosts**：发起连接的 LLM 应用。
- **Clients**：host 应用内的连接器。
- **Servers**：提供上下文和能力的服务。

MCP 受 Language Server Protocol（LSP）启发——LSP 标准化了如何跨开发工具生态支持编程语言，MCP 类似地标准化了如何把额外上下文和工具集成进 AI 应用生态。

**Base Protocol**：JSON-RPC 消息格式、无状态自包含请求、按请求协商能力。

**Features**——servers 向 clients 提供：Resources（上下文与数据）、Prompts（模板化消息与工作流）、Tools（供 AI 模型执行的函数）。clients 向 servers 提供：Elicitation（server 发起、向用户索取额外信息）。

**附加工具**：Configuration、Progress tracking、Cancellation、Error reporting。

**Extensions**（核心协议之外的可选扩展，需 client 和 server 双方在初始化时显式协商）：Tasks（长任务异步执行，含轮询、中途输入、持久句柄）、Skills over MCP（agent 工作流的结构化指令）、MCP Apps（对话内联的交互式 UI 元素）。

**安全与信任**四原则：用户同意与控制、数据隐私（host 暴露用户数据给 server 前须获显式同意）、工具安全（tool 是任意代码执行，须谨慎；工具行为描述/annotation 除非来自可信 server 否则视为不可信）。MCP 协议层无法强制这些原则，实现者 SHOULD 建健壮的同意/授权流。

## 架构（architecture）

MCP 采用 **client-host-server** 架构，每个 host 可运行多个 client 实例。MCP 是**无状态协议**：每个请求自包含，携带自己的协议版本和能力。基于 JSON-RPC，聚焦 client 与 server 间的上下文交换与 sampling 协调。

- **Host**：容器与协调者——创建管理多个 client 实例、控制连接权限与生命周期、强制安全策略与同意要求、处理用户授权、协调 AI/LLM 集成与 sampling、跨 client 聚合上下文。
- **Clients**：每个 client 由 host 创建，与**恰好一个 server** 1:1 通信——每个请求附带协议版本与能力、双向路由消息、管理订阅与通知、维持 server 间安全边界。
- **Servers**：提供专门的上下文与能力——通过 MCP 原语暴露 resources/tools/prompts、独立聚焦运作、通过回复里的 `InputRequiredResult` 请求 client 输入（sampling、elicitation、roots）、必须尊重安全约束、可为本地进程或远程服务。

**设计原则**：server 应极易构建；server 应高度可组合；server 不能读取整个对话、也不能「看进」其他 server（完整对话历史留在 host，host 强制安全边界）；功能可渐进添加（核心协议最小，能力按需协商，向后兼容）。

**能力协商**：基于能力的协商系统，client 和 server 在每个请求上声明所支持功能。client 在每个请求的 `_meta.io.modelcontextprotocol/clientCapabilities` 里带上能力；server 通过 `server/discover` 响应通告能力（client 可在任何其他请求前调用它做前置能力发现）。server 声明如工具支持、资源订阅、prompt 模板；client 声明如 sampling 支持、elicitation 处理。

## 基础协议（basic）

组成部分：Base Protocol（核心 JSON-RPC 消息类型）、版本与兼容（协议版本协商、扩展协商、与早期版本互操作）、消息模式（请求响应、MRTR、订阅通知）、Authorization（HTTP 传输的认证授权框架）、Server Features、Client Features、Utilities。所有实现 MUST 支持 base protocol、版本、消息模式；其他 MAY 按需实现。

**消息类型**（全部遵循 JSON-RPC 2.0）：

- **Requests**：client→server 发起操作，MUST 含 string 或 integer 的 id，且 id MUST NOT 为 null，MUST NOT 与未完成请求重复。
- **Responses**：Result responses（成功，MUST 含与请求相同 id、含 `result` 字段、`result` MUST 含 `resultType` 字段）或 Error responses。**ResultType**：`"complete"` 表示成功完成；`"input_required"` 表示需更多信息（result 含 `InputRequiredResult`）；扩展 MAY 加值；client 无法识别的 resultType MUST 视为无效；缺失 resultType（早期版本 server）MUST 视为 `"complete"`。
- **Error responses**：含 `error`（`code` 整数 + `message`，可选 `data`）。用标准 JSON-RPC 错误码；`-32000~-32099` 为实现定义 server 错误，MCP 分区：`-32000~-32019` 遗留（新实现 SHOULD NOT 用），`-32020~-32099` 保留给 MCP 规范。新定义错误码：`-32020` HeaderMismatch、`-32021` MissingRequiredClientCapability、`-32022` UnsupportedProtocolVersion。旧码 `-32002`（资源未找到，已被 `-32602` 取代）、`-32042` 保留不复用。
- **Notifications**：单向消息，接收方 MUST NOT 响应，MUST NOT 含 id。

**消息模式**三种：Request and Response；Multi Round-Trip Requests（MRTR，server 需额外 client 输入——sampling/elicitation/roots——才能完成请求）；Subscribe and Notify（client 订阅 server 的通知流）。

**无状态性**：处理请求所需的全部信息都在请求本身。server 独立处理每个请求，不从先前请求推断状态（即使同一连接）。server MUST NOT 依赖同连接的先前请求建立上下文（每请求在 `_meta` 供元数据）；跨请求的状态（长任务、应用级句柄）MUST 由 client 每请求传显式标识符引用。开放连接（如 STDIO 进程）不是对话或会话。`subscriptions/listen` 这类长连接仍是请求/响应，响应是开放的通知流。

**Auth**：为 HTTP 提供 Authorization 框架；HTTP 传输 SHOULD 遵循，STDIO 传输 SHOULD NOT 遵循（改从环境取凭据）。

**Schema**：完整协议由 TypeScript schema 定义（source of truth），另有自动生成的 JSON Schema。协议内用 JSON Schema 校验：默认方言 JSON Schema 2020-12；实现 MUST 支持 2020-12；`$ref` MUST NOT 自动解引用网络 URI（可选开启但默认禁用，须 allowlist、拒绝环回/链路本地/私网、限时限量）；组合关键字（anyOf/oneOf/allOf/if-then-else、$defs）SHOULD 设深度/子模式数/时间预算上限防 DoS。

**`_meta` 字段**：允许 client/server 附加元数据。key 名两段（可选 prefix + name）；prefix 第二个 label 为 `modelcontextprotocol` 或 `mcp` 的保留给 MCP。保留 key 含 `progressToken`、`io.modelcontextprotocol/protocolVersion`、`clientInfo`、`clientCapabilities`、`logLevel`、`subscriptionId`，以及 OpenTelemetry 的 `traceparent`/`tracestate`/`baggage`。每请求协议字段：`protocolVersion`（必需）、`clientCapabilities`（必需）、`clientInfo`（可选）、`logLevel`（可选）；缺必需字段 MUST 以 `-32602` 拒绝（HTTP 400）。clientInfo/serverInfo 自报、不被协议验证、SHOULD NOT 用于安全决策。

**`icons` 字段**：server 为 resources/tools/prompts/implementations 暴露视觉标识。Icon 含 `src`（HTTPS 或 data URI）、可选 `mimeType`/`sizes`/`theme`。client 渲染 MUST 支持 png/jpeg，SHOULD 支持 svg/webp。安全：视 icon 为不可信输入、拒绝 `javascript:`/`file:` 等不安全 scheme、无凭据拉取、按 magic bytes 校验类型。

## 服务器功能（server）

三种原语及其控制层级：

| 原语 | 控制方 | 描述 | 例子 |
|---|---|---|---|
| Prompts | 用户控制 | 用户选择调用的交互式模板 | 斜杠命令、菜单项 |
| Resources | 应用控制 | client 附加与管理的上下文数据 | 文件内容、git 历史 |
| Tools | 模型控制 | 暴露给 LLM 采取行动的函数 | API POST、写文件 |

## 关键变更（changelog，相对 2025-11-25）

**重大变更**：

1. 移除协议级 sessions 和 `Mcp-Session-Id` 头；需跨调用状态的 server 用显式的、server 铸造的句柄作普通工具参数传递（SEP-2567）。
2. **让 MCP 无状态**：移除 `initialize`/`notifications/initialized` 握手，每请求在 `_meta` 携带协议版本和 client 能力；版本不匹配返回 `UnsupportedProtocolVersionError`（SEP-2575）。
3. 新增 **`server/discover`**：server MUST 实现此 RPC 通告支持的版本、能力和身份（SEP-2575）。
4. 用 **`subscriptions/listen`** 取代 HTTP GET 端点和 `resources/subscribe`/`unsubscribe`：单条长连 POST-response 流承载 opt-in 的 server→client 变更通知（`toolsListChanged` 等），server 用 `subscriptionId` 标记通知（SEP-2575）。
5. 移除 `ping`、`logging/setLevel`、`notifications/roots/list_changed`；日志级别改为每请求经 `_meta` 的 `logLevel` 设置（SEP-2575）。
6. 把实验性 **tasks** 移出核心协议进官方扩展（`io.modelcontextprotocol/tasks`）：用 `tasks/get` 轮询取代阻塞式 `tasks/result`，新增 `tasks/update`，移除 `tasks/list`（SEP-2663）。
7. 引入 **MRTR（Multi Round-Trip Requests）** 模式，取代先前发送 server 发起请求（`roots/list`、`sampling/createMessage`、`elicitation/create`）的做法：server 返回 `InputRequiredResult`（`resultType: "input_required"`），client 在重试原请求时用 `inputResponses` 应答（SEP-2322）。
8. 所有 result 现带必需的 `resultType`（`"complete"` / `"input_required"`），早期 server 省略时 client MUST 视为 `"complete"`（SEP-2322）。
9. 从 Streamable HTTP 移除 SSE 流可恢复性与消息重投（`Last-Event-ID`、SSE event id）；流断则丢失在途请求，client MUST 以新请求 id 重发（SEP-2575）。

**次要变更**（选摘）：`ClientCapabilities`/`ServerCapabilities` 加 `extensions` 字段；记录 OpenTelemetry trace context 约定；`tools/list` SHOULD 确定性排序以利缓存；Streamable HTTP POST 要求 `Mcp-Method`/`Mcp-Name` 头；`tools/list` 等结果经 `CacheableResult` 要求 `ttlMs`/`cacheScope`；资源未找到错误码 `-32002`→`-32602`；错误码分配政策与重编号（HeaderMismatch `-32001`→`-32020` 等）。

**弃用**（保留但计划移除，最短 12 个月弃用窗口）：Roots、Sampling、Logging 三特性（SEP-2577，建议迁移：Roots→工具参数/资源 URI、Sampling→直连 LLM provider API、Logging→stderr 或 OpenTelemetry）；HTTP+SSE 传输（迁往 Streamable HTTP）；`includeContext` 的 `"thisServer"`/`"allServers"` 值；OAuth 2.0 Dynamic Client Registration（RFC 7591，改用 Client ID Metadata Documents）。

**治理**：采纳特性生命周期与弃用政策（Active/Deprecated/Removed 三态）；PR 式 SEP 工作流。

## 关联
- 主概念页: [[Model Context Protocol]]
