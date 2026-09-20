# 定时任务 prompt

三件事，只有一件适合做成排程：

| | 谁做 | 频率 | 为什么 |
|---|---|---|---|
| **补边** | **排程** ✅ | 每天 | 兜底「写页即同步」漏灌的边 —— 这个漏洞不会自愈，页面在图里孤立，`kg_search` 就找不到关联。所需工具在排程里全部验证可用 |
| **完整 Lint** | 手动（对话或终端脚本） | 想看的时候 | `wiki_lint` 是设备 MCP，**排程加载不到**（见下方限制）。排程只能发个提醒 |
| **索引同步** | 不做 | — | 同步管道自己在跑（实测索引时间会自动往后走）；而且排程侧调 `index_directory` 会 401，检测到落后也修不了。要建还得开 `allow_unscoped_write_tools` —— 不值 |

**主路径是「写页即同步」**（见文末）—— agent 写完页就该把边灌好。排程只是兜底。

> ### ⚠️ `wiki-inspect` MCP 在排程里用不了
>
> **实测**：排程运行环境加载不到设备上的 MCP skill，报
> `Skill 'wiki_inspect' not found`。遥测也印证了这点 —— `wiki_lint` 总共
> 被调用 7 次、`wiki_edges` 37 次，**排程会话里都是 0 次**。
>
> 而且这不是权限问题，开任何 flag 都解不了：工具在那个环境里不存在。
> 顺带两条也堵着：
> - `run_python(tools=[...])` 只能注入**排程 policy 已授权**的工具，包装不了
> - `load_skill` 暴露的工具必须作为独立工具调用，且仍要 policy 授权
>
> **所以排程任务只能用 Quick 自带工具。** 排程里验证可用的有：
> `run_python`（306 次）、`update_feed`（118）、`skip_cycle`（117）、
> `load_skill`（69）、`file_rag_status`（64）、`folder_list`（56）、
> `kg_search`（56）。
>
> `wiki-inspect` 的位置是**交互式 Lint** —— 你手动跑那种全量检查（46 页 187 边、
> 9 项确定性检查）。排程里做的是轻量比对，自带工具够用。
>
> 另有一个平台侧的限制：`file_rag_status` 在新版被判为 write 工具，而它无参数、
> 加不了条件，所以**新建排程时授不进 tool_policy**（旧排程里它调用成功过 64 次，
> 说明这是版本行为变化）。要用它就得开 `allow_unscoped_write_tools` ——
> 那个 flag 授的是「所有归 write 且无条件的工具」，范围会随平台新增工具而扩大，
> 用在无人值守任务上要想清楚。

> ⚠️ **这些任务只处理已有的 wiki 页，不摄入新素材** —— 这是有意的。
> 定时任务无人值守，不该让它自动消费刚进 `raw/` 的东西：素材正文和你的
> 指令走同一条通道，被投毒的内容可以影响 agent 行为。**新素材先手动跑一次
> Ingest，看清它做了什么，再决定要不要纳入自动化。**
> 见 [SECURITY.md](../SECURITY.md)。

---

## 为什么需要这个任务：抽取管线不产边

Quick 的本地文件抽取只产 entity，**不产对应 wikilink 的边**。这是管线行为，
不是配置问题 —— 在 `special_instructions` 里写明「每个 `[[X]]` 建一条
relation=linksTo 的边」也不生效。

`special_instructions` 是附加到抽取 prompt 后面的文字 —— 它能改「抽什么、怎么归类」，
因为那些是 LLM 的判断；但改不了管线的行为。所以 wikilink 必须经 `kg_add` 显式灌入。

## 关键机制：`run_python` 可以注入工具

整个同步逻辑能放在 Quick 内部完成，靠的是 `run_python` 的一个参数：

```python
run_python(
  code='...',                                    # 解析、比对、调用都在这段里
  tools=["kg_search", "kg_add", "kg_edit"]       # ← 注入工具
)
```

`tools` 一声明，这些工具就变成 Python 命名空间里的**同步函数**，返回解析好的 dict，
可以直接循环、判断、组合：

```python
pages = parse_wiki_files(d)              # 解析 frontmatter + wikilink
for name in pages:
    hit = kg_search(query=name)          # 查云端图谱里的现状
    if len(hit["entities"]) > 1:
        conflicts.append(name)           # 同名冲突 → 留给人裁定
        continue
    ...
kg_add(nodes=..., edges=...)             # 批量写
```

