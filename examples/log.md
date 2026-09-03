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

## [2026-09-02] lint-fix | 补建 2 缺页 + 修 3 处缺交叉引用
- 新建 concepts/Elicitation.md、concepts/Opaque Execution.md（依据已 ingest 的 MCP/A2A 源页）
- 补入链：MCP 服务器原语→Elicitation、Agent2Agent→Opaque Execution、两页 synthesis 正文裸词接 Opaque Execution
- 补缺交叉引用：无状态协议→MRTR、MCP 安全与信任↔客户端-主机-服务器架构、记录生命周期↔两个平面
- 未处理（需新 raw 素材，不编造）：缺页 Skill；数据缺口 Memex/AgentCore/RAG/Registry 定价

## [2026-09-02] ingest | 联网补全 4 处数据缺口（定点搜索）
- 方式：定点联网搜索 + 抓取权威页（非 Quick research），针对 lint 报出的 4 处数据缺口
- 新建 4 个 web 素材摘要页（标注来源 URL，忠实转述）：
  - sources/AWS Agent Registry 定价与区域 (Unite.AI).md
  - sources/AgentCore Gateway (AWS Docs).md
  - sources/混合检索与重排 (InfoQ).md
  - sources/As We May Think (Bush 1945).md
- 更新 4 个目标页：
  - RAG：补三阶段管线 + BM25/RRF/cross-encoder 重排机制，developing→stable，链到 qmd
  - Memex：补 As We May Think 出处/关联索引机制/影响，stub→developing
  - Amazon Bedrock AgentCore：补 Gateway 六项能力机制，stub→developing（Runtime 仍待素材）
  - AWS Agent Registry：模糊「消费型定价」替换为具体数字 + Free Tier 阈值
- raw/ 未改动（web 素材仅在 source 页引 URL，未落地本地快照）
- 灌边 + 更新 index + 触发索引见后续

## [2026-09-02] ingest | 网页永久留档 + 补齐 AgentCore Runtime
- 永久留档：把 5 份网页正文存成本地快照进 raw/articles/（仅新增，未触碰已有 raw 文件）：
  - aws-agent-registry-pricing-uniteai.md、agentcore-gateway-aws-docs.md
  - rag-hybrid-retrieval-infoq.md、as-we-may-think-bush-1945.md、agentcore-runtime-aws-docs.md
- 4 个既有 web source 页补上「本地快照」路径指针
- 补最后缺口 AgentCore Runtime：新建 sources/AgentCore Runtime (AWS Docs).md
  （microVM 会话隔离 / microVMs 8h vs Instances 14天 / 版本端点 / MCP+A2A / 认证 / 消费型定价）
- Amazon Bedrock AgentCore：补 Runtime 机制段，developing→stable（Gateway+Runtime 均已覆盖）
- 灌边 + 更新 index + 触发索引见后续。至此 stub 页清零、数据缺口清零

## [2026-09-02] ingest | 补全 AgentCore 服务簇（枢纽页 + 12 实体页）
- 起因：用户指出漏了 AgentCore 服务簇里的多项兄弟服务。根因是我把 AgentCore 当单一实体补全，被旧页「含 Runtime+Gateway」框定锚住，且未对新 ingest 素材重扫缺页——Memory/Identity 其实早在我存的 Runtime 快照里出现过
- 归档：raw/articles/agentcore-overview-aws-docs.md（总览页快照，仅新增）
- 新建源页：sources/AgentCore 服务簇总览 (AWS Docs).md（13 服务逐条转述）
- 新建枢纽概念页：concepts/AgentCore 服务簇.md（列全 13、服务间咬合）
- 新建 12 个实体页：Runtime、Gateway、Memory、Identity、Harness、Code Interpreter、Browser、Observability、Payments、Evaluations、Optimization、Policy
  （Runtime/Gateway 此前只寄居在产品页、无独立实体页，此次补上；第 13 个 Registry 复用既有 [[AWS Agent Registry]]）
- 修正 entities/Amazon Bedrock AgentCore.md：框定从「两组件」改为「一簇 13 服务」，链到枢纽页，加纠正说明（加法式，未删已有机制段）
- 灌边 + 更新 index + 触发索引见后续
- 待定（列出不做）：产品页里 Runtime/Gateway 机制段是否瘦身移交给新实体页——属重写已有页，等用户定夺

## [2026-09-03] ingest | ARD (AWS Blog)

协作模式 ingest，素材 `raw/articles/ard-agentic-resource-discovery.md`（AWS 博客，ARD 开放规范，2026-08-24）。新建 3 页：source ×1（[[ARD (AWS Blog)]]）、concept ×1（[[Agentic Resource Discovery]]）、synthesis ×1（[[Agent 发现的三个层次]]，对比 Agent Card / AWS Agent Registry / ARD 三层发现）。扩充已有页 [[AWS Agent Registry]]（补 Registries+Registry Records 两个核心概念、MCP-native endpoint、hybrid search；显式标注 preview 2026-08-24 → GA 2026-08-31 时间线，非矛盾）。全库解析 316 条 linksTo，库内实际 316，无重复无死链。62 页各自唯一解析，无同名歧义。index 已更新，索引已触发。
