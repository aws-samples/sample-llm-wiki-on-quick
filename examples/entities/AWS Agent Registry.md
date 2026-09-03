---
type: entity
tags: [aws, agent-registry, agentcore, governance, discovery]
status: developing
summary: AWS 的企业级 agent/工具/技能统一治理与发现目录，内置语义搜索、访问控制和审批生命周期；2026-08-31 GA。
---
# AWS Agent Registry

AWS 推出的**单一、受治理、可搜索的目录**，用于在企业范围注册、发现、管理 AI agent、工具、技能和自定义资源。2026-08-31 GA。它解决组织扩大 agent 规模时的三个痛点：没有权威清单、无法跨团队发现、没有治理/审计轨迹。

## 两个核心概念

据 [[ARD (AWS Blog)]]，Registry 围绕两个核心概念构建：

- **Registries（注册表）**：你在 AWS 账户里创建的目录，有自己的授权配置和审批设置。可运行单个组织级 registry，或按资源类型/阶段/团队分设多个；借助跨账户共享，一个 registry 可服务整个 AWS Organization。
- **Registry Records（记录）**：一条记录代表一个资源，捕获描述「它是什么、做什么、如何触达」的元数据。记录类型见[[四种记录类型]]。

## 两个平面

内部跨 [[两个平面]]运作——Governance Plane（管理员的权威存储与策略控制）和 Discovery Plane（消费者的高性能、只读已批准资源的搜索界面）。两者干净地分离关注点。

## 能编目什么

支持[[四种记录类型]]：MCP server、Agent（A2A agent card）、Skill、Custom（合法 JSON）。

## 谁来用

围绕[[四种角色]]设计：Admins、Publishers、Consumers、Curators。记录走一套[[记录生命周期]]（DRAFT → PENDING_APPROVAL → APPROVED/REJECTED → DEPRECATED）。

## 怎么发现

消费者用 Search API 做**语义 + 词法混合搜索**（hybrid search，自然语言查询和精确名查找都返回相关结果）；Search API 也暴露为 [[Model Context Protocol]] server（**MCP-native access**：registry 在一个远程 MCP 端点可用，任何 MCP 兼容 client 可直接搜索使用）。MCP 兼容 IDE（Kiro、Claude Code）可原生连接，用 Dynamic Client Registration（DCR）在运行时建立信任。业务用户可从 [[Amazon Quick]] 的 Integrations 页发现并启用。授权灵活：IAM 凭据或企业 IdP 的 JWT。

## 跨环境发现（ARD）

AWS Agent Registry 本身只解决**单个 AWS 环境内**的发现。要跨多云/本地/SaaS 联邦，AWS 提出并贡献了开放规范 [[Agentic Resource Discovery]]（ARD）：registry 作**执行点**（访问控制留本地），ARD 作**互操作层**。三种「发现」的作用域对比见 [[Agent 发现的三个层次]]。

## 治理与 Shadow AI

不自带审批流，只提供 hook（查重、安全扫描、人工签字，可用 CI/CD checklist 或 Slack 审批起步）。通过组织级 auto-detection 应对 [[Shadow AI]]：自动检测跨账户在 [[Amazon Bedrock AgentCore]] 的 runtime 和 Gateway 上运行的 agent 与 MCP server。审计由 AWS CloudTrail 记录。

## 部署形态

可跨企业建单个或多个 registry 实例（按业务单元/环境/合规边界），每个实例独立配置 OAuth 或 IAM 认证。GA 区域：US East (N. Virginia)、US West (Oregon)、Europe (Ireland)、Asia Pacific (Tokyo/Sydney)。

> **状态时间线**：[[ARD (AWS Blog)]]（2026-08-24）称本服务「now in preview」；一周后的 GA 公告 [[AWS Agent Registry (AWS Blog)]]（2026-08-31）宣布 GA。即 preview（08-24）→ GA（08-31），非矛盾。

## 定价

消费型定价、无预付，计费按**存储记录数** + **Search/List/Get API 调用数**两个维度（据 [[AWS Agent Registry 定价与区域 (Unite.AI)]]）：

- **Free Tier（每月）**：前 5,000 条记录、前 1,000,000 次 Search 调用、前 2,000,000 次 Get+List 合计调用。
- **超出**：记录 $0.40/1,000 条；Search $0.020/1,000 次；List 与 Get $0.004/1,000 次。

常见叫法：AWS Agent Registry、Agent Registry、AWS agent 注册表、agent 目录、agent/工具/技能治理目录、agentic 资源注册中心。

## 关联
- 原文摘要: [[AWS Agent Registry (AWS Blog)]]
- 两个核心概念出处: [[ARD (AWS Blog)]]
- 定价与区域: [[AWS Agent Registry 定价与区域 (Unite.AI)]]
- 两个平面: [[两个平面]]
- 记录类型: [[四种记录类型]]
- 角色: [[四种角色]]
- 生命周期: [[记录生命周期]]
- 跨环境联邦: [[Agentic Resource Discovery]]
- 发现层次对比: [[Agent 发现的三个层次]]
- 影子问题: [[Shadow AI]]
- 运行/检测平台: [[Amazon Bedrock AgentCore]]
- 发现界面: [[Amazon Quick]]
- 核心协议: [[Model Context Protocol]]、[[Agent2Agent]]