于是「解析文件 → 查图谱现状 → 算差集 → 写入」在一次调用里闭环，**数据不经过对话上下文**。
不传 `tools` 的话这些函数不在命名空间里，会报 `NameError`。

> ⚠️ **闭环归闭环，`kg_add` 的写入仍要分批。** 解析和比对可以一轮算完几百页，
> 但灌边时别把几十页塞进一次 `kg_add` —— 前端图谱面板大批量加载有上限，会画不出。
> 按源文件分批（每批 10~15 页），一批一个 `kg_add`。

**这也是为什么不需要外部脚本：agent 自己就是编排层。**

> **两个限制。** ① 只能注入 Quick **自带**的工具 —— 设备上的 MCP 工具
> （`wiki_lint` 那些）注入不了，实测报
> `wiki_index_status not permitted by this scheduled task's tool policy`。
> ② 排程里只能注入**该排程 policy 已授权**的工具，包装不能绕过授权。
>
> 所以这个机制适合**交互会话**里的批量操作。排程任务用它的话，要注入的工具
> 得先授进 policy —— 那时直接调也行，包装没有额外好处。

## 两条必须写进 prompt 的规矩

**① 用 `node_id` 而不是名字指定边的两端**

`kg_add` 的名字解析是模糊的，有两种失效模式：

- **模糊匹配**：库里没有名为 `AgentCore Gateway` 的实体（精确查询无结果），
  但它被吸收进了既有的 `AgentCore Gateway (MCP)` —— 名字不同也会被匹配走
- **同名分裂**：两个精确同名的实体（一个来自网页抽取、一个是 wiki 页），
  单独补一条边时挂到了错的那个

第一批灌图时不容易发现，因为节点和边同批写入、名字解析用的是刚创建的节点。
但**增量同步恰好是「单独补边」的场景**，所以这个坑一定会遇到。

解法：先 `kg_search` 拿真实 `node_id`，用 `from_id` / `to_id` 精确指定。
挂错了可以 `kg_edit(delete_edges=...)` 删掉重来（已验证）。

**② 同名多候选就报出来等人裁定**

「这两个同名实体是不是一回事」是语义判断，不该让它自己猜。报出来，等人决定合并还是改名。

---

## 任务一：索引同步（机械任务）

**Schedule**：每小时
**Tool policy**：`core`（含 `folder_list`）+ `file_rag_status` + `skip_cycle` + `update_feed`

判断「索引是否跟得上盘上改动」。**只检测，不触发索引** —— 实测从排程侧调
`index_directory` 会 401 失败，而失败时它仍可能返回成功消息，那比不做更糟。

全部用 Quick 自带工具，不依赖 MCP、不用 `run_python`。

> **`file_rag_status` 在新版排程里授不进 policy**（判 write、无参加不了条件）。
> 要么开 `allow_unscoped_write_tools`，要么这个任务建不出来 —— 见上方限制说明。
> 决定之前先在交互会话里手动跑一次同样的检测，看索引到底会不会落后：
> 如果基本不落后，这个排程的价值就要重新算。

### Prompt

```
每小时检查 Wiki-Vault 的索引是否跟得上盘上的改动。只检测，不触发索引。

第 1 步 —— 用 folder_list 递归列出这两个文件夹里的 .md，
  各自找出 mtime 最新的那一个：
    /Users/fiwa/Wiki-Vault/raw
    /Users/fiwa/Wiki-Vault/wiki
  只要「最新那一个的 mtime」和它的文件名 —— 不用统计文件总数、
  也不用把所有文件列出来。

第 2 步 —— load_skill("rag_indexing")，对这两个文件夹分别调 file_rag_status，
  取 rag_index_time。

第 3 步 —— 比「盘上最新 mtime」和「rag_index_time」：
  盘上更新 → 该文件夹索引过期

  都不过期 → update_feed 报「索引跟得上」(importance="fyi")
  有过期   → update_feed 报「索引落后，需要在设备上手动 sync」
             (importance="important")，每个过期文件夹列出：
               · 盘上最新改动时间 / 云端索引时间 / 差多久
               · 最新改动的是哪个文件
             给一个 choices 按钮："在设备上手动 sync 后重新检查"

不要调 index_directory。大多数小时会在第 3 步结束，无变化就安静报 fyi。
```

