---
type: entity
tags: [aws, agentcore, platform, hosting]
status: stable
summary: AWS 的 agentic 平台，一簇 13 个可独立或组合使用的模块化服务（Runtime/Gateway/Memory/Identity 等）；是 AWS Agent Registry 组织级 auto-detection 的检测目标。
---
# Amazon Bedrock AgentCore

AWS 用于构建、部署、运营 agent 的 **agentic 平台**。它**不是单个服务，而是一簇模块化服务**——据 [[AgentCore 服务簇总览 (AWS Docs)]] 共 13 个，可独立或组合使用。完整清单与服务间咬合见枢纽页 [[AgentCore 服务簇]]。

> 早期本 vault 只从 [[AWS Agent Registry (AWS Blog)]] 了解到 Runtime 和 Gateway 两个组件，一度把 AgentCore 框定为「含两组件的托管平台」。这是不完整的——它是一整簇服务。下面保留 Runtime 与 Gateway 的机制细节（因为它们与本 vault 的 MCP/A2A 主题直接相关），其余服务见各自实体页。

## 在本素材里的角色

- **runtime 与 Gateway**——文章提到 agent 和 MCP server 跑在 **AgentCore runtime** 和 **AgentCore Gateway** 上，这两者是 [[AWS Agent Registry]] 组织级 auto-detection 的检测目标（应对 [[Shadow AI]]）。
- **未来直接部署**——路线图提到将支持从 registry 记录直接部署到 AgentCore Gateway 和 runtime。
- Agent Registry 本身发布在 Amazon Bedrock AgentCore 产品线下。

## AgentCore Gateway 的机制

据 [[AgentCore Gateway (AWS Docs)]]，Gateway 是全托管 AI gateway，为 agentic 流量提供**单一安全入口**——把 agent 连到工具、其他 agent 和 LLM：

- 把 API、Lambda、现有服务转成 **[[Model Context Protocol|MCP]] 兼容工具**（支持 OpenAPI/Smithy/Lambda 输入）；
- 通过 passthrough target 代理其他 agent 和 HTTP 服务（含 [[Agent2Agent|A2A]] 流量）；
- 通过统一的模型路由端点把推理请求分发到多个模型提供方。

六项关键能力：**Security Guard**（OAuth 授权）、**Translation**（协议转 API/Lambda 调用）、**Composition**（多源组合到单端点）、**Secure Credential Exchange**（逐工具注入凭据）、**Semantic Tool Selection**（在数千工具间语义选取、压小 prompt）、**Infrastructure Manager**（serverless + 内置可观测审计）。同时提供入站与出站认证。

## AgentCore Runtime 的机制

据 [[AgentCore Runtime (AWS Docs)]]，Runtime 是 serverless、框架无关、模型无关的 agent 托管环境，核心机制：

- **会话隔离**——每个 user session 跑在**独占的 microVM**（CPU/内存/文件系统完全隔离），会话结束后整个 microVM 销毁、内存清理，防跨会话污染。会话状态易失，长期持久化交给 AgentCore Memory。
- **两种计算类型**——microVMs（全托管 serverless，会话最长 8 小时）或 Instances（自有账户 EC2，支持持久多日会话/GPU/多 agent，最长 14 天）。
- **版本与端点**——Runtime 有不可变版本（V1 起，支持回滚），Endpoint 指向特定版本、可无停机更新、分 dev/test/prod。
- **协议**——同时支持 HTTP、[[Model Context Protocol|MCP]]、[[Agent2Agent|A2A]]。
- **认证**——Inbound（IAM/OAuth）+ Outbound（OAuth/API key，经 AgentCore Identity）。
- **消费型定价**——只按实际消耗计费，I/O 等待期通常不计 CPU 费。

常见叫法：Amazon Bedrock AgentCore、AgentCore、AgentCore runtime、AgentCore Gateway、Bedrock agent 运行平台、agent 托管运行时。

## 关联
- 服务簇枢纽: [[AgentCore 服务簇]]
- 服务簇素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 出处: [[AWS Agent Registry (AWS Blog)]]
- Gateway 机制: [[AgentCore Gateway (AWS Docs)]]
- Runtime 机制: [[AgentCore Runtime (AWS Docs)]]
- 检测方: [[AWS Agent Registry]]
- 相关问题: [[Shadow AI]]
- 承载协议: [[Model Context Protocol]]
