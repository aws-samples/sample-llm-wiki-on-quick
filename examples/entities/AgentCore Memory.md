---
type: entity
tags: [aws, agentcore, memory, context, state]
status: developing
summary: AgentCore 服务簇的记忆服务，支持短期（多轮对话）与长期（跨会话持久）记忆，记忆库可跨 agent 共享、可从经验学习。
---
# AgentCore Memory

[[AgentCore 服务簇]]中负责**状态与记忆**的服务：构建上下文感知 agent，让你完全控制 agent 记住/学到什么。

- **短期记忆**——多轮对话内的上下文。
- **长期记忆**——跨会话持久保存。
- 记忆库可**跨 agent 共享**，并能从经验中学习。

它承接了 [[AgentCore Runtime]] 的短板：Runtime 会话状态是易失的（microVM 结束即清理），需要跨会话持久时交给 Memory。据 [[AgentCore 服务簇总览 (AWS Docs)]]，Memory 与 LangGraph/LangChain/Strands/LlamaIndex 协作。

> 据总览页一段描述建页，具体 API 与存储模型待专门素材充实。

常见叫法：AgentCore Memory、agent 记忆、短期记忆、长期记忆、跨会话记忆、上下文感知、记忆库。

## 关联
- 所属簇: [[AgentCore 服务簇]]
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 补易失状态: [[AgentCore Runtime]]
