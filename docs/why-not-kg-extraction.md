# 为什么 KG 一列不勾

README 那张注册表里 Knowledge Graph 全不勾 —— 但**知识图谱是要用的**，只是不靠
Quick 的自动抽取，而是由 agent 在写页时用 `kg_add` 显式灌。

这是实测结论，不是一开始的选择。最初配的是三个全勾，跑完两次 `kg_folder_rebuild`
才改的。

## 三组对照

同一个 23 页的 wiki，三种配置各跑一遍：

| 配置 | 结果 | 累计 tokens |
|---|---|---|
| **不用抽取器**（agent 灌） | **23 页 = 23 实体，零偏差** | 0 |
| 带规则 + rebuild | 缺 2 实体、1 处撞名、5 处 category 错 | 87,271 |
| 无规则 + rebuild | 35 个碎片实体、21 处 category 错 | 197,572 |

十九万七千 token，换来一个比第一行更差的图。

## `special_instructions` 是软约束

同一次 rebuild 里，写进配置的四条规则全被违反：

| 规则 | 实际结果 |
|---|---|
| 一文件一实体 | 23 个文件只产出 21 个实体 —— 两页完全没抽到 |
| 实体名 = 文件名去 `.md` | `concepts/LLM Wiki.md` 被命名成 `LLM Wiki 模式`，和 source 页**撞名** |
| category 用 frontmatter 的 `type` | 出现 `Product` / `CreativeWork` / `DefinedTerm` |
| summary 用 frontmatter 的 `summary` | 被换成了正文里某个段落 |

**不能靠「把规则写得更严」解决** —— 出问题的正是规则本身没被遵守。实验 ② 和 ③
的差距说明规则有效（碎片从 35 个压到个位数），但压不干净。

## 抽取器确实产边 —— 但不是 `linksTo`

两次 rebuild 累计产出 **110 条**非 `linksTo` 边：

| relation | 条数 |
|---|---|
| `relatedTo` | 39 |
| `mentions` | 19 |
| `about` | 14 |
| `isPartOf` | 12 |
| `hasPart` | 10 |
| `dependsOn` / `author` / `object` | 各 1-9 |

内容有实质意义（`LLM Wiki 与 RAG 的区别 --relatedTo--> LLM Wiki`），是读正文推的关联，
wikilink 里没有。对 Lint 的「缺交叉引用」检查有用。

**但它不认 wikilink** —— `[[X]]` 那一层无论如何都得 agent 自己灌。

## 为什么会这样：需求正好相反

抽取器不是做得不好，是**用错了场景**。Knowledge Graph 开关的官方说明是
**"Extract people, projects, and dates"** —— 它为会议记录、邮件这类非结构化文档设计，
价值在于从正文里发现藏着的实体，挖得越全越是优点。但 wiki 页不是这种文档：

| | 普通文档（抽取器的场景） | wiki 页 |
|---|---|---|
| 实体在哪 | 藏在正文里，要发现 | frontmatter 已写死，一文件一实体 |
| 名字 | 抽取器猜 | 文件名就是名字 |
| category | 抽取器判 | frontmatter 的 `type` 定了 |
| 正文里的术语 | 挖出来是优点 | **不该成为独立实体** |

于是「发现能力」变成「过度发现」：实验 ③ 里一个 `The Schema.md` 炸出
`Raw sources`、`AGENTS.md`、`file_rag_search`、`index.md` 一堆碎片节点，
它们不对应任何文件，却混进图谱把 23 页的干净结构冲垮。

> 抽取器是**发现工具**；这个 wiki 不需要发现，需要**忠实登记**。
> 用发现工具做登记，只会把已经清晰的结构搅乱。

而且「自动」也没省事：确定性方式一步到位（写页时就知道名字和 category，直接
`kg_add`）；自动抽取要先清碎片、改 category、修命名、重灌边 —— **善后比手动建还费劲**。

## 一个额外的实验：对 `raw/` 开 KG

`raw/` 是真正的非结构化文档（官方博客、规范原文），理论上正是抽取器的场景。
试过一次，目标是拿一张「素材里提到了哪些实体」的清单来做缺页检测。

结果：**191,067 tokens 抽出 130 个实体，但恰好漏掉了要找的那两个。**

原文里 `AgentCore Identity` 出现 6 次、`AgentCore Memory` 3 次，都有专门段落描述职责 ——
抽取器一个都没抽到。它抽到的是 `Asana`、`Jira`、`Slack`、`Zendesk`（第三方集成示例）、
21 个 `Person`（博客作者名）、20 个 `Organization`（背书客户）。

原因是它按「文中是否显著」抽：`Slack` 作为集成示例反复出现所以显著；
`AgentCore Identity` 藏在「Outbound Auth, powered by AgentCore Identity」这种从句里
所以不显著 —— 但**后者才是族成员**。

**换成结构提取就对了**：官方文档的服务清单是一张表格，抓取后被压平成
「表头 + 连续短行」。按这个结构提取，13 个服务一个不漏、零 token。这个方法做进了
`wiki_lint` 的第 14 项「缺页候选」。

> **结构比语义可靠。**

## 关掉 KG 不影响已有的图

一个容易担心的点：关掉开关，`context` 里的知识图谱还看得到吗？

**看得到。** 实测 `kg_enabled: 1 → 0` 前后：

```
wiki 实体   22 → 22
linksTo 边  115 → 115
全部边      225 → 225
```

四个数字一个没动。那个开关只管**扫描时要不要自动抽取**，图谱面板读的是全库数据，
不按文件夹开关过滤。

所以关掉之后：已有的图照常展示、`kg_search` 照常查、`kg_add` 照常灌，
连之前抽出的 110 条语义边都留着。**唯一变化是不再自动抽取。**

## 如果你确实想要那层语义边

勾上 KG、配好规则跑一次也可以（模板见 [extraction-rules.md](extraction-rules.md)），
但要接受随后的六步校正 —— 已写进 `scaffold/AGENTS.md`：

```
rebuild 之前：从文件解析 wikilink，按「页名」固化（不记 node_id —— rebuild 后 id 全变）
rebuild 之后：
  1. 完整性  文件数 == 实体数？列出没产出实体的文件
  2. 名字    按 source_file 校验，不等就 kg_edit 改
  3. category 按 frontmatter type 校验
  4. summary  按 frontmatter summary 校验
  5. 重灌边   用固化的页名重查 node_id，灌回 linksTo
  6. 核验     文件边数 == 库里 linksTo 边数
```

**rebuild 是破坏性的** —— 它先删光该文件夹的实体再重抽，而边会随节点级联删除，
所以 agent 灌的边全没。

关键一条：**权威依据是实体的 `source_file` 属性，不是抽取器起的名字。**
名字会偏，`source_file` 不会。
