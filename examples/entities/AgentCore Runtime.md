---
type: entity
tags: [aws, agentcore, runtime, microvm, hosting]
status: developing
summary: AgentCore 服务簇的 serverless agent 托管运行时，每会话独占 microVM 隔离，支持 MCP/A2A 与两种计算类型。
---
# AgentCore Runtime

[[AgentCore 服务簇]]中负责**运行 agent** 的核心服务：安全、serverless 的运行时，部署和伸缩 agent 与工具。快速冷启动、真正的会话隔离、内置身份，支持多模态与多 agent。

机制详见素材页 [[AgentCore Runtime (AWS Docs)]]：每会话独占 microVM（CPU/内存/文件系统隔离，结束即销毁清理）；两种计算类型（microVMs 会话最长 8 小时 / Instances 最长 14 天）；不可变版本 + 端点；支持 HTTP、[[Model Context Protocol|MCP]]、[[Agent2Agent|A2A]]；Inbound/Outbound 认证由 [[AgentCore Identity]] 支撑；长期记忆交给 [[AgentCore Memory]]。

常见叫法：AgentCore Runtime、agent 运行时、serverless agent 托管、microVM 会话隔离、Bedrock agent 运行平台。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 详细素材: [[AgentCore Runtime (AWS Docs)]]
- 认证: [[AgentCore Identity]]
- 记忆: [[AgentCore Memory]]
