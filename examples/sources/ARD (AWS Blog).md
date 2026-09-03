---
type: source
tags: [aws, ard, agent-registry, discovery, federation, dns]
status: stable
summary: AWS 博客介绍 ARD（Agentic Resource Discovery）原文摘要——一个跨环境 agent 发现的开放规范，类比 DNS 做 registry 联邦，与 AWS Agent Registry 互补。
---
# ARD (AWS Blog)

> 忠实转述 `raw/articles/ard-agentic-resource-discovery.md`，不加解读。解读见 [[Agentic Resource Discovery]] 及 synthesis 页 [[Agent 发现的三个层次]]。
>
> 来源: https://aws.amazon.com/cn/blogs/machine-learning/agentic-resource-discovery-ard-an-open-specification-for-agent-discovery/
> 作者: Jeffrey Damick、Anubhav Mangal、Bhargav Talluri · 发布 2026-08-24（Amazon Bedrock AgentCore / Announcements / Intermediate 200）

## 问题背景

组织扩大 AI agent 和工具规模时，「找到对的资源」成了难点。团队建 MCP server、部署 agent、造专门工具，但没有中央目录，这些资源就各自孤立。开发者手动定位、评估、连接、维护连接。更糟的是，为一个 AI client 配好的 agent 换个 client 就不可用。少量工具时可控，但面对散落在公共 registry 和私有企业资产里、不断增长的 agent/MCP server/技能/API，就无法规模化。

## AWS Agent Registry：集中、可搜索的目录

给组织一个集中目录，编目 agent、MCP server、工具、agent 技能和自定义资源。围绕两个核心概念：

- **Registries**：你在 AWS 账户里创建的目录，有自己的授权配置和审批设置。可运行单个组织级 registry，或按资源类型/阶段/团队分设多个。借助跨账户共享，一个 registry 可服务整个 AWS Organization。
- **Registry Records**：一条记录代表一个资源，捕获描述「它是什么、做什么、如何触达」的元数据。

工作流：管理员**创建 registry**（配审批设置、用 IAM 或企业 IdP 的 JWT 设授权）→ publisher **发布记录**（把 MCP server/agent/工具描述成记录并提交审批）→ curator **策展审批**（审 pending 记录、批准/拒绝、弃用不再用的）→ consumer（人或 AI agent）**发现已批准资源**。

企业级特性：**Curation**（审批流，只有过安全/合规/质量门槛的记录才可发现，管理员可随时移除）、**Hybrid search**（语义理解 + 关键词匹配，自然语言查询和精确名查找都返回相关结果）、**MCP-native access**（registry 在一个远程 MCP 端点可用，任何 MCP 兼容 client 可直接搜索使用）、**Flexible authorization**（IAM 凭据或企业 IdP 的 JWT）。

> 注：本篇（2026-08-24）称 AWS Agent Registry「now in preview」；一周后的 GA 公告（[[AWS Agent Registry (AWS Blog)]]，2026-08-31）宣布 GA。时间线为 preview → GA。

## 多环境挑战

AWS Agent Registry 解决的是**你自己 AWS 环境内**的发现。但多数企业不在一处运营——agent 和工具跨多云、本地基础设施、SaaS 平台、企业应用部署，每个环境有自己的 registry、命名约定、元数据 schema。每个环境格式不同时，全部打通需要为「每一对需要互通的 registry」写定制连接器。共享规范改变这个等式：若每个 registry 用相同格式描述资源、通过共同协议暴露发现，则**发布一次，处处可发现**。

## ARD 是什么

Agentic Resource Discovery——一个**开放标准，不是产品、不是单个 registry**。Apache License 2.0，在 agenticresourcediscovery.org 和 GitHub 上。AWS 在规范制定中贡献了反馈。

核心类比：ARD 之于「跨 registry 联邦」，如同 **DNS 之于跨网络名称解析**。组织可跨环境部署 agent，每个环境的目录用共同协议、在一个端点后暴露这些资源；要做合并发现，任何 registry 都能凭对共享协议的理解跨这些端点索引。于是本地 registry 通过 ARD 联邦，**无需双边协议或专有连接器**。

## ARD 如何补充 AWS Agent Registry

视为 AWS Agent Registry 模型的自然补充（原文用「We expect」表述，属预期方向）：

- **不迁移即联邦**：agentic 基础设施散在多云/本地/SaaS 的组织，可用一种一致格式暴露这些资源，实现跨环境发现同时保持本地管控。
- **全局发现、本地管控**：ARD 的设计镜像 AWS 客户期待的控制模型——发布目录的组织控制里面有什么、谁能看、何时撤销。现有 AWS Agent Registry 的访问控制仍是执行点，ARD 作互操作层。
- **开放公共发现**：以 ARD 为共享协议，任何组织可在自己域名上发布目录，被任何 ARD 兼容 client 发现，为 Agent Registry 客户打开跨组织发现路径。

## 作者背景（与主题相关的一点）

三位作者中 Jeffrey Damick 与 Bhargav Talluri 都是 Amazon Route 53 / DNS 背景——这解释了 ARD 的 DNS 联邦类比不是随口比喻，而是「用成熟互联网基础设施支撑 AI agent 发现」这一思路的延续。Anubhav Mangal 负责 Amazon Bedrock AgentCore 的 agentic 资源发现与治理及 AWS Agent Registry。

## 关联
- 主概念页: [[Agentic Resource Discovery]]
