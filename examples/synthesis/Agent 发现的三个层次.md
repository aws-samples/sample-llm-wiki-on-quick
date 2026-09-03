---
type: synthesis
tags: [discovery, ard, agent-registry, agent-card, comparison]
status: developing
summary: 本 vault 里三种「agent/资源发现」机制按作用域递进——Agent Card（单 agent）、AWS Agent Registry（单环境目录）、ARD（跨环境联邦），层层嵌套互补。
---
# Agent 发现的三个层次

一处跨页综合：vault 里出现了三种「发现」机制，作用域层层放大、互相嵌套。本页把它们放在一起对比。来源：[[Agent Card]]（A2A 规范）、[[AWS Agent Registry (AWS Blog)]]、[[ARD (AWS Blog)]]。

## 三个层次（作用域递进）

| 层次 | 机制 | 发现什么 | 作用域 | 类比 |
|---|---|---|---|---|
| 1. 单 agent | [[Agent Card]] | 一个 A2A server 的身份/能力/端点 | 点对点：已知对方就能取卡 | 一张名片 |
| 2. 单环境目录 | [[AWS Agent Registry]] | 一个组织 AWS 环境内已批准的 agent/工具/技能 | 一个 registry 内部 | 一本企业通讯录 |
| 3. 跨环境联邦 | [[Agentic Resource Discovery]]（ARD） | 跨多云/本地/SaaS 各环境目录里的资源 | 跨 registry 联邦 | DNS |

## 它们怎么嵌套

- **Agent Card ⊂ Registry**：[[Agent Card]] 的发现机制之一就是「Registries/Catalogs」——即把卡登记进 [[AWS Agent Registry]]（作为 [[四种记录类型|Agent 记录]]）。所以单 agent 的名片可以被单环境目录收录。
- **Registry ⊂ ARD**：[[AWS Agent Registry]] 只解决单环境发现；[[Agentic Resource Discovery|ARD]] 让多个环境的 registry 联邦互通。Registry 是执行点（访问控制留本地），ARD 是互操作层。

一句话：**名片进目录，目录进联邦。** 三层不是竞争关系，而是同一件事（「让 agent 找到彼此/资源」）在三个作用域上的递进——从一个 agent，到一个组织的一个环境，到跨组织跨环境。

## 一个统一线索：都靠「共享格式 + 共同协议」

三层的共性是「用一个各方都懂的描述格式 + 一个共同查询协议」消除定制对接：Agent Card 用统一 JSON schema + well-known URI；Registry 用统一记录格式 + [[Model Context Protocol|MCP]]-native 端点；ARD 用共享规范 + 共同协议做联邦。层层放大的都是同一招。

## 关联
- 层次一: [[Agent Card]]
- 层次二: [[AWS Agent Registry]]
- 层次三: [[Agentic Resource Discovery]]
- 记录类型: [[四种记录类型]]
- 共同协议: [[Model Context Protocol]]
- 来源: [[ARD (AWS Blog)]]
