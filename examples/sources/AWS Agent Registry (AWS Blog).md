---
type: source
tags: [aws, agent-registry, agentcore, governance, mcp, a2a]
status: stable
summary: AWS Agent Registry GA 公告原文摘要——面向企业的 agent/工具/技能的统一治理与发现目录，含两个平面、四种记录类型、四种角色、生命周期与路线图。
---
# AWS Agent Registry (AWS Blog)

> 忠实转述 `raw/articles/aws-agent-registry.md`，不加解读。解读见 [[AWS Agent Registry]] 及相关 concept 页。
>
> 来源: https://aws.amazon.com/cn/blogs/machine-learning/manage-agents-tools-and-skills-at-scale-with-aws-agent-registry/
> 作者: Chaitra Mathur、Anubhav Mangal、Amanda Lester · 发布 2026-08-31（Amazon Bedrock AgentCore / Announcements）

## 企业为什么需要 registry

组织扩大 agentic AI 规模时出现三个问题：**没有权威清单**（各团队孤立维护，重复劳动、版本漂移、能力散乱）、**无法跨团队发现**（好工具没人找得到，默认重建已有的）、**没有治理或审计轨迹**（不知道谁能访问什么、是否过安全审查、故障如何追溯到版本和 owner）。Registry 一次解决这三点。

## 是什么

一个单一、受治理的目录，用来注册、发现、管理 AI agent、工具和能力，内置语义搜索和访问控制。内部跨两个互补的平面运作：

- **Governance Plane（治理平面）**——已注册资源的权威存储，不论生命周期状态。管理员在这里配置规则：合规与安全信号、发现策略（基于权限的搜索规则）、自定义元数据 schema（如 cost center、数据分级、SLA tier）。
- **Discovery Plane（发现平面）**——消费者日常交互的界面，只呈现通过审批的资源。特点：只收录已批准的（草稿/拒绝/影子资源不可见）、为规模而建（高吞吐查询）、语义 + 词法搜索、呈现信任信号而非原始治理数据。

## 可以编目什么（四种记录类型）

- **MCP**——Model Context Protocol server，及其工具、资源、prompts。
- **Agent**——Agent2Agent（A2A）agent card，定义 agent 及其技能。
- **Skill**——markdown 文件里的 agent 技能定义及关联代码/包。
- **Custom**——自定义描述符，必须是合法 JSON。

## 客户与合作伙伴

Sony（跨业务单元复用 agent 模式）、Mitsubishi Electric、Southwest Airlines（7 万+ 员工，从散落的数十个 agent 到单一受治理目录）、PepsiCo、Syngenta、Amdocs（集成进 aOS Cognitive Core）等客户；PwC Australia、Caylent、Slalom 等合作伙伴；Informatica（MCP server 上架）、Check Point（安全态势评估）等 ISV 集成。原文引用了多位高管背书（缓解 agent sprawl、单一事实来源等）。

## 四种角色

- **Admins**——搭建 registry、配置护栏、建立发现与治理流程。
- **Publishers**——构建 agent/工具/技能并开放发现（可为非技术人员）。
- **Consumers**——发现并使用已批准能力（开发者、业务用户或自主 agent）。
- **Curators**——人在环审阅者，按内部需求批准/拒绝资源、决定生命周期。

## 管理员与 curator 工作流

管理员可跨企业建单个或多个 registry 实例，按业务单元/环境/合规边界划分；每个实例有自己的访问策略、审批流、生命周期规则，可独立配置 OAuth 或 IAM 认证。审批流程（7 步）：CRUD Registry → 创建审批工作流 → 发布记录 → 记录进入 pending 后经 Amazon EventBridge 触发事件 → 审批工作流（安全扫描、去重等检查）→ 批准并发布到 discovery plane → 消费者发现。AWS CloudTrail 记录全部操作审计。

## 组织级 auto-detection

针对 Shadow AI：管理员在 AWS Organization 级启用一次端点检测，Registry 自动检测跨所有账户在 AgentCore runtime 和 AgentCore Gateway 上运行的 agent 和 MCP server，汇入集中的「Detected Endpoints」视图，作为 draft 记录走标准治理生命周期。新 agent 部署到已连接账户时自动出现，无需发布团队操作，避免影子 agent。

