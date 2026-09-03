---
type: entity
tags: [aws, agentcore, policy, cedar, guardrails]
status: developing
summary: AgentCore 服务簇的确定性控制服务，用自然语言或 Cedar 编写细粒度规则，让 agent 在定义好的边界与业务规则内运作。
---
# AgentCore Policy

[[AgentCore 服务簇]]中负责**边界控制**的服务：提供确定性控制，让 agent 在定义好的边界与业务规则内运作而不拖慢速度。可用自然语言或 **Cedar**（AWS 开源策略语言）编写细粒度规则。

据 [[AgentCore 服务簇总览 (AWS Docs)]]，它与 [[AgentCore Gateway]] 集成，**拦截每次工具调用**（在执行前）——你可定义 agent 能访问哪些工具、能执行什么动作、在什么条件下。

> 据总览页一段描述建页，Cedar 规则模型细节待专门素材充实。

常见叫法：AgentCore Policy、策略控制、guardrails、Cedar、工具调用拦截、agent 边界、确定性控制。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 拦截点: [[AgentCore Gateway]]
