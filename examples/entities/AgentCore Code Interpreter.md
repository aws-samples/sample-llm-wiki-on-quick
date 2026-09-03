---
type: entity
tags: [aws, agentcore, code-interpreter, sandbox, tools]
status: developing
summary: AgentCore 服务簇的隔离代码执行沙箱，供 agent 执行 Python/JavaScript/TypeScript，提升准确性、扩展解决复杂任务的能力。
---
# AgentCore Code Interpreter

[[AgentCore 服务簇]]中的**内置工具**之一：一个隔离的沙箱环境，供 agent 执行代码，提升准确性、扩展其解决复杂端到端任务的能力（如生成可视化）。支持 Python、JavaScript、TypeScript 多语言。

它是 agent 可用的两个内置工具之一（另一个是 [[AgentCore Browser]]），可经 [[AgentCore Harness]] 或 [[AgentCore Gateway]] 提供给 agent。

> 据总览页一段描述建页，沙箱隔离模型（如 Firecracker microVM）待专门素材充实。

常见叫法：AgentCore Code Interpreter、代码解释器、代码沙箱、code interpreter、隔离代码执行、agent 执行代码。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 姊妹工具: [[AgentCore Browser]]
