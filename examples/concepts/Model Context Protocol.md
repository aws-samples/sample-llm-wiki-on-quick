---
type: concept
tags: [mcp, protocol, tools, agent, json-rpc, stateless]
status: stable
summary: 让 LLM 应用连接外部数据源和工具的开放协议，基于 JSON-RPC、client-host-server 架构、无状态；MCP server 也是 AWS Agent Registry 的一种记录类型。
---
# Model Context Protocol

一个开放协议（简称 MCP），让 LLM 应用与外部数据源和工具无缝集成——为 AI IDE、聊天界面、自定义 AI 工作流提供把 LLM 连接到所需上下文的标准方式。受 Language Server Protocol（LSP）启发：LSP 标准化了跨开发工具支持编程语言，MCP 类似地标准化了把上下文和工具集成进 AI 应用生态。权威依据是 [[MCP Specification (2026-07-28)]] 的 TypeScript schema。

## 协议本体

- **架构**——[[客户端-主机-服务器架构]]：一个 Host 管理多个 Client，每个 Client 与恰好一个 Server 1:1 通信，Host 强制安全边界。
- **消息**——基于 JSON-RPC 2.0，支持三种[[MCP 消息模式]]（请求响应、[[MRTR 与 InputRequiredResult|MRTR]]、订阅通知）。
- **无状态**——[[无状态协议]]：每个请求自包含，靠 [[_meta 元数据]]携带协议版本与能力。
- **能力协商**——[[能力协商]]：client/server 每请求声明能力，server 通过 `server/discover` 通告。
- **服务器原语**——[[MCP 服务器原语]]：Prompts（用户控制）、Resources（应用控制）、Tools（模型控制）。
- **安全**——[[MCP 安全与信任]]：用户同意、数据隐私、工具安全三原则，协议层不强制、由实现者落地。
- **本版变更**——[[MCP 关键变更]]：2026-07-28 相对 2025-11-25 的无状态化等重大调整。

## 在企业治理场景里的角色

除了协议本体，本 vault 也从 [[AWS Agent Registry (AWS Blog)]] 了解 MCP 在企业治理里的用法：

- **一种记录类型**——MCP server（及其工具、资源、prompts）是 [[AWS Agent Registry]] 支持编目的[[四种记录类型]]之一。
- **发现接口**——Registry 的 Search API 本身也暴露为一个 MCP server，供自动化流水线和 agentic 工作流程序化查找。
- **IDE 原生连接**——MCP 兼容 IDE（Kiro、Claude Code）可原生连到 registry 实例（每个实例暴露为 MCP server），用 Dynamic Client Registration（DCR）在运行时建立信任。注意 MCP 官方规范已把 DCR 列入弃用、转向 Client ID Metadata Documents（见 [[MCP 关键变更]]）。
- **auto-detection 目标**——组织级 auto-detection 会检测跑在 [[Amazon Bedrock AgentCore]] 上的 MCP server。

> [[qmd]] 也暴露一个 MCP server，是本 vault 里 LLM Wiki 簇与 AWS 簇之外的又一处 MCP 实例。

常见叫法：Model Context Protocol、MCP、MCP server、模型上下文协议、agent 工具连接协议、开放上下文协议。

## 关联
- 原文规范: [[MCP Specification (2026-07-28)]]
- 架构: [[客户端-主机-服务器架构]]
- 无状态性质: [[无状态协议]]
- 能力协商: [[能力协商]]
- 服务器原语: [[MCP 服务器原语]]
- 消息模式: [[MCP 消息模式]]
- 多轮请求: [[MRTR 与 InputRequiredResult]]
- 元数据: [[_meta 元数据]]
- 安全: [[MCP 安全与信任]]
- 关键变更: [[MCP 关键变更]]
- 编目于: [[AWS Agent Registry]]
- 作为记录类型: [[四种记录类型]]
- 运行平台: [[Amazon Bedrock AgentCore]]
- 本地实例: [[qmd]]
