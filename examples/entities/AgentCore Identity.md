---
type: entity
tags: [aws, agentcore, identity, auth, oauth]
status: developing
summary: AgentCore 服务簇的 agent 身份、访问与认证管理服务，兼容现有 IdP，无需用户迁移或重建认证流。
---
# AgentCore Identity

[[AgentCore 服务簇]]中负责**身份与认证**的服务：安全、可扩展的 agent 身份、访问与认证管理，兼容现有身份提供方（Cognito、Okta、Microsoft Entra ID、Auth0 等），无需用户迁移或重建认证流。

它支撑 [[AgentCore Runtime]] 的 Inbound 认证（验 agent/用户身份）与 Outbound 认证（agent 安全访问 Slack/Zoom/GitHub 等第三方，user-delegated 或 autonomous 模式）。

> 据总览页一段描述建页，具体凭据模型与 API 待专门素材充实。

常见叫法：AgentCore Identity、agent 身份、认证管理、access management、OAuth 凭据、IdP 集成、agent 身份服务。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 支撑运行时认证: [[AgentCore Runtime]]
