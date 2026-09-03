---
type: source
tags: [aws, agentcore, overview, web-source]
status: stable
summary: AWS 官方总览页对 Amazon Bedrock AgentCore 的说明——一个 agentic 平台，含 13 个可独立或组合使用的模块化服务。
---
# AgentCore 服务簇总览 (AWS Docs)

> 本地快照: `raw/articles/agentcore-overview-aws-docs.md`
> 来源: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html
> 抓取日期: 2026-09-02。忠实转述，不加解读。

AWS 官方总览页对 **Amazon Bedrock AgentCore** 的说明。

## 是什么

一个用于构建、部署、运营 agent 的 agentic 平台，框架无关、模型无关。各服务**可组合使用，也可独立使用**，与 CrewAI/LangGraph/LlamaIndex/Strands 等开源框架及任意基础模型协作。

## 13 个模块化服务（官方逐条描述）

- **Harness**——托管的 agent loop，单次 API 调用即可定义并调用 agent（内联指定模型、system prompt、工具）。负责编排、工具执行、记忆管理、响应生成。每会话跑在隔离 microVM（有文件系统与 shell 访问）。可自带容器镜像。
- **Runtime**——安全、serverless 的运行时，部署和伸缩 agent 与工具。快速冷启动、会话隔离、内置身份、支持多模态与多 agent。支持 MCP、A2A。
- **Memory**——构建上下文感知 agent，完全控制 agent 记住/学到什么。支持短期记忆（多轮对话）与长期记忆（跨会话持久），记忆库可跨 agent 共享、可从经验学习。
- **Gateway**——把 API、Lambda、现有服务转成 MCP 兼容工具，也可连已有 MCP server，几行代码经 Gateway 端点提供给 agent。
- **Identity**——安全可扩展的 agent 身份、访问与认证管理服务，兼容现有 IdP（Cognito/Okta/Entra ID/Auth0），无需用户迁移或重建认证流。
- **Code Interpreter**——隔离沙箱环境，供 agent 执行代码，提升准确性、扩展解决复杂端到端任务的能力。支持 Python/JavaScript/TypeScript。
- **Browser**——快速安全的云端浏览器运行时，让 agent 与 web 应用交互、填表、导航、抽取信息。兼容 Playwright、BrowserUse 等。
- **Observability**——统一视图，追踪/调试/监控生产中 agent 表现。可视化 agent 工作流每一步，审计中间输出、排查瓶颈与失败。基于 OpenTelemetry（OTEL）。
- **Payments**——托管服务，让 agent 用 x402 协议和 Machine Payments Protocol（MPP）为访问付费 API/MCP server/内容做微交易支付。含钱包集成、可配额度、端到端可观测。支持 Coinbase CDP、Stripe (Privy)。
- **Evaluations**——专用评估服务，自动、一致、数据驱动地评估 agent。度量 agent/工具执行任务、处理边缘情况、维持输出可靠性的表现。结果并入 Observability。
- **Optimization**——持续改进服务，用 AI 生成的建议、版本化配置包、A/B 测试来改进 agent 表现。基于 Evaluations，经 Gateway 做流量切分做 A/B。
- **Policy**——确定性控制，用自然语言或 Cedar（AWS 开源策略语言）编写细粒度规则，让 agent 在定义好的边界与业务规则内运作。经 Gateway 拦截每次工具调用。
- **Registry**——集中目录，发现和管理组织内的 agent、MCP server、工具、技能、自定义资源。含发布/审查/批准的受治理工作流，混合语义 + 关键词搜索。

## 关联
- 转述对象: [[AgentCore 服务簇]]
