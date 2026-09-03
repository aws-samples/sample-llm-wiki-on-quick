---
type: concept
tags: [llm-wiki, knowledge-base, pattern]
status: developing
summary: 用 LLM 增量维护一个持久、互链的 markdown wiki，把知识编译一次并持续保鲜，替代每次查询重新检索的 RAG。
---
# LLM Wiki

一种用 LLM 构建个人知识库的模式：LLM 不在查询时从原始文档临时检索，而是**增量构建并维护一个持久的、互链的 markdown wiki**，坐落在人和原始素材之间。加入新素材时，LLM 读它、抽取关键信息、整合进已有 wiki——更新实体页、修订摘要、标注矛盾、演进综述。知识**编译一次然后持续保鲜**，不是每次查询重新推导。

## 它解决什么

RAG（见 [[RAG]]）每次查询都从零重新发现知识，没有积累。LLM Wiki 把 wiki 变成一个**持久的、复利式的产物**：交叉引用已经在、矛盾已经标记、综述已经反映读过的一切。每加一份素材、每问一个问题，它都更丰富。

分工是这个模式能成立的关键：人负责选材、探索、问对问题；LLM 负责总结、交叉引用、归档、记账。因为维护成本趋近于零，wiki 才不会像人工维护的 wiki 那样被弃（见 [[Memex]]——Bush 没能解决的「谁来维护」正是这里由 LLM 补上）。作者的类比：**Obsidian 是 IDE，LLM 是程序员，wiki 是代码库**（见 [[Obsidian]]）。

## 三层与三个操作

- 结构分三层——见 [[三层架构]]（raw sources / the wiki / the schema）。
- 维护靠三个操作——见 [[三个操作]]（Ingest / Query / Lint）。

## 适用场景

个人成长、长期研究、读书伴读 wiki、商业/团队内部 wiki（喂入 Slack、会议记录、客户通话）、竞品分析、尽调、行程规划、课程笔记等——任何随时间累积、希望被组织而非散落的知识。

常见叫法：LLM 维护的个人知识库、增量知识库、复利型 wiki、agent 维护的 wiki、Karpathy 的 wiki 模式、卡帕西 wiki。

## 关联
- 原文摘要: [[LLM Wiki (Karpathy)]]
- 结构: [[三层架构]]
- 维护操作: [[三个操作]]
- 对照基线: [[RAG]]
- 思想渊源: [[Memex]]
- 浏览端: [[Obsidian]]
- 检索工具: [[qmd]]
