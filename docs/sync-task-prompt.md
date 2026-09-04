# 定时任务 prompt

两个任务：**同步**（把 `[[双链]]` 灌成边）和 **体检**（LINT）。可以合成一个，也可以分开。

---

## 为什么需要这个任务：抽取管线不产边

Quick 的本地文件抽取只产 entity，**不产 edge**。这是管线行为，不是配置问题 ——
我在 `special_instructions` 里明确写过「每个 `[[X]]` 建一条 relation=linksTo 的边」，
重抽之后 `edges` 表仍然是空的。

对照：全库有一万多条边（从 Slack / 邮件 / 日历抽的），说明建边机制本身正常，
只是**本地文件这条管线不走它**。

`special_instructions` 是附加到抽取 prompt 后面的文字 —— 它能改「抽什么、怎么归类」，
因为那些是 LLM 的判断；但改不了管线的行为。所以关系必须经 `kg_add` 显式灌入。

## 关键机制：`run_python` 可以注入 MCP 工具

整个同步逻辑能放在 Quick 内部完成，靠的是 `run_python` 的一个参数：

```python
run_python(
  code='...',                                    # 解析、比对、调用都在这段里
  tools=["kg_search", "kg_add", "kg_edit"]       # ← 注入 MCP 工具
)
```

`tools` 一声明，这些工具就变成 Python 命名空间里的**同步函数**，返回解析好的 dict，
可以直接循环、判断、组合：

```python
pages = parse_wiki_files(d)              # 解析 frontmatter + wikilink
for name in pages:
    hit = kg_search(query=name)          # 查库里现状
    if len(hit["entities"]) > 1:
        conflicts.append(name)           # 同名冲突 → 留给人裁定
        continue
    ...
kg_add(nodes=..., edges=...)             # 批量写
```

于是「解析 → 查现状 → 算差集 → 写入」在一次调用里闭环，**数据不经过对话上下文** ——
几页和几百页都是一轮。不传 `tools` 的话这些函数不在命名空间里，会报 `NameError`。

**这也是为什么不需要外部脚本：agent 自己就是编排层。**

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

## 任务一：同步 wiki 图谱

**Schedule**：每天一次，或半小时一次（有「先检查」那步，无变化时成本极低）
**Capabilities**：knowledge_graph 相关工具

### Prompt

```
同步 /path/to/wiki 的 wikilink 图谱到知识图谱。

用 run_python 完成，必须传 tools=["kg_search", "kg_add", "kg_edit"]
（不传的话这些函数不在命名空间里，会报 NameError）。

步骤：

第 0 步 —— 先判断要不要干活：

  比对每个 .md 的 mtime 和库里的 kg_index_time / rag_index_time。
  没有任何文件比索引新 → 报告「无变化」并结束，不要往下做。
  有 → 只处理这些文件，不必全量。

  （抽取要花 token；这一步做轻了，任务频率才能设得激进。
    正常情况下写页时已经同步过了，所以这个任务大多数时候会在这里就结束）

第 1 步 —— 解析文件：
  读每个 .md 的 frontmatter（type / tags / status / summary）和正文里的 [[wikilink]]。
  wikilink 变体要归一化：[[X|别名]] → X，[[X#章节]] → X，![[X]] → X。
  同一对 (from, to) 出现多次只算一条边（正文和「## 关联」小节常各出现一次）。

第 2 步 —— 查库里现状，拿真实 node_id：
  对每个页名调 kg_search 查是否已有实体。
  ⚠️ 关键：灌边时必须用 from_id / to_id，不能用 from_name / to_name。
     kg_add 的名字解析是模糊的 —— 库里可能有同名但不同来源的实体，
     也可能把你的页名模糊匹配到一个名字略有差异的既有实体上，
     两种情况都会让边挂错节点。

第 3 步 —— 算差集：
  只灌库里还没有的边，已存在的跳过。

第 4 步 —— 灌入：
  kg_add(nodes=..., edges=..., source_type="local")
  每条边的 properties.reason 写 "wikilink in <文件名>"，让边可追溯到源文件。

停下问人的情况（不要自己决定）：
  - 某个页名在库里查到多个候选实体 → 列出来等我裁定
  - [[X]] 指向的文件不存在（死链）→ 报告，但不要灌这条边
    （否则会凭空建出一个空实体，把死链掩盖成正常节点）

最后报告：灌了几个节点、几条边、几条死链、几项待裁定。
```

## 任务二：体检（LINT）

**Schedule**：每周一次
**Capabilities**：knowledge_graph 相关工具

### Prompt

```
对 /path/to/wiki 做知识库体检，用 run_python 解析文件、用 kg_search / kg_stats
读图谱，逐项检查并报告：

① 死链：文件里的 [[wikilink]] 指向了不存在的 .md 文件
② 孤儿页：库里零入边零出边的实体
③ 文件↔实体一致性：有 .md 文件但库里没有对应实体，或反之
④ 边一致性：文件里解析出的 wikilink 数量 vs 库里 linksTo 边数量
   （这是最重要的一项 —— 不一致说明图谱和文件系统漂移了）
⑤ 元数据完整性：frontmatter 缺 summary / status 的页面
⑥ 身份冲突：同名实体多个候选

报告要求：
- 每项给出具体页面名，不要只给数字
- 区分「真问题」和「设计如此」（例如 raw/ 素材类页面天然无入链，不算孤儿）
- 不要自己动手修，只报告

⚠️ 注意 ④ 的坑：kg_search 返回的 edges 有 3 条上限，度数高的页会被截断。
   要准确数边，得对每个页面单独查、或者用外部脚本读库（见 kg-sync.py --lint）。
```

## 任务三（可选）：生成分面索引页

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
   定时任务里会变成「每天报告成功，数据从没更新」。验证方法：查 `files` 表的
   `kg_index_time` / `rag_index_time` 是否真的更新了（`kg-sync.py --lint` 的第 ⑦ 项）。

2. **它对检索排名的机制解释可能站不住。** 遇到过它把某个实体排第一归因于
   「连接度最高 → PageRank boost」，查库发现度数并列最高的另一个实体并未被 boost。
   它不是在撒谎，是在用一个合理的机制解释一个它没有观测数据的现象。
