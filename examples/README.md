# 示例：一次真实运行的完整产出

四份官方素材 ingest 之后的 wiki，可以直接对照页面格式、双链写法、`index.md` 结构。

| | |
|---|---|
| 内容页 | 59（27 concepts / 5 entities / 4 sources / 2 synthesis） |
| `linksTo` 边 | 298 |
| 死链 | 0 |
| lint | 12 项全绿 |

**素材来源**（都是官方原文，非二次加工）：

| 素材 | 大小 | 来源 |
|---|---|---|
| Karpathy 的 `llm-wiki` gist | 12 KB | gist 原文 |
| AWS Agent Registry GA 公告 | 35 KB | AWS 官方博客 |
| MCP 规范 2026-07-28 | 50 KB | `github.com/modelcontextprotocol/modelcontextprotocol` |
| A2A 规范（节选） | 42 KB | `github.com/a2aproject/A2A` |

后续又补了 AgentCore 相关的官方文档若干。

## 几处值得看的

**`sources/` 下的摘要页开头自带声明** —— agent 自己写的，不是模板：

```
> 素材：raw/articles/llm-wiki-karpathy.md
> 本页忠实转述素材内容，不加解读。解读见 [[...]]
```

**`synthesis/A2A 与 MCP 的关系.md`** —— 跨素材综合。它引的 A2A 规范 Appendix B
原话逐字可追溯，`MUST` / `SHOULD` / `MAY` 的规范性关键词没走形。

**`index.md`** —— 按类别分组的内容目录，每次 ingest 后更新。agent 回答问题时先读它定位。

**`log.md`** —— 只追加的操作日志，每条以 `## [YYYY-MM-DD] 操作 | 标题` 开头，
可以 `grep "^## \[" log.md | tail -5` 看最近五条。

## 注意

这些页面是**中文 wiki**，所以每页正文里有一段「常见叫法：A、B、C」——
给语义检索准备的。中文没有空格分词、同一概念说法又多，这一段直接决定它能不能
被口语化提问检索到。实测同一页面，加这段之前三个同义查询全部查不到，加之后全部命中第一名。
