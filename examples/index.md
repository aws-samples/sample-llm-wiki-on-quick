---
type: index
tags: [meta]
status: developing
summary: 整个 wiki 的内容目录，按类别分组。回答问题前先读这里定位相关页。
---
# Index

wiki 的内容目录。**每次 ingest 后更新这个文件。**

## Concepts

| 页面 | 摘要 | 更新 |
|---|---|---|
| [[LLM Wiki]] | 用 LLM 增量维护持久互链的 markdown wiki，知识编译一次并持续保鲜，替代每次查询重新检索的 RAG。 | 2026-09-02 |
| [[三层架构]] | LLM Wiki 的三层结构——raw sources（不可变源）、the wiki（LLM 拥有）、the schema（人机共同演进）。 | 2026-09-02 |
| [[三个操作]] | 维护 LLM Wiki 的三个操作——Ingest、Query、Lint。 | 2026-09-02 |
| [[RAG]] | 检索增强生成；作为 LLM Wiki 的对照基线，其局限是知识不累积。 | 2026-09-02 |
| [[Memex]] | Vannevar Bush 1945 年设想的个人策展知识存储；LLM Wiki 的思想渊源。 | 2026-09-02 |
| [[两个平面]] | AWS Agent Registry 内部的 Governance Plane（治理）与 Discovery Plane（发现）。 | 2026-09-02 |
| [[四种记录类型]] | Registry 可编目的四类记录——MCP、Agent(A2A)、Skill、Custom。 | 2026-09-02 |
| [[四种角色]] | Registry 的四种用户——Admins、Publishers、Consumers、Curators。 | 2026-09-02 |
| [[记录生命周期]] | Registry 记录的状态机——DRAFT→PENDING_APPROVAL→APPROVED/REJECTED→DEPRECATED。 | 2026-09-02 |
| [[Model Context Protocol]] | 让 LLM 应用连接工具/数据的开放协议，JSON-RPC、client-host-server、无状态；也是 Registry 的一种记录类型。 | 2026-09-02 |
| [[客户端-主机-服务器架构]] | MCP 的三方架构——一个 Host 管理多个 Client，每个 Client 与一个 Server 1:1 通信。 | 2026-09-02 |
| [[无状态协议]] | MCP 2026-07-28 的核心性质——每请求自包含携带版本与能力，移除了 initialize 握手和 session。 | 2026-09-02 |
| [[能力协商]] | MCP 基于能力的协商——client 每请求声明能力，server 经 server/discover 通告。 | 2026-09-02 |
| [[MCP 服务器原语]] | MCP server 的三种构件——Prompts（用户控制）、Resources（应用控制）、Tools（模型控制）。 | 2026-09-02 |
| [[MRTR 与 InputRequiredResult]] | MCP 消息模式之一——server 返回 input_required 索取输入，client 重试原请求时应答。 | 2026-09-02 |
| [[_meta 元数据]] | MCP 请求/响应附加元数据的 _meta 字段，承载每请求的协议版本、能力、日志级别等。 | 2026-09-02 |
| [[MCP 消息模式]] | MCP 支持的三种消息交互——请求响应、MRTR、订阅通知；基于 JSON-RPC 2.0。 | 2026-09-02 |
| [[MCP 安全与信任]] | MCP 安全四原则——用户同意与控制、数据隐私、工具安全；协议层不强制。 | 2026-09-02 |
| [[MCP 关键变更]] | MCP 2026-07-28 相对 2025-11-25 的关键变更——无状态化、server/discover、MRTR、Roots/Sampling/Logging 弃用。 | 2026-09-02 |
| [[Agent2Agent]] | 让独立 AI agent 作为对等方通信协作的开放协议；agent card 也是 Registry 的一种记录类型。 | 2026-09-02 |
| [[A2A 三层规范结构]] | A2A 规范的三层——Canonical Data Model（proto）、Abstract Operations、Protocol Bindings。 | 2026-09-02 |
| [[A2A Task]] | A2A 的基本工作单元，有状态、有生命周期，终态 COMPLETED/FAILED/CANCELED/REJECTED。 | 2026-09-02 |
| [[A2A 协议操作]] | A2A 绑定无关的核心操作——Send Message、流式、Get/List/Cancel/Subscribe Task、Push Config。 | 2026-09-02 |
| [[Agent Card]] | A2A Server 发布的 JSON 元数据，描述身份/能力/技能/端点，经 well-known URI 发现、可 JWS 签名。 | 2026-09-02 |
| [[A2A 消息与内容模型]] | A2A 承载内容的三对象——Message（通信轮次）、Part（最小单元）、Artifact（任务产出）。 | 2026-09-02 |
| [[Push Notifications]] | A2A 经 webhook 交付的异步任务更新，用于长任务或断连场景；载荷是 StreamResponse。 | 2026-09-02 |
| [[Shadow AI]] | 未注册、无监管的影子 agent/工具；Registry 用组织级 auto-detection 应对。 | 2026-09-02 |

## Entities

| 页面 | 摘要 | 更新 |
|---|---|---|
| [[Obsidian]] | 本地 markdown 知识管理工具；在 LLM Wiki 里充当人的浏览端与「IDE」。 | 2026-09-02 |
| [[qmd]] | 本地 markdown 搜索引擎，混合 BM25/向量检索加 LLM 重排，有 CLI 与 MCP server。 | 2026-09-02 |
| [[AWS Agent Registry]] | AWS 的企业级 agent/工具/技能统一治理与发现目录，2026-08-31 GA。 | 2026-09-02 |
| [[Amazon Bedrock AgentCore]] | AWS 运行/管理 agent 的平台（runtime + Gateway）；Registry auto-detection 的检测目标。 | 2026-09-02 |
| [[Amazon Quick]] | AWS 面向业务用户的界面；连接 Registry 后从 Integrations 页发现并启用 agent。 | 2026-09-02 |

## Sources

| 页面 | 素材 | 摘要 | 更新 |
|---|---|---|---|
| [[LLM Wiki (Karpathy)]] | `raw/articles/llm-wiki-karpathy.md` | Karpathy 提出的 LLM Wiki 模式原文摘要。 | 2026-09-02 |
| [[AWS Agent Registry (AWS Blog)]] | `raw/articles/aws-agent-registry.md` | AWS Agent Registry GA 公告原文摘要。 | 2026-09-02 |
| [[MCP Specification (2026-07-28)]] | `raw/articles/mcp-specification-2026-07-28.md` | MCP 官方规范 2026-07-28 版原文摘要。 | 2026-09-02 |
| [[A2A Specification]] | `raw/articles/a2a-specification.md` | A2A 协议官方规范节选原文摘要。 | 2026-09-02 |

## Synthesis

| 页面 | 摘要 | 更新 |
|---|---|---|
| [[A2A 与 MCP 的关系]] | A2A（agent↔agent 协作）与 MCP（agent→工具使用）是互补协议，在 Registry 里并列为记录类型。 | 2026-09-02 |
| [[A2A 委派端到端流程]] | 一个 agent 发现并委派另一个 agent 干活的端到端时序——发现 Agent Card→选传输→验签认证→Send Message 建 Task→拿结果。 | 2026-09-02 |

## 待消化

放进 `raw/` 但还没 ingest 的素材：

| 文件 | 加入日期 |
|---|---|