## 任务二：补边（可选兜底）

**Schedule**：每天一次
**前提**：只在「写页即同步」偶尔漏了的情况下需要 —— 正常路径下它每次都报「无事可做」

### Prompt

```
补 ~/Wiki-Vault/wiki 里漏灌的 wikilink 边。

用 Quick 自带工具完成：file_read 读文件、kg_search 查图谱、kg_add 灌边。

第 1 步 —— 用 file_read 逐个读 wiki/ 下的 .md，解析出 [[wikilink]]。
  两条规则不能省：

  ① **跳过代码块和行内代码里的 [[X]]** —— 讲双链语法的页里那是示例，
     不是真链接。``` 围栏之间的、以及 `反引号` 之间的内容都要忽略。
  ② **同一对 (from, to) 只算一条** —— 同一条边在正文和「## 关联」小节
     常各出现一次，实测有 142 对重复。不去重会多数出上百条。

  另外：index.md 和 log.md 是元文件，它们的出链是导航（目录条目、
  记录引用），不算知识关联，跳过不解析。

  wikilink 变体要归一化：[[X|别名]] → X，[[X#章节]] → X，![[X]] → X。

第 2 步 —— 查图谱里现状，拿真实 node_id：
  对每个页名调 kg_search 查是否已有实体。
  ⚠️ 关键：灌边时必须用 from_id / to_id，不能用 from_name / to_name。
     kg_add 的名字解析是模糊的 —— 图里可能有同名但不同来源的实体，
     也可能把你的页名模糊匹配到一个名字略有差异的既有实体上，
     两种情况都会让边挂错节点。

第 3 步 —— 算差集：
  只灌图里还没有的边，已存在的跳过。一条都不缺就报「无事可做」并结束。

第 4 步 —— 灌入：
  kg_add(edges=..., source_type="local")
  每条边的 properties.reason 写 "wikilink in <文件名>"，让边可追溯到源文件。
  ⚠️ **差集大时按源文件分批灌，一批约 10~15 页，别一次 kg_add 灌几十页。**
     实测短时间内一次性灌几十页会让前端图谱面板画不出（大批量加载有上限）；
     分批逐簇灌则整张图正常渲染。正常情况差集很小（写页时就灌了），
     这条只在补历史欠账时才用得上。

停下问人的情况（不要自己决定）：
  - 某个页名在图里查到多个候选实体 → 列出来等我裁定
  - [[X]] 指向的文件不存在（死链）→ 报告，但不要灌这条边
    （否则会凭空建出一个空实体，把死链掩盖成正常节点）

最后报告：灌了几条边、几条死链、几项待裁定。
```

## 任务三：体检（LINT）—— 交互式，不是排程

**`wiki_lint` 在排程里跑不了**（MCP 加载不到，见上方限制说明），所以完整体检
是你**手动**发起的，不是定时任务。

### 手动 Lint（在 Quick 对话里发这段）

```
对 ~/Wiki-Vault 做知识库体检。只报告，不动手修。

第 1 步 —— wiki_lint(vault="~/Wiki-Vault", brief=True)
  它一次报完 9 项确定性检查（死链、孤儿页、frontmatter、index.md 一致性、
  type 取值、索引时效、文件夹注册、缺页候选、枢纽分布）。
  全绿约 80 字符；有问题再取完整结果看细节。

  ⚠️ 不要自己现场写这些检查 —— 数边要按 (from, to) 去重、要剥掉代码块里的
     `[[X]]` 语法示例，这两处很容易错。

第 2 步 —— 补 #10 的另一半：
  wiki_lint 的 #10 只给盘上 newest_mtime_epoch。用 file_rag_status 取
  rag_index_time，两个数一比判断索引有没有过期。

第 3 步 —— 图谱层用 kg_search 抽查（wiki_lint 查不了这层）：
  抽 3～5 个页名，确认有对应实体节点、节点上能看到 linksTo 边。
  别全查，费 token。
  ⚠️ kg_search 每节点最多回 3 条边 —— 看到 3 条不等于只有 3 条。
     准确边数用 wiki_hubs。

第 4 步 —— 补机器判断不了的 4 项（读页面内容）：
  ① 矛盾：两页对同一事实说法冲突
  ② 过期声明：被更新的素材取代了但没改的说法
  ③ 缺交叉引用：两页明显相关但没互链
  ④ 数据缺口：可以靠一次联网搜索补上的空白

报告要求：
- 每项给出具体页面名，不要只给数字
- 区分「真问题」和「设计如此」（wiki/sources/ 下的摘要页天然无入链，不算孤儿）
- 只报告不动手
```

### 或者：在终端跑独立脚本

同一套检查，不用开 Quick：

```bash
python3 skill/quick-wiki-ops/scripts/quick_wiki_lint.py --vault ~/Wiki-Vault
python3 skill/quick-wiki-ops/scripts/quick_wiki_lint.py --vault ~/Wiki-Vault --strict   # CI 用
```

脚本和 MCP 的检查项同源，结果应该一致 —— 不一致说明有一边的实现漂了。

### 想要定时提醒的话

排程做不了完整 Lint，但可以做一件轻量的事：**提醒你该跑 Lint 了**。

**Tool policy**：`core` + `update_feed` + `skip_cycle`

```
每周一次，用 update_feed 发一条提醒（importance="fyi"）：
「该跑一次 Wiki-Vault 体检了 —— 在对话里说『对 ~/Wiki-Vault 做知识库体检』，
  或在终端跑 quick_wiki_lint.py」
给一个 choices 按钮："现在就跑体检"，prompt 填上面那段完整的 Lint 指令。
```

这样点一下按钮就在**交互会话**里跑起来，MCP 可用，检查项完整。

## 任务四（可选）：生成分面索引页

多值元数据（`tags` / `status`）目录装不下，用一个自动生成的索引页承载。

**Schedule**：跟同步任务一起，或每天一次

### Prompt

```
扫描 /path/to/wiki 所有 .md 的 frontmatter，生成一个分面索引页
/path/to/wiki/概念索引.md，格式：

---
type: index
tags: [meta, facet]
summary: 按 type 和 status 分组的分面索引，用于替代 metadata 过滤。
---
# 概念索引

## status-superseded
以下页面已被取代：[[页A]] · [[页B]]

## tag-rag
[[页C]] · [[页D]]

（每个 tag 和每个 status 值各一个小节，小节标题用 tag-<值> / status-<值>
这种形式 —— 这些字符串本身可被全文检索命中）

写完后触发一次重新索引。
```

之后查「哪些页被取代了」就是：搜 `status-superseded` 命中索引页 → 顺 wikilink 走。

## 写页即同步（这是主路径）

按 Karpathy 的设计，wiki/ 由 LLM 完全拥有 —— 人读它，LLM 写它。既然写入全在
agent 手里，它就该在写完的同一个动作里把边灌好，不用等定时任务来发现。

放进写 wiki 页的 skill 或 prompt 里：

```
往 wiki 写页时，三步连着做完：

1. file_write 写 .md
   frontmatter 必须有 type / tags / status / summary。
   [[双链]] 只能指向真实存在的文件 —— 先确认页名，不要编造。

2. 立刻把这页的 wikilink 灌成边：
   kg_add(edges=[...], source_type="local")
   用 from_id / to_id（先 kg_search 拿 node_id），不要用名字。
   遇到同名实体多个候选 → 停下来报给我，不要自己挑一个。

3. 触发这个文件夹的重新索引。

三步都做完再回话，不要写完页就算完 —— 那样新页在图里是孤立的。
```

这样新知识落盘的同时就进了图，Query 循环立刻能用上。

**定时同步任务退为兜底**：捡上一步漏掉的（比如同名冲突暂停了、索引触发失败），
以及跑 LINT。它的第 0 步是 mtime 比对，正常情况下会直接判定「无变化」结束。

## 两件不能全信 agent 的事

1. **它可能报告「已触发重新索引」但实际没发生。** 这是静默失败 —— 放在无人值守的
   定时任务里会变成「每天报告成功，数据从没更新」。验证方法：用 `file_rag_status`
   看索引时间戳是否真的动了，**别信工具返回的成功消息**。（新版索引在云端，
   本机 `files` 表是空的，查不到时间戳。）

2. **它对检索排名的机制解释可能站不住。** 遇到过它把某个实体排第一归因于
   「连接度最高 → PageRank boost」，实际查下来度数并列最高的另一个实体并未被 boost。
   它不是在撒谎，是在用一个合理的机制解释一个它没有观测数据的现象。
