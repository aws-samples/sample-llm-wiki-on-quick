---
type: entity
tags: [aws, agentcore, runtime, gateway, hosting]
status: stub
summary: AWS 运行和管理 agent 的平台；含 AgentCore runtime 和 AgentCore Gateway，是 AWS Agent Registry 组织级 auto-detection 的检测目标。
---
# Amazon Bedrock AgentCore

AWS 用于运行和管理 agent 的平台。本 vault 目前只从 [[AWS Agent Registry (AWS Blog)]] 一处素材了解到它，信息有限。

## 在本素材里的角色

- **runtime 与 Gateway**——文章提到 agent 和 MCP server 跑在 **AgentCore runtime** 和 **AgentCore Gateway** 上，这两者是 [[AWS Agent Registry]] 组织级 auto-detection 的检测目标（应对 [[Shadow AI]]）。
- **未来直接部署**——路线图提到将支持从 registry 记录直接部署到 AgentCore Gateway 和 runtime。
- Agent Registry 本身发布在 Amazon Bedrock AgentCore 产品线下。

> `status: stub`：AgentCore runtime / Gateway 的机制待专门素材再充实，届时可能各自单开页面。

常见叫法：Amazon Bedrock AgentCore、AgentCore、AgentCore runtime、AgentCore Gateway、Bedrock agent 运行平台、agent 托管运行时。

## 关联
- 出处: [[AWS Agent Registry (AWS Blog)]]
- 检测方: [[AWS Agent Registry]]
- 相关问题: [[Shadow AI]]
- 承载协议: [[Model Context Protocol]]
