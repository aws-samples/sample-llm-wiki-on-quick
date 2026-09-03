---
type: concept
tags: [ard, discovery, federation, open-standard, dns, agent-registry]
status: developing
summary: 一个跨环境 agent 发现的开放规范（Apache 2.0），类比 DNS 让各环境的 registry 联邦互通——发布一次、处处可发现，与 AWS Agent Registry 互补。
---
# Agentic Resource Discovery

一个**开放标准**（简称 ARD），用于跨环境的 agentic 资源发现——让部署在不同云、本地、SaaS 里的 agent、[[Model Context Protocol|MCP]] server、工具、技能能被统一发现。Apache License 2.0，在 agenticresourcediscovery.org 和 GitHub 上。**它不是产品、不是某个 registry**；AWS 在其制定中贡献了反馈。本 vault 从 [[ARD (AWS Blog)]] 了解它。

## 它解决什么

单个目录（如 [[AWS Agent Registry]]）只解决**自己环境内**的发现。企业实际跨多云/本地/SaaS，各环境有自己的 registry、命名约定、元数据 schema。两两打通要为每一对 registry 写定制连接器。ARD 用一个共享规范改变这点：每个 registry 用相同格式描述资源、通过共同协议暴露发现，于是**发布一次，处处可发现**。

## DNS 联邦类比

ARD 之于「跨 registry 联邦」，如同 **DNS 之于跨网络名称解析**。每个环境的目录用共同协议在一个端点后暴露资源；任何 registry 都能凭对共享协议的理解跨这些端点索引，做合并发现。于是本地 registry 通过 ARD 联邦，**无需双边协议或专有连接器**。（提出者多为 Amazon Route 53 / DNS 背景，这个类比是其「用互联网基础设施支撑 agent 发现」思路的延续。）

## 与 AWS Agent Registry 的关系

**互补，非替代**：ARD 是**互操作层**，[[AWS Agent Registry]] 仍是**执行点**（访问控制留在本地）。三个预期方向：不迁移即联邦、全局发现本地管控、开放公共发现。与本 vault 里其他两种「发现」的层次对比见 [[Agent 发现的三个层次]]。

常见叫法：Agentic Resource Discovery、ARD、agent 发现开放规范、跨环境发现、registry 联邦、agenticresourcediscovery.org、agent 发现的 DNS。

## 关联
- 原文: [[ARD (AWS Blog)]]
- 互补的执行点: [[AWS Agent Registry]]
- 发现层次对比: [[Agent 发现的三个层次]]
- 被发现的资源: [[Model Context Protocol]]、[[Agent2Agent]]
