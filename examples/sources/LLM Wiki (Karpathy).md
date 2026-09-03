---
type: source
tags: [llm-wiki, knowledge-base, rag, memex, obsidian]
status: stable
summary: Karpathy 提出的 LLM Wiki 模式原文摘要——用 LLM 增量维护一个持久、互链的 markdown wiki，替代每次查询重新检索的 RAG。
---
# LLM Wiki (Karpathy)

> 忠实转述 `raw/articles/llm-wiki-karpathy.md`，不加解读。解读见 [[LLM Wiki]] 及相关 concept 页。

原文副标题：*A pattern for building personal knowledge bases using LLMs.*

这是一份「idea 文件」，设计成复制粘贴给自己的 LLM agent（如 OpenAI Codex、Claude Code、OpenCode / Pi 等）。目标是传达高层想法，具体细节由 agent 与你协作搭建。

## The core idea

多数人用 LLM 处理文档的方式是 RAG：上传一堆文件，查询时 LLM 检索相关片段并生成答案。这可行，但 LLM 每次都在从零重新发现知识，没有积累。问一个需要综合五份文档的微妙问题，LLM 每次都要重新查找、拼凑相关片段。什么都没被建立起来。NotebookLM、ChatGPT 文件上传、多数 RAG 系统都是这样。

这里的想法不同：LLM 不只是在查询时从原始文档检索，而是**增量地构建并维护一个持久的 wiki**——一个结构化、互链的 markdown 文件集合，位于你和原始素材之间。加入新素材时，LLM 不只是索引它备查，而是读它、抽取关键信息、整合进已有 wiki——更新实体页、修订主题摘要、标注新数据与旧说法矛盾之处、强化或挑战正在演进的综述。知识被编译一次，然后**持续保鲜**，而不是每次查询重新推导。

关键区别：**wiki 是一个持久的、复利式的产物。** 交叉引用已经在那了。矛盾已经被标记了。综述已经反映了你读过的一切。每加一份素材、每问一个问题，wiki 都变得更丰富。

你几乎从不自己写 wiki——LLM 写并维护全部。你负责选材、探索、问对的问题。LLM 做所有苦力活——总结、交叉引用、归档、记账，那些让知识库长期有用的事。作者的实践：一边开 LLM agent，一边开 Obsidian，LLM 根据对话做编辑，作者实时浏览结果（跟链接、看 graph view、读更新的页）。**Obsidian 是 IDE；LLM 是程序员；wiki 是代码库。**

适用场景举例：个人（目标/健康/心理/自我提升）、研究（数周数月深挖一个主题、演进的论点）、读书（逐章归档人物/主题/情节线，最终得到一份伴读 wiki，类比 Tolkien Gateway 这类粉丝 wiki）、商业/团队（LLM 维护的内部 wiki，喂入 Slack 线程/会议记录/项目文档/客户通话，可有人类审核）、竞品分析/尽调/行程规划/课程笔记/兴趣深挖。

## Architecture

三层：

- **Raw sources**——你策展的源文档集合（文章、论文、图片、数据文件）。不可变——LLM 只读不改。这是你的 source of truth。
- **The wiki**——一个 LLM 生成的 markdown 文件目录（摘要、实体页、概念页、对比、综述、synthesis）。LLM 完全拥有这层：创建页、新素材到来时更新、维护交叉引用、保持一致。你读，LLM 写。
- **The schema**——一份文档（Claude Code 用 `CLAUDE.md`，Codex 用 `AGENTS.md`），告诉 LLM wiki 怎么组织、约定是什么、ingest / 回答 / 维护时遵循什么工作流。这是关键配置文件——它让 LLM 成为有纪律的 wiki 维护者而非通用聊天机器人。你和 LLM 随时间共同演进它。

## Operations

