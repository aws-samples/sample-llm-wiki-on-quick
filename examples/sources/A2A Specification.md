---
type: source
tags: [a2a, protocol, specification, agent-card, task, mcp]
status: stable
summary: A2A 协议官方规范节选原文摘要——三层规范结构、核心协议操作、数据模型（Task/Message/Part/Artifact）、Agent Card 发现与签名、以及与 MCP 的互补关系。
---
# A2A Specification

> 忠实转述 `raw/articles/a2a-specification.md`（官方规范节选），不加解读。解读见 [[Agent2Agent]] 及相关 concept 页；与 MCP 的对比见 synthesis 页 [[A2A 与 MCP 的关系]]。
>
> 来源: https://a2a-protocol.org/latest/specification/
> 仓库: github.com/a2aproject/A2A，docs/specification.md
> 下载日期: 2026-09-02。原文 3618 行，此处节选 Introduction/Terminology、Protocol Operations、Data Model、Agent Card、Appendix B。

## 1. Introduction

Agent2Agent（A2A）协议是一个开放标准，用于促进**独立、可能不透明的 AI agent 系统**之间的通信与互操作。在 agent 可能由不同框架、语言、厂商构建的生态里，A2A 提供共同语言与交互模型。目标是让 agent 能：发现彼此能力、协商交互模态（文本/文件/结构化数据）、管理协作任务、**在无需访问彼此内部状态、记忆或工具的前提下**安全交换信息。

**关键目标**：互操作性、协作（委派任务、交换上下文）、发现（动态找到并理解其他 agent 能力）、灵活性（同步请求响应 / 流式实时更新 / 异步 push 通知）、安全（对齐企业级 web 安全实践）、异步性（原生支持长任务与 human-in-the-loop）。

**指导原则**：Simple（复用 HTTP、JSON-RPC 2.0、SSE 等成熟标准）、Enterprise Ready、Async First、Modality Agnostic、**Opaque Execution**（基于声明的能力和交换的信息协作，无需共享内部想法/计划/工具实现）。

## 1.3 三层规范结构

- **Layer 1 — Canonical Data Model**：核心数据结构与消息格式，所有实现都必须理解，以 Protocol Buffer 消息表达、协议无关。
- **Layer 2 — Abstract Operations**：A2A agent 必须支持的基本能力与行为，独立于具体协议暴露方式。
- **Layer 3 — Protocol Bindings**：抽象操作与数据结构到具体协议绑定的映射（JSON-RPC、gRPC、HTTP/REST、自定义），含方法名、端点模式、协议特定行为。

分层保证：核心语义跨绑定一致；新绑定无需改动数据模型即可加入；开发者可独立于绑定推理 A2A 操作。

**规范内容权威性**：`spec/a2a.proto` 是所有协议数据对象与请求/响应消息的**唯一权威规范定义**。生成的 `spec/a2a.json` 是非规范构建产物。SDK 绑定、schema 等派生形式 MUST 从 proto 重新生成而非手改。变更控制：字段重命名时旧名保留并标 deprecated 直到下个大版本；遗留文档锚点 MUST 保留（隐藏 HTML 锚点）避免断链；弃用名 SHOULD NOT 早于替代引入后的下个大版本移除。

## 2. Terminology（核心概念）

- **A2A Client**：代表用户或另一系统向 A2A Server 发起请求的应用或 agent。
- **A2A Server（Remote Agent）**：暴露 A2A 兼容端点、处理任务并给出响应的 agent。
- **Agent Card**：A2A Server 发布的 JSON 元数据文档，描述其身份、能力、技能、服务端点和认证要求。
- **Message**：client 与 remote agent 之间的一个通信轮次，有 `role`（"user" 或 "agent"），含一个或多个 `Part`。
- **Task**：A2A 管理的基本工作单元，有唯一 ID，**有状态**并经历定义好的生命周期。
- **Part**：Message 或 Artifact 内的最小内容单元，可含文本、文件引用或结构化数据。
- **Artifact**：agent 作为任务结果生成的输出（文档、图像、结构化数据），由 `Part` 组成。
- **Streaming**：任务的实时增量更新（状态变化、artifact 分块），经协议特定流机制交付。
- **Push Notifications**：经 server 发起的 HTTP POST 到 client 提供的 webhook URL 交付的异步任务更新，用于长任务或断连场景。
- **Context**：可选标识符，把相关任务和消息逻辑分组。
- **Extension**：agent 提供核心规范之外额外功能或数据的机制。

## 3. Protocol Operations（核心操作，绑定无关）

