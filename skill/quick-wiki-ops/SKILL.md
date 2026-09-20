---
name: quick-wiki-ops
description: >
  Operating guide for the LLM Wiki running on **Amazon Quick desktop** (vault at ~/Wiki-Vault).
  Load this when doing anything on the Quick-hosted wiki: ingest 素材、查询问答、跑 Lint 体检、
  灌 wikilink 边、配置文件夹索引、rebuild 后校正、诊断图谱漂移。
  与 wiki-ops 的区别：那个管 Obsidian + markdown-vault + S3 那套；**这个管 Quick 桌面端**
  （kg_* 工具族 / file_rag_search / run_python / 只读校验层）。
  触发词：Quick wiki、Wiki-Vault、kg_add、kg_search、file_rag_search、quick lint、灌边、
  抽取管线、kg_folder_rebuild。
---

# quick-wiki-ops — Quick 上的 LLM Wiki 操作手册

vault：`~/Wiki-Vault`。schema 正本：`~/Wiki-Vault/AGENTS.md`（同时是 Quick agent
「LLM Wiki Agent」的 instructions）。**本 skill 是校验与排障的确定性补充**，规格以
`AGENTS.md` 为准；两者有出入时以用户最新决定为准。

## 一句话架构

markdown 文件在 `~/Wiki-Vault` → Quick 桌面端建两套索引（全文 + 语义）→ 图谱由 agent
用 `kg_add` 显式灌，**不开自动抽取** → 检索靠 `file_rag_search` + `kg_search`。

## 目录分区

| 层 | 目录 | 谁写 | 索引配置 |
|---|---|---|---|
| schema | `AGENTS.md` | 人 | ❌ 不索引（靠 Agent access 直读） |
| 原料层 | `raw/{articles,papers,assets}/` | 人 | ✅ 开 Indexing |
| 编译层 | `wiki/{concepts,entities,sources,synthesis}/` | agent | ✅ 开 Indexing |
| 特殊文件 | `wiki/index.md`、`wiki/log.md` | agent | ✅ 同上（在 `wiki/` 那行覆盖内） |

## 文件夹注册（三行，Settings → Capabilities → My Computer → Local Folders）

| # | 路径 | Agent access | Allow full file context | Always remember |
|---|---|---|---|---|
| 1 | `~/Wiki-Vault` | ✓ | ✗ | ✗ |
| 2 | `~/Wiki-Vault/raw` | ✓ | ✓ | ✗ |
| 3 | `~/Wiki-Vault/wiki` | ✓ | ✓ | ✗ |

**`Always remember file information` 不开**，原因见「为什么不用自动抽取」。四条约束：

- **添加文件夹 ≠ 建索引** —— 只添加只给 Agent access，索引要单独开 `Indexing`
- 顺序：先注册根（不开索引）→ 再加子目录。同一棵树上父子不能都开索引，反过来会被拒（`Cannot enable indexing: subfolder X is already indexed`）
- **索引在云端** —— 开 Indexing 等于文件全文上传到 Quick Space，上传→可检索约 1 分钟。本机 `files` / chunk 表不会有记录
- `index_directory` 工具跑在云端后端、看不到设备本地路径（报 `Directory not found`）；索引由 Quick 客户端自动建，不用手工触发

## 工具分工（别混用）

| 要做什么 | 用什么 | 为什么不用别的 |
|---|---|---|
| 按意思找内容 | `file_rag_search(query, folder_path)` | `kg_search(semantic)` 只检索实体的**那一句** summary |
| 按页面类型筛 | `kg_search(category="Concept")`，支持多值 | `folder_path` 存注册路径，`wiki/` 一行，区分不了类型 |
| 查反向链接 | 全文检索 `[[X]]` 字面量 | `kg_search` 的 edges 有 **3 条上限**，枢纽页会被截断 |
| 灌边 / 建节点 | `kg_add(from_id, to_id)` | 名字解析是模糊的，必须用 id；**补欠账时按源文件分批（每批 10~15 页），别一次灌几十页 —— 前端面板大批量加载有上限** |
| 批量解析 + 比对 | `run_python(code, tools=[...])` | 不传 `tools` 这些函数不在命名空间，报 `NameError` |
| 全量边 / 索引时间戳 | `wiki-inspect` MCP 或 lint 脚本 | 内置工具拿不到 |

## 校验数据从哪来

`quick_wiki_lint.py` 和 `wiki-inspect` MCP 都以**只读方式**读取 Quick 的本地索引状态，
用来比对「vault 里的 markdown 文件」和「Quick 记录的状态」是否一致。

