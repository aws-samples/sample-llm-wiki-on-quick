---
type: entity
tags: [aws, agent-registry, agentcore, governance, discovery]
status: developing
summary: AWS 的企业级 agent/工具/技能统一治理与发现目录，内置语义搜索、访问控制和审批生命周期；2026-08-31 GA。
---
# AWS Agent Registry

AWS 推出的**单一、受治理、可搜索的目录**，用于在企业范围注册、发现、管理 AI agent、工具、技能和自定义资源。2026-08-31 GA。它解决组织扩大 agent 规模时的三个痛点：没有权威清单、无法跨团队发现、没有治理/审计轨迹。

## 两个平面

内部跨 [[两个平面]]运作——Governance Plane（管理员的权威存储与策略控制）和 Discovery Plane（消费者的高性能、只读已批准资源的搜索界面）。两者干净地分离关注点。

## 能编目什么

支持[[四种记录类型]]：MCP server、Agent（A2A agent card）、Skill、Custom（合法 JSON）。

## 谁来用

围绕[[四种角色]]设计：Admins、Publishers、Consumers、Curators。记录走一套[[记录生命周期]]（DRAFT → PENDING_APPROVAL → APPROVED/REJECTED → DEPRECATED）。

## 怎么发现

消费者用 Search API 做语义 + 词法搜索；Search API 也暴露为 [[Model Context Protocol]] server 供程序化调用。MCP 兼容 IDE（Kiro、Claude Code）可原生连接，用 Dynamic Client Registration（DCR）在运行时建立信任。业务用户可从 [[Amazon Quick]] 的 Integrations 页发现并启用。

## 治理与 Shadow AI

不自带审批流，只提供 hook（查重、安全扫描、人工签字，可用 CI/CD checklist 或 Slack 审批起步）。通过组织级 auto-detection 应对 [[Shadow AI]]：自动检测跨账户在 [[Amazon Bedrock AgentCore]] 的 runtime 和 Gateway 上运行的 agent 与 MCP server。审计由 AWS CloudTrail 记录。

## 部署形态

可跨企业建单个或多个 registry 实例（按业务单元/环境/合规边界），每个实例独立配置 OAuth 或 IAM 认证。GA 区域：US East (N. Virginia)、US West (Oregon)、Europe (Ireland)、Asia Pacific (Tokyo/Sydney)。消费型定价含 Free Tier。

常见叫法：AWS Agent Registry、Agent Registry、AWS agent 注册表、agent 目录、agent/工具/技能治理目录、agentic 资源注册中心。

## 关联
- 原文摘要: [[AWS Agent Registry (AWS Blog)]]
- 两个平面: [[两个平面]]
- 记录类型: [[四种记录类型]]
- 角色: [[四种角色]]
- 生命周期: [[记录生命周期]]
- 影子问题: [[Shadow AI]]
- 运行/检测平台: [[Amazon Bedrock AgentCore]]
- 发现界面: [[Amazon Quick]]
- 核心协议: [[Model Context Protocol]]、[[Agent2Agent]]
