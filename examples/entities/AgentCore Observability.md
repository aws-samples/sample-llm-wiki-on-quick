---
type: entity
tags: [aws, agentcore, observability, opentelemetry, monitoring]
status: developing
summary: AgentCore 服务簇的统一可观测服务，基于 OpenTelemetry 追踪/调试/监控生产中 agent 表现，可视化工作流每一步。
---
# AgentCore Observability

[[AgentCore 服务簇]]中负责**质量与运维可见性**的服务：统一视图，追踪、调试、监控生产中的 agent 表现。可视化 agent 工作流的每一步，审计中间输出，排查性能瓶颈与失败。

基于标准 **OpenTelemetry（OTEL）** 兼容格式发射遥测，可对接任意监控栈。它是簇内的遥测汇聚点：[[AgentCore Evaluations]] 与 [[AgentCore Payments]] 的结果都并入 Observability（由 Amazon CloudWatch 支撑）。

> 据总览页一段描述建页，具体指标与仪表化细节待专门素材充实。

常见叫法：AgentCore Observability、可观测性、agent 监控、OpenTelemetry、OTEL 遥测、追踪调试、agent 可观测。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 汇入结果: [[AgentCore Evaluations]]、[[AgentCore Payments]]
