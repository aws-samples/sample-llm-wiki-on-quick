---
type: entity
tags: [aws, agentcore, evaluations, quality, assessment]
status: developing
summary: AgentCore 服务簇的评估服务，自动、一致、数据驱动地度量 agent 执行任务、处理边缘情况、维持输出可靠性的表现。
---
# AgentCore Evaluations

[[AgentCore 服务簇]]中负责**质量评估**的服务：自动、一致、数据驱动地评估 agent 与工具——度量它们执行任务、处理边缘情况、跨多样输入维持输出可靠性的表现。提供可度量的质量信号，帮团队据结构化洞见优化，确保 agent 在部署前后达到功能与行为标准。

据 [[AgentCore 服务簇总览 (AWS Docs)]]，支持对 Strands/LangGraph 生成、经 OpenTelemetry 或 OpenInference 仪表化的 session/trace/span 做评估，结果并入 [[AgentCore Observability]]。它是 [[AgentCore Optimization]] 的基础。

> 据总览页一段描述建页，评估指标体系待专门素材充实。

常见叫法：AgentCore Evaluations、agent 评估、质量评估、eval、agent 打分、输出可靠性评估。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 结果汇入: [[AgentCore Observability]]
- 被依赖: [[AgentCore Optimization]]
