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
| 原料层 | `raw/{articles,papers,assets}/` | 人 | ✅ 只勾 Keyword |
| 编译层 | `wiki/{concepts,entities,sources,synthesis}/` | agent | ✅ Keyword + Semantic |
| 特殊文件 | `wiki/index.md`、`wiki/log.md` | agent | ✅ 同上（在 `wiki/` 那行覆盖内） |

## 文件夹注册（三行，Settings → Capabilities → My Computer → Local Folders）

| # | 路径 | Agent access | Keyword | Semantic | KG |
|---|---|---|---|---|---|
| 1 | `~/Wiki-Vault` | ✓ 锁定 | ✗ | ✗ | ✗ |
| 2 | `~/Wiki-Vault/raw` | ✓ 锁定 | ✓ | ✗ | ✗ |
| 3 | `~/Wiki-Vault/wiki` | ✓ 锁定 | ✓ | ✓ | ✗ |

**KG 一列不勾**，原因见「为什么不用自动抽取」。三条约束：

- 顺序：先注册根（全关）→ 再加子目录。反过来会被拒（`Cannot enable indexing: subfolder X is already indexed`）
- Semantic 是 Keyword 的升级档，不能单独开 —— 勾它前必须先勾 Keyword
- Agent access 是索引前置条件，索引开着时它锁死不让关

## 工具分工（别混用）

| 要做什么 | 用什么 | 为什么不用别的 |
|---|---|---|
| 按意思找内容 | `file_rag_search(query, folder_path)` | `kg_search(semantic)` 只检索实体的**那一句** summary |
| 按页面类型筛 | `kg_search(category="Concept")`，支持多值 | `folder_path` 存注册路径，`wiki/` 一行，区分不了类型 |
| 查反向链接 | 全文检索 `[[X]]` 字面量 | `kg_search` 的 edges 有 **3 条上限**，枢纽页会被截断 |
| 灌边 / 建节点 | `kg_add(from_id, to_id)` | 名字解析是模糊的，必须用 id |
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

它比让 agent 现场写代码可靠 —— 实测过 agent 把方向字段判成 `"out"`（实际 `"outgoing"`），
误报「图谱 0 条边、严重漂移」。**查询 bug 比数据故障常见得多。**

### 检查清单（脚本覆盖 ✅ / 需人判断 👤）

| # | 项 | |
|---|---|---|
| 1 | 死链：`[[X]]` 指向不存在的文件 | ✅ |
| 2 | 孤儿页：零入链（**按豁免清单过滤**） | ✅ |
| 3 | frontmatter 四字段完整性 | ✅ |
| 4 | `index.md` ↔ 实际文件一致 | ✅ |
| 5 | 边一致性：文件 wikilink 数 == 库里 `linksTo` 数 | ✅ |
| 6 | 文件↔实体完整性：每个 `.md` 是否都有实体 | ✅ |
| 7 | 实体名污染：name 是否等于文件名去 `.md` | ✅ |
| 8 | 同名实体：多个候选 | ✅ 报出，👤 裁定 |
| 9 | 索引时效：`rag_index_time` < `modified_at` | ✅ |
| 10 | 来源不明的 `linksTo`：`reason` 为空 | ✅ |
| 11 | 矛盾：两页对同一事实说法冲突 | 👤 |
| 12 | 过期声明 | 👤 |
| 13 | 缺页：反复提到但没有独立页的概念 | 👤 |
| 14 | 缺交叉引用：两页明显相关但没互链 | 👤 |
| 15 | 数据缺口：可联网补上的空白 | 👤 |

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
| 实体名混进 summary（如 `qmd \| 本地 markdown 搜索引擎…`） | **工程层面** —— 文件 frontmatter 是干净的，是 `kg_add` 拼接时插入的分隔符不一致。只能靠检查项 7 抓 |
| agent 报告「已触发索引」但实际没发生 | **静默失败** —— 查 `rag_index_time` 是否真的动了（检查项 9） |
| `entity_count` 与 `nodes` 表实际数量不符 | Quick 的计数器不准，**以 `nodes` 表为准** |

## 为什么不用自动抽取（KG 开关不勾）

抽取器为**非结构化文档**设计（会议记录、邮件），价值在于从正文里发现藏着的实体，挖得越全越好。
但 wiki 页**没有待发现的东西** —— 实体名 = 文件名，category = frontmatter 的 `type`，
summary 也已写好。发现能力用在这里就是过度发现。

三组实测对照（同一个 23 页的 wiki）：

| 配置 | 结果 | 累计 tokens |
|---|---|---|
| 不用抽取器（agent 灌） | **23 页 = 23 实体，零偏差** | 0 |
| 带规则 + rebuild | 缺 2 实体、1 处撞名、5 处 category 错 | 87,271 |
| 无规则 + rebuild | 35 个碎片、21 处 category 错 | 197,572 |

`special_instructions` 是**软约束**，抽取器不保证遵守 —— 加规则能把碎片从 35 压到个位数，
但压不干净。**不能靠「把规则写得更严」解决，因为出问题的正是规则本身没被遵守。**

**关掉 KG 不影响已有的图** —— 那个开关只管「扫描时要不要自动抽取」，
图谱面板读的是全库数据。实测开关 `1 → 0` 前后节点/边数一个没动。

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