## Publishing

支持 Console、CLI、API 发布 MCP Server / A2A Agent / Skill / 自定义元数据；可集成进 CI/CD 流水线避免每次发版手动改。记录经历生命周期状态（draft → pending approval → approved / rejected / deprecated）。也能用同步功能从外部 MCP 或 A2A server 拉元数据（OAuth / IAM / 无认证）。

## Discovery and usage

消费者通过 Search API 做语义搜索，覆盖全目录；Search API 也暴露为 MCP server，供自动化流水线和 agentic 工作流程序化查找。认证按实例配置 OAuth 或 IAM。锁定网络环境用 AWS PrivateLink。消费流程：搜索 → 收到 auth 信息与 URI → 请求访问 → 获取凭据 → 用凭据调用。

## Discovery from IDEs

Registry 把每个实例暴露为 MCP server，MCP 兼容 IDE（含 Kiro 和 Claude Code）可原生连接。开发者在 IDE 里输入自然语言（「find me an MCP server for problem tickets」）即可查询、返回匹配工具及连接细节、有权限就直接用。连接用 Dynamic Client Registration（DCR）在运行时建立信任，无需管理员预置 OAuth 凭据；开发者经组织 IdP（如 AWS IAM Identity Center）认证一次得到受限 token。

## Discovery from Amazon Quick

Quick 管理员把租户连接到一个或多个 Agent Registry 后，所有已批准的 agent、MCP server、技能出现在 Quick 的 Integrations 页。企业版用户可浏览搜索全目录、看工具描述、为租户启用特定 agent、分享给团队。终端用户通过 Quick Chat、Automations、Flows、Deep Research 访问。

## State transitions（记录生命周期）

Publisher 创建/更新记录 → DRAFT；提交审批 → PENDING_APPROVAL；Approver 批准 → APPROVED，拒绝 → REJECTED（auto_approve 为 true 时自动 APPROVED）；pending 或 approved 状态下 Publisher 更新会退回 DRAFT；Curator 弃用 → DEPRECATED。

## 企业考量

- **单个 vs 多个 registry**——单个可见性最广；有 dev/staging/prod 隔离或数据驻留需求则镜像边界用多实例。权衡：合规强制物理隔离用多实例；每多一个实例都是额外维护负担；单个大 registry 缺元数据会变噪杂；不同团队用不同授权模型（一个 OAuth 一个 IAM）必须多实例。经验法则：从满足隔离需求的最少实例起步。
- **治理工作流**——Registry 不自带审批流，只提供 hook。最低要求：发布前查重、对工具/agent/技能跑安全扫描、人工审批签字。CI/CD checklist 或基于 Slack 的审批流起步足够。
- **安全**——能发现工具的人不一定该能注册新工具；工具元数据可能含内部端点或架构细节；审计谁在查询、多频繁。

## What's next（路线图四主题）

1. **治理、安全、合规**——Registry 主动参与治理：呈现安全与漏洞评估、合规评估、去重分析；资源版本化与审计轨迹；对 agent 调用做集中策略执行。
2. **丰富清单与元数据**——自动检测部署在 AgentCore、Amazon Quick 及 EC2 / EKS / ECS 上的资源；计划联邦扩展到非 AWS/本地/SaaS；自定义 schema 强化元数据丰富度。
3. **搜索、发现、可观测**——策略驱动的可见性（控制哪些身份看到哪些记录）；扩展可发现资产（prompts、models、knowledge bases）；per-agent/tool 可观测指标 + 依赖图做影响分析；跨组织发现。
4. **在客户所在处相遇**——从任意界面访问（agentic IDE、生产力系统、IaC 流水线）；从 registry 记录直接部署到 AgentCore Gateway 和 runtime；独立 web 应用（OAuth/SSO，无需 AWS Console）；公共 registry 作为对外能力橱窗。

## 可用性与定价（原文结尾）

GA 区域：US East (N. Virginia)、US West (Oregon)、Europe (Ireland)、Asia Pacific (Tokyo)、Asia Pacific (Sydney)。消费型定价，含 AWS Free Tier。资源：agentcore-samples repo、AWS Agent Registry Developer Guide。

## 关联
- 主实体页: [[AWS Agent Registry]]
