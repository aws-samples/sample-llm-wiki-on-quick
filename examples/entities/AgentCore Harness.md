---
type: entity
tags: [aws, agentcore, harness, agent-loop, orchestration]
status: developing
summary: AgentCore 服务簇的托管 agent loop，单次 API 调用即可定义并运行 agent，内联指定模型/prompt/工具，负责编排、工具执行、记忆管理、响应生成。
---
# AgentCore Harness

[[AgentCore 服务簇]]中的**托管 agent loop**：单次 API 调用即可定义并调用 agent——内联指定模型、system prompt 和工具。Harness 负责编排、工具执行、记忆管理和响应生成。

每会话跑在隔离的 microVM（有文件系统与 shell 访问），支持代码生成、数据分析、深度研究等场景；可自带容器镜像用于自定义环境。据 [[AgentCore 服务簇总览 (AWS Docs)]]，与 Amazon Bedrock/OpenAI/Gemini 及任意 OpenAI 兼容模型协作，集成 [[AgentCore Memory]]、[[AgentCore Gateway]]、[[AgentCore Browser]]、[[AgentCore Code Interpreter]]、[[AgentCore Observability]]，支持远程 MCP server 与内联函数。

> 据总览页一段描述建页，与 Runtime 的分工细节待专门素材充实。

常见叫法：AgentCore Harness、托管 agent loop、agent 循环、单次调用 agent、编排 harness。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 集成: [[AgentCore Memory]]、[[AgentCore Gateway]]、[[AgentCore Browser]]、[[AgentCore Code Interpreter]]、[[AgentCore Observability]]