**⚠️ 只读。** 不要尝试写入 —— 那会绕过 Quick 自己的索引更新和计量，让状态不一致。
写操作一律走 `kg_add` / `kg_edit` / `file_write`。

## LINT — 说「lint」「体检」时跑

`scripts/quick_wiki_lint.py` 是**确定性实现**，优先用它而不是现场写代码：

```bash
python3 ~/.claude/skills/quick-wiki-ops/scripts/quick_wiki_lint.py            # 全部检查
python3 ~/.claude/skills/quick-wiki-ops/scripts/quick_wiki_lint.py --strict   # 有问题则退出码 1
python3 ~/.claude/skills/quick-wiki-ops/scripts/quick_wiki_lint.py --json     # 机器可读
```

它比让 agent 现场写代码可靠 —— 逻辑固定、结果可复现。
**查询 bug 比数据故障常见得多**，所以异常数字先怀疑查询写错。

### 检查清单

脚本只查文件层 —— 索引和图谱在云端 Quick Space，本机没有副本。三组：

| # | 项 | 谁查 |
|---|---|---|
| 1 | 死链：`[[X]]` 指向不存在的文件 | ✅ 脚本 |
| 2 | 孤儿页：零入链（**按豁免清单过滤**） | ✅ 脚本 |
| 3 | frontmatter 四字段完整性 | ✅ 脚本 |
| 4 | `index.md` ↔ 实际文件一致 | ✅ 脚本 |
| 9 | `type` 取值：是四类之一，且和子目录对应 | ✅ 脚本 |
| 13 | 文件夹注册 + `sync_status` 是否 synced | ✅ 脚本（读权限层） |
| 14 | 缺页候选：从 `raw/` 结构里提的名字 | ✅ 脚本给候选，👤 判断 |
| 15 | 枢纽分布：网状还是星形 | ✅ 脚本 |
| — | 实体在图谱里有没有节点、边有没有灌进去 | 🔍 `kg_search`（Quick 里） |
| — | 同名实体：多个候选 | 🔍 `kg_search` 报出，👤 裁定 |
| — | 索引进度、chunk 数、索引时间戳 | 🔍 `file_rag_status`（Quick 里） |
| — | 矛盾：两页对同一事实说法冲突 | 👤 |
| — | 过期声明 | 👤 |
| — | 缺交叉引用：两页明显相关但没互链 | 👤 |
| — | 数据缺口：可联网补上的空白 | 👤 |

> **数边只信脚本的数字。** 报的 `total_edges` 是按 `(from, to)` 去重、且剥掉代码块
> 后的唯一有向边数。自己 `grep '\[\['` 数出来的会更大 —— 那是含重复、含语法示例的
> 原始 wikilink 数（实测同一 vault：359 原始 → 348 剥代码块 → 187 去重）。

### 孤儿页豁免清单（这几类正常无入链，忽略）

1. **`wiki/sources/` 下的摘要页** —— 按设计单向被引（source 页链出去，别人不链它）
2. **`wiki/index.md`、`wiki/log.md`** —— 元文件，`index.md` 的出链是目录条目、不是知识关联
3. **刚建的页**（当天创建 + `status: stub`）—— 还没被其他页链上是正常的，报「待接线」而非缺陷
4. **`AGENTS.md`** —— schema 层，不参与知识网

### 边计数豁免（这几类不算 wikilink 边）

1. **`index.md` / `log.md` 的出链** —— 目录条目和记录引用，是导航不是关联。**数边时排除这两个文件**
2. **抽取管线产的边** —— `relatedTo` / `mentions` / `isPartOf` / `about` / `hasPart` / `dependsOn`。
   只数 `relation='linksTo'`，混在一起数会永远不一致
3. **`reason` 为空的 `linksTo`** —— agent 灌的每条都写了 `"wikilink in <文件名>"`，
   空的说明来自别处，单独报不计入

### 已知的工程层面缺陷（加规则解决不了，只能靠比对发现）

| 现象 | 判定 |
|---|---|
| 实体名混进 summary（如 `qmd \| 本地 markdown 搜索引擎…`） | **工程层面** —— 文件 frontmatter 是干净的，是 `kg_add` 拼接时插入的分隔符不一致。用 `kg_search` 查页名，看回来的节点名对不对 |
| agent 报告「已触发索引」但实际没发生 | **静默失败** —— 用 `file_rag_status` 看索引时间戳是否真的动了，别信工具的成功消息 |
| `kg_search` 某节点只回 3 条边 | **不是只有 3 条** —— 那是接口上限。准确边数用 `wiki_hubs` / `wiki_edges` |

