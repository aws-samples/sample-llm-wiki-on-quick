---
type: entity
tags: [aws, agentcore, optimization, ab-testing, improvement]
status: developing
summary: AgentCore 服务簇的持续改进服务，用 AI 生成建议、版本化配置包、A/B 测试来据数据改进 agent 表现。
---
# AgentCore Optimization

[[AgentCore 服务簇]]中负责**持续改进**的服务：用 AI 生成的建议、版本化配置包、A/B 测试来改进 agent 表现。不靠人工猜测，而是指向 agent trace 生成改进项，再用受控实验验证。

据 [[AgentCore 服务簇总览 (AWS Docs)]]，它构建在 [[AgentCore Evaluations]] 之上，作用于经 [[AgentCore Observability]] 用 OpenTelemetry 仪表化的 agent；支持 system prompt 与工具描述的优化，经 [[AgentCore Gateway]] 做流量切分实现 A/B 测试。

> 据总览页一段描述建页，优化算法与配置模型待专门素材充实。

常见叫法：AgentCore Optimization、agent 优化、持续改进、A/B 测试、prompt 优化、配置调优。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 基于: [[AgentCore Evaluations]]
- A/B 落点: [[AgentCore Gateway]]
