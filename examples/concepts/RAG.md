---
type: concept
tags: [rag, retrieval, baseline]
status: developing
summary: 检索增强生成——查询时从原始文档检索相关片段并生成答案；作为 LLM Wiki 的对照基线，其局限是知识不累积、每次查询从零重新拼凑。
---
# RAG

Retrieval-Augmented Generation（检索增强生成）：上传一堆文件，查询时 LLM 检索相关片段，基于片段生成答案。NotebookLM、ChatGPT 文件上传、多数「与文档对话」系统都是这个模式。

## 作为 LLM Wiki 的对照基线

原文用 RAG 作为反面参照来讲清 [[LLM Wiki]] 的价值。RAG 可行，但：

- **知识不累积**——LLM 每次查询都在从零重新发现知识。
- **反复重拼**——问一个需要综合五份文档的问题，LLM 每次都要重新查找、拼凑相关片段。
- **什么都没被建立起来**——交叉引用、矛盾标记、综述都不留存。

LLM Wiki 的差异：知识**编译一次然后持续保鲜**，wiki 是持久、复利的产物，而非每次查询重新推导。

> 注：本页目前只覆盖原文把 RAG 作对照基线的用法，`status: developing`。RAG 本身的机制（embedding、向量检索、重排等）待专门素材再充实。

常见叫法：检索增强生成、Retrieval-Augmented Generation、检索式问答、与文档对话、chat with your docs、向量检索问答。

## 关联
- 对照的模式: [[LLM Wiki]]
