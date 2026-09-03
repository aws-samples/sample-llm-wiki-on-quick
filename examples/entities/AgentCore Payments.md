---
type: entity
tags: [aws, agentcore, payments, x402, mpp]
status: developing
summary: AgentCore 服务簇的托管支付服务，让 agent 用 x402 协议和 Machine Payments Protocol 为访问付费 API/MCP/内容做微交易。
---
# AgentCore Payments

[[AgentCore 服务簇]]中负责**支付**的服务：让 agent 用 **x402 协议**和 **Machine Payments Protocol（MPP）**，为访问付费 API、MCP server 和内容做微交易支付。提供钱包集成、可配置支出额度、端到端可观测。

据 [[AgentCore 服务簇总览 (AWS Docs)]]，支持 Coinbase CDP 与 Stripe (Privy) 钱包，配合 [[AgentCore Gateway]]、[[AgentCore Identity]]，监控经 [[AgentCore Observability]]（Amazon CloudWatch）。

> 据总览页一段描述建页，x402/MPP 协议细节待专门素材充实。

常见叫法：AgentCore Payments、agent 支付、微交易、x402、Machine Payments Protocol、MPP、agent 钱包。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 依赖: [[AgentCore Gateway]]、[[AgentCore Identity]]、[[AgentCore Observability]]
