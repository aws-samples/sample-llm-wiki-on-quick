---
type: source
tags: [aws, agentcore, gateway, mcp, web-source]
status: stable
summary: AWS 官方文档对 Amazon Bedrock AgentCore Gateway 的说明——统一安全入口，把 API/Lambda/服务转成 MCP 工具，含六项关键能力。
---
# AgentCore Gateway (AWS Docs)

> 来源: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html
> 本地快照: `raw/articles/agentcore-gateway-aws-docs.md`
> 抓取日期: 2026-09-02。忠实转述，不加解读。

AWS 官方开发者文档对 **Amazon Bedrock AgentCore Gateway** 的说明。

## 是什么

一个全托管的 AI gateway，为 agentic 流量提供**单一、安全的入口**——把 agent 连到工具、其他 agent、以及 LLM。它不止是 MCP 工具网关：
- 把 API、Lambda 函数、现有服务转成 **MCP 兼容的工具**（支持 OpenAPI、Smithy、Lambda 作为工具输入类型）；
- 通过 passthrough target 代理其他 agent 和 HTTP 服务（含 A2A 流量）；
- 通过统一的、基于模型的路由端点，把推理请求路由到多个模型提供方。
- 对 Salesforce、Slack、Jira、Asana、Zendesk 等提供 1-click 集成。

## 六项关键能力

1. **Security Guard**——管理 OAuth 授权，确保只有合法用户和 agent 能访问工具与资源。
2. **Translation**——把 MCP 等协议的 agent 请求转成 API 请求和 Lambda 调用，免去自行管理协议集成/版本。
3. **Composition**——把多个 API、函数、工具、agent、模型提供方组合到单一端点后面，含跨提供方的模型路由。
4. **Secure Credential Exchange**——为每个工具注入凭据，让 agent 无缝使用认证要求各异的工具。
5. **Semantic Tool Selection**——让 agent 在可用工具间做语义搜索，从而在数千工具中选出最合适的，同时压小 prompt、降低延迟。
6. **Infrastructure Manager**——serverless、内置可观测与审计，免基础设施管理。

## 其他

同时提供入站认证（验 agent 身份）与出站认证（连工具），据文档是唯一在全托管服务里同时提供两者的方案。兼容 CrewAI、LangGraph、LlamaIndex、Strands Agents 等框架。

## 关联
- 转述对象: [[Amazon Bedrock AgentCore]]
