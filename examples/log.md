---
type: log
tags: [meta]
status: developing
summary: 只追加的操作日志。每条以「## [YYYY-MM-DD] 操作 | 标题」开头，可用 grep 解析。
---
# Log

只追加的操作记录。**永不删除历史条目。**

每条以固定前缀开头，便于用 unix 工具解析：

```
grep "^## \[" log.md | tail -5     # 最近五条
```

格式：`## [YYYY-MM-DD] <ingest|query|lint> | <标题>`

---


## [2026-09-02] ingest | LLM Wiki (Karpathy)

首次 ingest，素材 `raw/articles/llm-wiki-karpathy.md`。建 8 页：source ×1（[[LLM Wiki (Karpathy)]]）、concept ×5（[[LLM Wiki]]、[[三层架构]]、[[三个操作]]、[[RAG]]、[[Memex]]）、entity ×2（[[Obsidian]]、[[qmd]]）。灌 18 条 linksTo 边（解析 18 == 库内 18），无死链。周边工具（Marp / Dataview / Web Clipper / Tolkien Gateway）按规则并入相关页未单开。index 已更新，索引已触发。

## [2026-09-02] ingest | AWS Agent Registry (AWS Blog)

自动 ingest，素材 `raw/articles/aws-agent-registry.md`（35 KB，AWS Agent Registry GA 公告）。建 11 页：source ×1（[[AWS Agent Registry (AWS Blog)]]）、entity ×3（[[AWS Agent Registry]]、[[Amazon Bedrock AgentCore]]、[[Amazon Quick]]）、concept ×7（[[两个平面]]、[[四种记录类型]]、[[四种角色]]、[[记录生命周期]]、[[Model Context Protocol]]、[[Agent2Agent]]、[[Shadow AI]]）。更新已有页 [[qmd]]（补一条到 [[Model Context Protocol]] 的交叉引用）。全库解析 60 条 linksTo（含上簇 18 条），库内实际 60，无重复无死链。index 已更新，索引已触发。stub 页：Amazon Bedrock AgentCore、Amazon Quick、Agent2Agent（待专门素材再充实）。

## [2026-09-02] ingest | MCP Specification (2026-07-28)

自动 ingest，素材 `raw/articles/mcp-specification-2026-07-28.md`（51 KB，MCP 官方规范 2026-07-28 版）。新建 11 页：source ×1（[[MCP Specification (2026-07-28)]]）、concept ×10（[[客户端-主机-服务器架构]]、[[无状态协议]]、[[能力协商]]、[[MCP 服务器原语]]、[[MRTR 与 InputRequiredResult]]、[[_meta 元数据]]、[[MCP 消息模式]]、[[MCP 安全与信任]]、[[MCP 关键变更]]、以及扩充）。扩充已有页 [[Model Context Protocol]]（从 developing→stable，叠加协议本体细节，保留全部 registry/qmd 交叉引用）。全库解析 107 条 linksTo（含前两簇），库内实际 107，无重复无死链。29 页各自唯一解析到一个节点，无同名歧义。index 已更新，索引已触发。

## [2026-09-02] ingest | A2A Specification

自动 ingest，素材 `raw/articles/a2a-specification.md`（42 KB，A2A 协议官方规范节选）。新建 8 页：source ×1（[[A2A Specification]]）、concept ×6（[[A2A 三层规范结构]]、[[A2A Task]]、[[A2A 协议操作]]、[[Agent Card]]、[[A2A 消息与内容模型]]、[[Push Notifications]]）、synthesis ×1（[[A2A 与 MCP 的关系]]，本 vault 首个 synthesis 页）。扩充已有页 [[Agent2Agent]]（stub→stable，保留全部 registry 交叉引用）。全库解析 163 条 linksTo，库内实际 163，无重复无死链（解析时修正了 synthesis 表格里转义管道 \| 的归一化）。37 页各自唯一解析到一个节点，无同名歧义。index 已更新，索引已触发。
## [2026-09-02] query | 一个 agent 怎么找到另一个 agent 帮它干活

Query 归档。基于 [[Agent Card]]、[[A2A 协议操作]] 回答 A2A 的 agent 发现机制，并归档一页 synthesis [[A2A 委派端到端流程]]（串起 发现→选传输→验签认证→Send Message 建 Task→拿结果 的端到端时序）。灌 9 条 linksTo，全库 172 条（解析 172 == 库内 172），无死链无重复。index 已更新，索引已触发。