## 为什么不用自动抽取（`Always remember file information` 不开）

抽取器为**非结构化文档**设计（会议记录、邮件），价值在于从正文里发现藏着的实体，挖得越全越好。
但 wiki 页**没有待发现的东西** —— 实体名 = 文件名，category = frontmatter 的 `type`，
summary 也已写好。发现能力用在这里就是过度发现。

让 agent 在写页时用 `kg_add` 显式灌，图和文件严格一对一、零 token 开销。
开自动抽取则会额外产出正文术语的碎片节点，还要花 token 善后 —— 实测拿一段讲负载均衡、
消息队列的普通技术文字去跑，抽出了「缓存层」「限流器」「对象存储」「分布式追踪」
一串 `Defined Term` 节点，它们在 wiki 的结构里没有位置。

`special_instructions` 是**软约束**，抽取器不保证遵守 —— 写规则能减少碎片，但压不干净。
**不能靠「把规则写得更严」解决，因为出问题的正是规则本身没被遵守。**

**不开这个开关不影响 `kg_add` 灌的图。** `kg_add` 显式灌的节点和边照常进去，
哪怕自动抽取一次都没跑，图在「知识图谱」面板里也是完整可用的。开抽取只是额外多灌
一批正文术语的碎片节点。

> **灌入方式决定前端能不能渲染（实测）。** 一份份增量灌（每批一份素材、10~15 页），
> 面板逐簇累积、整张图正常显示；短时间内一次性把几十页全灌完，面板的大批量加载
> 会出问题（只剩根节点画不出）。所以补历史欠账时**必须按源文件分批**。
> 「写页即同步」天然是一页一灌，不会踩这个上限。

## rebuild 后必须校正（只在确实要跑抽取时）

`kg_folder_rebuild` 先删光该文件夹的实体再重抽，而边会随节点级联删除
—— **节点一删，agent 灌的边全没**。所以：

```
rebuild 之前：从文件解析全部 wikilink，按「页名」固化（不记 node_id —— rebuild 后 id 全变）
rebuild 之后：
  1. 完整性  文件数 == 实体数？列出没产出实体的文件
  2. 名字    按 source_file 校验 name == 文件名去 .md，不等就 kg_edit 改
  3. category 按 frontmatter type 校验
  4. summary  按 frontmatter summary 校验
  5. 重灌边   用固化的页名重查 node_id，灌回 linksTo
  6. 核验     文件边数 == 库里 linksTo 边数
```

**权威依据是实体的 `source_file` 属性，不是抽取器起的名字。** 名字会偏，`source_file` 不会。

## 避坑

- **灌边必须用 `from_id` / `to_id`，不要用名字。** `kg_add` 的名字解析是模糊的：可能挂到
  同名但不同来源的实体上，也可能被模糊匹配到名字略有差异的既有实体。挂错了
  `kg_edit(delete_edges=...)` 删掉重来
- **死链不要灌边** —— 会凭空建出空实体，把死链掩盖成正常节点。报告，不灌
- **`run_python` 必须传 `tools=[...]`**，否则 `kg_search`/`kg_add` 不在命名空间
- **wikilink 变体要归一化**：`[[X|别名]]` → X，`[[X#章节]]` → X，`![[X]]` → X。
  同一对 (from, to) 出现多次只算一条边
- **新建节点的 `category` 用 frontmatter 的 `type` 首字母大写**（`Concept` / `Entity` /
  `Source` / `Synthesis`）—— `kg_search(category=...)` 过滤靠它
- **索引不是实时的** —— 按 `Scan interval` 定时扫描（默认 30 分钟）。所以写页后要
  显式触发索引，别等
- **`kg_search` 的 edges 有 3 条上限** —— 数边要逐页查，或用 `wiki_edges()`

## 三个操作的边界（详见 AGENTS.md）

- **Ingest** —— 只有开始前讨论要点这一步要等确认，之后（写页 → 灌边 → 更新 index →
  追加 log → 触发索引）连着做完
- **Query** —— 归档判断自己做：复述已有内容不归档；跨页综合/新对比直接写成 synthesis 页
- **Lint** —— 只报告不动手。**这是定义，不是需要请示**。待办列在报告末尾，不做成选择题

## 参考

- `~/Wiki-Vault/AGENTS.md` —— schema 正本
- Karpathy `llm-wiki` gist（2026-04-04）—— 模式原始定义
- `wiki-ops` skill —— Obsidian + markdown-vault + S3 那套（不同环境，别混用）
