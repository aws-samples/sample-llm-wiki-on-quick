---
type: entity
tags: [aws, agentcore, gateway, mcp, tools]
status: developing
summary: AgentCore 服务簇的统一安全入口，把 API/Lambda/服务转成 MCP 兼容工具，也连已有 MCP server。
---
# AgentCore Gateway

[[AgentCore 服务簇]]中负责**工具连接**的服务：把 API、Lambda 函数、现有服务转成 [[Model Context Protocol|MCP]] 兼容工具，也可连已有 MCP server，几行代码经 Gateway 端点提供给 agent。

机制详见素材页 [[AgentCore Gateway (AWS Docs)]]：六项关键能力（Security Guard、Translation、Composition、Secure Credential Exchange、Semantic Tool Selection、Infrastructure Manager）；同时提供入站与出站认证；支持 passthrough 代理其他 agent（含 [[Agent2Agent|A2A]] 流量）。它也是 [[AgentCore Policy]] 拦截工具调用、[[AgentCore Optimization]] 做 A/B 流量切分的落点。

常见叫法：AgentCore Gateway、agent 工具网关、MCP 工具入口、统一 agentic 入口。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 详细素材: [[AgentCore Gateway (AWS Docs)]]
- 承载协议: [[Model Context Protocol]]、[[Agent2Agent]]
