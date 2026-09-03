---
type: source
tags: [rag, retrieval, embedding, bm25, reranking, web-source]
status: stable
summary: InfoQ 对 RAG 检索机制的说明——三阶段管线、embedding 的近似本质、BM25、RRF 融合、cross-encoder 重排。
---
# 混合检索与重排 (InfoQ)

> 来源: https://www.infoq.com/articles/vector-search-hybrid-retrieval-rag/
> 本地快照: `raw/articles/rag-hybrid-retrieval-infoq.md`
> 抓取日期: 2026-09-02。忠实转述，不加解读。

InfoQ 文章《Why Vector Search Alone Isn't Enough: Hybrid Retrieval for RAG》对 RAG 检索机制的说明。

## RAG 三阶段管线

1. **Chunking（切块）**——把源语料切成可索引单元。
2. **Retrieval（检索）**——对查询在这些块上搜索，返回 top-K 最相关的。
3. **Generation（生成）**——把这些块作为上下文交给 LLM 产出答案。

## embedding 是「近似引擎」

embedding 模型（如 BERT）把文本转成固定维度向量，语义相近的文本产生相近向量。它擅长按**意思**找相似内容，但系统性地不擅长区分**具体实体**——版本号、错误码、feature flag 名。文中例子：`enable` 与 `disable` 两份 runbook 在向量空间里几乎重合，向量检索可能把错的排在前面。

## 三种机制补足

- **BM25**（Best Matching 25）——词法排序函数，提供 embedding 给不了的精确度。三个机制：IDF（罕见区分性 token 加权）、词频饱和、文档长度归一化。
- **RRF**（Reciprocal Rank Fusion，倒数排名融合）——合并 BM25 与向量结果，不需分数归一化，只按排名位置，奖励两个检索器都认可的文档。
- **Cross-encoder 重排**——可选的最后一级，在小候选集上做最终相关性精排。

## 生产检索栈的分层

BM25 + 向量检索，用 RRF 融合，可选再跟一级 cross-encoder 重排。**向量检索不是被替换，而是与经典关键词匹配配对**，让概念相关与精确匹配都参与最终排序。

## 关联
- 转述对象: [[RAG]]
