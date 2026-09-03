---
type: source
tags: [aws, agentcore, runtime, microvm, session-isolation, web-source]
status: stable
summary: AWS 官方文档对 Amazon Bedrock AgentCore Runtime 的说明——serverless agent 托管，每会话独占 microVM 隔离，支持 MCP/A2A，两种计算类型。
---
# AgentCore Runtime (AWS Docs)

> 本地快照: `raw/articles/agentcore-runtime-aws-docs.md`
> 来源:
> - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html
> - https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agents-tools-runtime.html
> 抓取日期: 2026-09-02。忠实转述，不加解读。

AWS 官方开发者文档对 **Amazon Bedrock AgentCore Runtime** 的说明。

## 是什么

一个安全、serverless、专为 AI agent/工具打造的托管运行环境。托管 agent/工具代码（容器化应用），负责伸缩、会话管理、安全隔离和基础设施管理。框架无关（LangGraph/CrewAI/Strands 或自定义），模型无关（Bedrock/Claude/Gemini/OpenAI）。

## 核心组件

- **Runtime** —— 承载 agent/工具代码的容器化应用，有唯一身份、有版本。
- **Versions** —— 每个 Runtime 维护不可变版本，V1 在创建时自动生成，每次配置更新（容器镜像、协议、网络）产生新版本，支持回滚。
- **Endpoints** —— 指向特定版本的可寻址访问点，每个有唯一 ARN。`DEFAULT` 端点自动指向最新版本；可建自定义端点区分 dev/test/prod。生命周期状态：CREATING / CREATE_FAILED / READY / UPDATING / UPDATE_FAILED。可无停机更新。
- **Sessions** —— 用户与 Runtime 的交互上下文，由 `runtimeSessionId` 标识。

## 会话隔离（关键机制）

**每个 user session 跑在独占的 microVM 里**，CPU/内存/文件系统资源完全隔离。会话结束后整个 microVM 被销毁、内存被清理，防止跨会话数据污染——即便处理非确定性 AI 过程也能提供确定性安全。

会话状态：Active / Idle / Terminated。终止条件：闲置 15 分钟、达最大生命期、或被判不健康。会话状态是**易失的**，长期持久化应交给 AgentCore Memory。

## 两种计算类型

- **microVMs** —— 全托管 serverless 会话，即时启动、按需伸缩、用多少付多少；会话最长 **8 小时**。
- **Instances** —— 在自有账户的 AWS 托管 EC2 上跑，支持持久多日会话、GPU 加速、多 agent 共享实例；会话最长 **14 天**。

## 协议、认证、其他

- **协议**：HTTP、[[Model Context Protocol|MCP]]、[[Agent2Agent|A2A]] 三种。
- **认证**：Inbound（IAM SigV4 或 OAuth 2.0 验 bearer token）+ Outbound（OAuth/API key，user-delegated 或 autonomous 模式访问 Slack/Zoom/GitHub 等），由 AgentCore Identity 管理凭据。
- **异步**：后台任务、经 `/ping` 追踪状态、最长 8 小时。
- **流式**：部分结果流式返回；WebSocket 双向流。
- **消费型定价**：只按实际消耗计费，I/O 等待（等 LLM 响应）期间通常不计 CPU 费。
- 100MB payload、内置 agent 专属可观测（追踪推理步骤/工具调用/模型交互）。

## 关联
- 转述对象: [[Amazon Bedrock AgentCore]]
