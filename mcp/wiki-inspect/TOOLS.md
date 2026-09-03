# wiki-inspect MCP Server

给 Quick 里的 agent 提供**只读内省层** —— 读 Quick 内部状态，做它自己做不到、或容易做错的那几件事。

## 为什么需要它

Quick 内置的 `kg_*` 工具足够读写图谱，但有三处硬缺口，实测都踩过：

| 缺口 | agent 的实际表现 |
|---|---|
| 读不到边的元数据 | 试过各种调用方式都拿不到，最后只能标注「这一项查不了，不是没问题」 |
| 读不到索引时间戳 | 误报「语义索引卡了 14.5 小时」，实际早已完成 |
| `kg_search` 的 edges 有 **3 条上限** | 枢纽页被截断。`Agent Card` 实际有 8 条边，只能看到 3 条 |

还有一处不是缺口而是可靠性问题：**agent 每次现场写校验代码都可能出新 bug**。实测把边的方向字段判成 `"out"`（实际是 `"outgoing"`），误报「图谱 0 条边、严重漂移」。

这个 server 把校验逻辑固定下来 —— 逻辑写死、测过、不会每次重新犯错。

## 四个工具（全部只读）

```
wiki_lint(vault="~/Wiki-Vault", brief=False)
```
12 项确定性检查：死链、孤儿页（含豁免清单）、frontmatter 完整性、`index.md` 一致性、
边一致性、文件↔实体完整性、来源可疑的实体、实体名污染、同名实体、category 合规、
索引时效、来源不明的边，以及**缺页候选**。

**缺页候选**这项值得单独说 —— 它扫 `raw/` 素材里被**结构化列为族成员**（表格第一列、
列表项粗体开头）但 wiki 里没有页的名字。用结构而非语义，因为实测过两条别的路都不行：

- **Quick 的抽取器**：花了 191067 tokens 抽出 130 个实体，但漏掉了原文里出现 6 次的
  `AgentCore Identity` 和 3 次的 `AgentCore Memory` —— 它按「文中是否显著」抽，
  于是挑走了 `Slack`/`Jira`（集成示例）和博客作者名，漏掉了表格里第 3、5 行的兄弟服务
- **前缀族启发式**（和已有页共享首词）：产出 74 项，大半是 `AgentCore AgentCore`、
  `Amazon EC`（截断）、`Model The`（语法碎片）这类垃圾

结构提取产出 20 项、全部有据可查（附出现次数和源文件），而同一份文档的服务清单表格
13 项一个不漏。**结构比语义可靠。**

`brief=True` 只返回结论和问题项 —— 全绿时约 **136 字符**，完整版 **2126 字符**。
先用 brief 看有没有问题，有问题再取完整结果。

```
wiki_edges(page=None, vault="~/Wiki-Vault")
```
读全量边，**不受 3 条上限**。给 `page` 只返回和它相关的边，不给则返回全库统计
（按 relation 分组 + `linksTo` 里缺 `reason` 的条数）。

```
wiki_index_status(vault="~/Wiki-Vault")
```
读文件夹注册配置和索引时间戳。**报告「已触发重新索引」之后应该用这个确认** ——
仅凭工具返回的成功消息不足以证明索引真的跑了。

```
wiki_hubs(limit=15, vault="~/Wiki-Vault")
```
按入链数排名找枢纽页，同时报零入链的页，并判断整体是**网状**还是**星形**
（入链过半集中在前 3 页 = 星形，说明其余页多是各自连主页、彼此不互链）。

从文件解析、不查库 —— 所以不受 3 条边上限影响，也不依赖边有没有灌进图谱。
Lint 时用来判断结构健康：核心概念应该是枢纽，新页/边缘页入链少才正常。

实测输出（38 页 / 172 边）：

```
结构：网状（前 3 页占入链 26%）

Model Context Protocol      入 19  出 15   concept   ← 跨簇枢纽
AWS Agent Registry          入 14  出 10   entity
Agent2Agent                 入 11  出 12   concept
A2A Specification           入  9  出  3   source

零入链 (1): A2A 委派端到端流程
```

## 安装

**① 放到 Quick 的 mcp-servers 目录**

```bash
mkdir -p ~/.quickwork/mcp-servers/wiki-inspect
cp server.py ~/.quickwork/mcp-servers/wiki-inspect/
```

**② 注册到 Quick 的 MCP 配置**

编辑 `~/.quickwork/profiles/<你的-profile>/mcp_config.json`，在 `mcpServers` 里加一段：

```json
"wiki-inspect": {
  "command": "uv",
  "args": ["run", "--with", "fastmcp",
           "~/.quickwork/mcp-servers/wiki-inspect/server.py"],
  "env": {
    "UV_DEFAULT_INDEX": "https://mirrors.aliyun.com/pypi/simple/",
    "UV_HTTP_TIMEOUT": "120"
  }
}
```

`UV_DEFAULT_INDEX` 是国内镜像，网络没问题的话可以去掉。profile 目录名形如
`enterprise-xxxxxxxx-us-west-2`，看 `~/.quickwork/profiles/` 下哪个含你的 vault
注册记录（`folders` 表里有 `~/Wiki-Vault`）。

**③ 重启 Quick**，然后在对话里确认工具可用：

```
跑一次 wiki_lint
```

## 收益实测

对比 agent 现场写校验（上一轮实际发生的多轮 `run_python` + 逐页 `kg_search` + 试错）：

| | 现场写 | 调 MCP |
|---|---|---|
| token（含报告） | 约 7900 | 约 2080 |
| token（只算中间过程） | 约 6700 | 约 880 |
| 耗时 | 多轮 LLM 往返，几秒起 | **14 ms** |
| `kg_expand` 试错 | 900 token 白花 | 不存在 |
| 逐页 `kg_search` 37 次 | 2200 token | 一次调用 |

省下的**主要不是「代码短了」**，而是试错、多轮往返、和中间结果占上下文。
（`run_python` 的 `tools=[...]` 本来就能让批量数据不进上下文，所以那部分不是新增收益。）

**注意反直觉的一点**：MCP 也可能更费 token —— 如果工具无条件倒出全部细节而
agent 只需要一句结论。所以设计成「结论 + 按需展开」：`brief=True` 给结论，
`items` 截断在 40 条、`wiki_edges` 截断在 200 条。

## 边界

- **只读。** 直写 Quick 的 SQLite 会绕过索引更新、`content_hash` 校验和 token 计量。
  写操作仍然走 `kg_add` / `kg_edit` / `file_write`。
- **查不了 5 项**，那些只有 LLM 能做：矛盾、过期声明、缺页、缺交叉引用、数据缺口。
  这 5 项交给 agent 自己判断（`AGENTS.md` 的 Lint 清单里有）。

## 和 quick-wiki-ops skill 的关系

两者并存，各服务不同的调用方：

| | 给谁用 | 形态 |
|---|---|---|
| `wiki-inspect` MCP | **Quick 里的 agent** | 工具调用 |
| `quick-wiki-ops` skill | **Claude Code** | 操作手册 + 独立脚本 |

校验逻辑同源（`quick_wiki_lint.py` 和 `server.py` 里的检查项一致），
所以两边跑出来的结果应该相同 —— 不同就说明有一边的实现漂了。