- **Ingest.** 把新素材放进 raw 集合，让 LLM 处理。示例流程：LLM 读源、与你讨论要点、写 wiki 摘要页、更新 index、更新 wiki 里相关的实体和概念页、追加一条 log。一份素材可能牵动 10-15 页。作者个人偏好一次 ingest 一份并保持参与（读摘要、检查更新、指导强调什么），但也可以少监督地批量 ingest。工作流由你发展并写进 schema。
- **Query.** 向 wiki 提问。LLM 检索相关页、读它们、带引用综合出答案。答案形式随问题而定——markdown 页、对比表、幻灯片（Marp）、图表（matplotlib）、canvas。关键洞见：**好答案可以回填成 wiki 新页。** 你要过的一个对比、一份分析、你发现的一处关联——这些有价值，不该消失在聊天记录里。这样探索也像 ingest 的素材一样在知识库里复利。
- **Lint.** 定期让 LLM 体检 wiki。找：页间矛盾、被新素材取代的过期说法、无入链的孤儿页、被提到却没有自己页面的重要概念、缺失的交叉引用、可以靠一次联网搜索补上的数据缺口。LLM 擅长建议新的待研究问题和值得找的新素材。

## Indexing and logging

两个特殊文件帮助导航：

- **index.md** 面向内容。整个 wiki 的目录——每页列出链接、一句摘要、可选元数据（日期、素材数）。按类别组织（entities、concepts、sources 等）。LLM 每次 ingest 更新它。回答查询时 LLM 先读 index 找相关页，再钻进去。在中等规模（约 100 份素材、数百页）表现出奇地好，免去 embedding RAG 基础设施。
- **log.md** 面向时间。只追加的记录——ingest / query / lint 发生了什么、何时。技巧：每条以一致前缀开头（如 `## [2026-04-02] ingest | Article Title`），日志就能用简单 unix 工具解析——`grep "^## \[" log.md | tail -5` 给出最近五条。

## Optional: CLI tools

规模变大后可能想建小工具帮 LLM 更高效操作 wiki。最明显的是 wiki 页的搜索引擎——小规模 index 文件够用，变大后需要正经搜索。[qmd](https://github.com/tobi/qmd) 是个好选择：本地 markdown 搜索引擎，混合 BM25/向量检索加 LLM 重排，全在设备上。有 CLI（LLM 可 shell out）也有 MCP server（LLM 可当原生工具用）。也可以自己 vibe-code 一个更简单的搜索脚本。

## Tips and tricks

- **Obsidian Web Clipper**——浏览器扩展，把网页文章转成 markdown。快速把素材弄进 raw 集合很有用。
- **Download images locally.**——Obsidian 设置里把附件路径设为固定目录（如 `raw/assets/`），绑一个下载热键，剪藏后一键把图片下到本地。可选但有用——让 LLM 直接看图而非依赖可能失效的 URL。注意 LLM 无法一遍读完带内联图片的 markdown，变通做法是先读文本再单独看引用的图片。
- **Obsidian's graph view**——看 wiki 形状的最佳方式：什么连着什么、哪些页是枢纽、哪些是孤儿。
- **Marp**——基于 markdown 的幻灯片格式，Obsidian 有插件，可直接从 wiki 内容生成演示。
- **Dataview**——Obsidian 插件，对页面 frontmatter 跑查询。若 LLM 给 wiki 页加了 YAML frontmatter（tags、日期、素材数），Dataview 能生成动态表格和列表。
- wiki 就是一个 markdown 文件的 git repo——版本历史、分支、协作都白送。

## Why this works

维护知识库的苦活不是阅读或思考，而是**记账**：更新交叉引用、保持摘要最新、标注新数据与旧说法矛盾、维护数十页的一致性。人类抛弃 wiki，是因为维护负担增长快过价值。LLM 不会厌倦、不会忘记更新交叉引用、能一次动 15 个文件。wiki 之所以保持被维护，是因为维护成本趋近于零。

人的工作：策展素材、指导分析、问好问题、思考这一切意味着什么。LLM 的工作：其余一切。

这个想法在精神上关联 Vannevar Bush 的 Memex（1945）——一个私人、策展的知识存储，文档间有关联性的 trail。Bush 的愿景更接近这个而非 web 后来的样子：私密、主动策展、文档间的连接与文档本身同样有价值。他没能解决的部分是「谁来维护」。LLM 处理了那部分。

## Note（原文结尾）

原文强调它有意保持抽象：它描述的是想法，不是具体实现。确切的目录结构、schema 约定、页面格式、工具——都取决于你的领域、偏好和所选 LLM。上面提到的一切都是可选且模块化的：挑有用的，忽略没用的。正确用法是把它分享给你的 LLM agent，一起实例化一个适合你需求的版本。

## 关联
- 概念中心页: [[LLM Wiki]]
