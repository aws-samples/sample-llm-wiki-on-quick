---
type: entity
tags: [qmd, tool, search, bm25, vector-search, mcp]
status: developing
summary: 本地 markdown 搜索引擎，混合 BM25/向量检索加 LLM 重排，全在设备上；有 CLI 和 MCP server 两种接口，用于 LLM Wiki 规模变大后的检索。
---
# qmd

一个本地 markdown 文件搜索引擎（[github.com/tobi/qmd](https://github.com/tobi/qmd)）。特点：**混合 BM25 + 向量检索 + LLM 重排**，全部在设备本地运行。

## 在 LLM Wiki 里的角色

[[LLM Wiki]] 小规模时 `index.md` 就够用；wiki 变大后想要正经搜索，qmd 是原文推荐的选择。它提供两种接口：

- **CLI**——LLM 可以 shell out 调用。
- **MCP server**（[[Model Context Protocol]]）——LLM 可当原生工具使用。

原文也提到可以自己 vibe-code 一个更简单的搜索脚本替代。

常见叫法：qmd、markdown 搜索引擎、本地检索工具、BM25 向量混合检索、on-device 搜索、tobi/qmd。

## 关联
- 用于模式: [[LLM Wiki]]
- 浏览端: [[Obsidian]]
- 接口协议: [[Model Context Protocol]]