- **Send Message**：发起 agent 交互的主操作。client 发消息，收到追踪处理的 `Task` 或直接的 `Message` 响应。操作 MUST 立即返回。
- **Send Streaming Message**：类似但处理中实时流式更新。返回 Stream Response（初始 Task 或 Message，后续 TaskStatusUpdateEvent / TaskArtifactUpdateEvent）；任务达终态时流关闭。
- **Get Task**：取先前任务的当前状态（状态、artifacts、可选 history），用于轮询或取终态。
- **List Tasks**：列任务，支持过滤和**游标分页**（pageToken/nextPageToken），MUST 按状态时间戳降序排（最近更新在前），MUST 只返回已认证 client 可见的任务。
- **Cancel Task**：请求取消进行中任务，成功不保证（可能已完成/失败或当前阶段不支持取消）。
- **Subscribe to Task**：对已有任务建流式连接收更新，首事件 MUST 是当前 Task 状态（防 GetTask 与 Subscribe 之间丢信息）。
- **Push Notification Config**：Create / Get / List / Delete 四个操作管理任务的 webhook 推送配置。

**错误**（选摘）：ContentTypeNotSupportedError、UnsupportedOperationError（向终态任务发消息、或 agent 不支持流式）、TaskNotFoundError、TaskNotCancelableError、PushNotificationNotSupportedError。

## 4. Data Model（数据模型，Protocol Buffers）

所有绑定 MUST 提供功能等价的表示。核心对象：Task、TaskStatus、TaskState（枚举，终态含 COMPLETED/FAILED/CANCELED/REJECTED）、Message、Role（user/agent 枚举）、Part、Artifact。流事件：TaskStatusUpdateEvent、TaskArtifactUpdateEvent。Push 对象：TaskPushNotificationConfig、AuthenticationInfo、Push Notification Payload（webhook 收到的是 StreamResponse 对象，恰含 task/message/statusUpdate/artifactUpdate 之一）。发现对象：AgentCard、AgentProvider、AgentCapabilities、AgentExtension、AgentSkill、AgentInterface、AgentCardSignature。安全对象：SecurityScheme 及 APIKey/HTTPAuth/OAuth2/OpenIdConnect/MutualTls 等方案与 OAuth 流。

**Push Notification 交付保证**：agent MUST 对每个配置的 webhook 至少尝试交付一次，MAY 指数退避重试，SHOULD 设 10–30 秒超时；client MUST 回 2xx 确认、SHOULD 幂等处理（可能重复投递）、MUST 校验 task ID、SHOULD 验证通知来源。

## 8. Agent Discovery: The Agent Card

A2A Server **MUST** 提供 Agent Card，描述 server 身份、能力、技能、交互要求。发现机制：Well-Known URI（`https://{server_domain}/.well-known/agent-card.json`）、Registries/Catalogs（查询策展的 agent 目录）、Direct Configuration。

**协议声明**：`supportedInterfaces` SHOULD 按偏好顺序声明所有支持的协议组合，第一条为首选；client MUST 解析并选第一个支持的 transport、用对应 URL、按所选 AgentInterface 的 `tenant` 值设请求。

**签名**：Agent Card MAY 用 JWS（RFC 7515）签名。签名前 MUST 用 JCS（RFC 8785）规范化：按 proto 字段存在语义处理默认值（optional 未设则省略、REQUIRED 始终在、非 REQUIRED 空值省略），词典序排 key，去无意义空白，排除 `signatures` 字段本身。protected header MUST 含 alg/typ/kid，MAY 含 jku。client 验证 SHOULD 至少验一个签名后才信任，公钥 SHOULD 经 HTTPS 取，过期/吊销的 key MUST NOT 用，多签名 MAY 支持 key 轮换。

**缓存**：Agent Card 变化不频繁，server SHOULD 带 `Cache-Control`(max-age)、`ETag`（由 version 或内容 hash 派生）、MAY 带 `Last-Modified`；client SHOULD 遵循 RFC 9111 缓存语义、过期后用条件请求（If-None-Match/If-Modified-Since）。

样例 Agent Card 含 name/description/supportedInterfaces（JSONRPC/GRPC/HTTP+JSON 三绑定）/provider/version/capabilities（streaming、pushNotifications）/securitySchemes（OpenIdConnect）/skills（每个含 id/name/description/tags/examples/inputModes/outputModes）/signatures。

## Appendix B. 与 MCP 的关系

A2A 与 [[Model Context Protocol|MCP]] 是**互补协议**，面向 agentic 系统的不同方面：

- **MCP**：标准化 AI 模型/agent 如何连接并使用**工具、API、数据源等外部资源**——描述工具能力、传入参数、接收结构化输出。是 agent *使用*某能力/资源的「how-to」。
- **A2A**：标准化独立、往往不透明的 **AI agent 之间如何作为对等方通信协作**——发现彼此、协商模态、管理共享任务、交换上下文或复杂结果。是 agent 之间*结伴*或*委派*工作。

**如何协同**：一个 A2A Client agent 可请求 A2A Server agent 执行复杂任务，Server agent 反过来可能用 MCP 与若干底层工具/API/数据源交互，以完成该 A2A 任务。

## 关联
- 主概念页: [[Agent2Agent]]
