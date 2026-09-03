---
type: source
tags: [aws, agent-registry, pricing, web-source]
status: stable
summary: Unite.AI 对 AWS Agent Registry GA 的报道，含具体消费型定价数字与 Free Tier 阈值、GA 区域。
---
# AWS Agent Registry 定价与区域 (Unite.AI)

> 来源: https://www.unite.ai/aws-agent-registry-reaches-general-availability/
> 本地快照: `raw/articles/aws-agent-registry-pricing-uniteai.md`
> 抓取日期: 2026-09-02。忠实转述，不加解读。

Unite.AI 对 AWS Agent Registry 2026-08-31 GA 的报道。本页只摘录本 vault 已有页面未覆盖的**定价与区域**细节，其余（两平面、四记录类型、生命周期、auto-detection）已在既有页转述，不重复。

## 定价（消费型，无预付）

计费基于两个维度：**存储的记录数** + 对记录发起的 **Search / List / Get API 调用数**。

**Free Tier（每月）**：
- 前 5,000 条记录
- 前 1,000,000 次 Search API 调用
- 前 2,000,000 次 Get + List 合计调用

**超出部分**：
- 记录：$0.40 / 1,000 条
- Search API：$0.020 / 1,000 次调用
- List 与 Get：$0.004 / 1,000 次调用

## GA 区域

US East (N. Virginia)、US West (Oregon)、Europe (Ireland)、Asia Pacific (Tokyo)、Asia Pacific (Sydney)。

## 时间线

Preview 2026-04-09 发布；GA 2026-08-31。

## 客户与合作方（报道提及）

Southwest Airlines、Syngenta 给出具名背书；Sony、Mitsubishi Electric、PepsiCo、Amdocs 为用户或早期采用者；合作方 Informatica（列出并发现其托管 MCP server）、Check Point（持续发现与安全态势评估）。

## 关联
- 转述对象: [[AWS Agent Registry]]
