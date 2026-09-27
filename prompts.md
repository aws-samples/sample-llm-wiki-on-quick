# 提示词

## 创建 agent

```
建一个 agent，名字叫「LLM Wiki Agent」。

描述：维护 ~/Wiki-Vault 这个 LLM Wiki —— 消化素材、回答问题、做体检。

instructions 用 ~/Wiki-Vault/AGENTS.md 的全文，原样放进去，不要改写、不要精简。

welcome_message：
我维护 ~/Wiki-Vault。把素材放进 raw/ 让我 ingest，或者直接问我 wiki 里有什么。

starter_prompts：
自动 ingest raw/ 里的新素材
wiki 里都有什么
做一次体检（lint）
```

## 验证 MCP

```
跑一次 wiki_lint
```

## Ingest

```
ingest raw/articles/llm-wiki-karpathy.md
```

```
自动 ingest raw/articles/aws-agent-registry.md
```

## Query

```
MCP 的主要功能是什么?
```

```
一个 agent 想让另一个 agent 帮它干活，怎么找到对方？
```

## Lint

```
对 ~/Wiki-Vault 做一次完整体检
```

## 定时任务

```
每天对 ~/Wiki-Vault 做一次体检。只查不改，跳过语义判断。
任一工具不可用，在报告里写该项「未检查」，继续下一步，不要自己写代码代替。

1. 跑 wiki_lint(brief=True)。
2. 用 wiki_edges(for_kg=True) 取边集，对 pages 逐个 kg_search 拿 node_id，数出文件里有、图谱里没有的边。只数不灌。
3. 随机抽 3~5 个页名 kg_search，核对名字、category、summary 与文件名和 frontmatter 是否一致，查四类之外的碎片节点。
4. 用 wiki_lint #10 的 raw/、wiki/ 最新 mtime（epoch）对比 file_rag_status 的 rag_index_time。

用 update_feed 发报告，每项写具体页面名。全绿只写「无问题」。
有问题时，末尾只列有发现的项：
[1] 补边 [2] 更新索引 [3] 修抽取偏差 [4] 完整体检 [5] 处理缺页候选
```

工具策略只写 `kg_search`、`file_rag_status`、`update_feed`、`wiki_lint`、`wiki_edges`、`wiki_hubs`，并打开 `allow_unscoped_write_tools`。
创建前用 `validate_tool_policy` 确认 `kg_add`、`kg_edit`、`index_directory`、`file_write`、`sync_indexed_folders` 全部 DENIED。
