# wiki-inspect MCP Server

给 Quick 里的 agent 提供**只读内省层** —— 读 Quick 的索引状态，补上内置工具的三处缺口。

## 为什么需要它

Quick 内置的 `kg_*` 工具足够读写图谱，但有三处读不到：

| 缺口 | 后果 |
|---|---|
| 边的元数据 | 无法核对边的溯源信息 |
| 索引时间戳 | 无法判断索引是否滞后 |
| `kg_search` 的 edges 有 **3 条上限** | 枢纽页的边被截断，数不准 |

此外，让 agent 每次现场写校验代码，结果不稳定。这个 server 把校验逻辑固定下来。

## 四个工具（全部只读）

```
wiki_lint(vault="~/Wiki-Vault", brief=False)
```

12 项确定性检查：死链、孤儿页（含豁免清单）、frontmatter 完整性、`index.md` 一致性、
边一致性、文件↔实体完整性、来源可疑的实体、实体名污染、同名实体、category 合规、
索引时效、来源不明的边，以及**缺页候选**。

**缺页候选**扫 `raw/` 素材里被结构化列为族成员（表格第一列、列表项粗体开头）
但 wiki 里没有页的名字。只用结构信号，不用语义猜测 —— 每一项都附出现次数和源文件，
建不建页由 agent 判断。

`brief=True` 只返回结论和问题项，全绿时约 136 字符（完整版 2126）。
先用 brief 看有没有问题，有问题再取完整结果。

```
wiki_edges(page=None, vault="~/Wiki-Vault")
```

读全量边，**不受 3 条上限**。给 `page` 只返回和它相关的边，不给则返回全库统计
（按 relation 分组 + `linksTo` 里缺 `reason` 的条数）。

```
wiki_index_status(vault="~/Wiki-Vault")
```

读文件夹注册配置和索引时间戳。**触发重新索引后用这个确认** ——
工具返回的成功消息不足以证明索引真的跑完了。

```
wiki_hubs(limit=15, vault="~/Wiki-Vault")
```

按入链数排名找枢纽页，同时报零入链的页，并判断整体是**网状**还是**星形**
（入链过半集中在前 3 页 = 星形，说明其余页多是各自连主页、彼此不互链）。

从文件解析、不查库 —— 不受 3 条边上限影响，也不依赖边有没有灌进图谱。
Lint 时用来判断结构健康：核心概念应该是枢纽，新页入链少才正常。

输出形如：

```
结构：网状（前 3 页占入链 26%）

Model Context Protocol      入 19  出 15   concept   ← 跨簇枢纽
AWS Agent Registry          入 14  出 10   entity
Agent2Agent                 入 11  出 12   concept

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
    "UV_HTTP_TIMEOUT": "120"
  }
}
```

profile 目录名形如 `enterprise-xxxxxxxx-us-west-2`，看 `~/.quickwork/profiles/` 下
哪个注册了你的 vault。国内网络装 `fastmcp` 慢的话，可以在 `env` 里加一个
`UV_DEFAULT_INDEX` 指向你信任的 pip 镜像。

完整步骤和排查见 [INSTALL.md](INSTALL.md)。

**③ 重启 Quick**，然后在对话里确认工具可用：

```
跑一次 wiki_lint
```

## 边界

- **查不了 5 项**，那些只有 LLM 能做：矛盾、过期声明、缺页、缺交叉引用、数据缺口。
  这 5 项交给 agent 自己判断（`AGENTS.md` 的 Lint 清单里有）。
- 工具设计成「结论 + 按需展开」：`brief=True` 给结论，`items` 截断在 40 条、
  `wiki_edges` 截断在 200 条 —— 无条件倒出全部细节反而更费 token。

## 和 quick-wiki-ops skill 的关系

两者并存，各服务不同的调用方：

| | 给谁用 | 形态 |
|---|---|---|
| `wiki-inspect` MCP | **Quick 里的 agent** | 工具调用 |
| `quick-wiki-ops` skill | **Claude Code** | 操作手册 + 独立脚本 |

校验逻辑同源（`quick_wiki_lint.py` 和 `server.py` 里的检查项一致），
两边跑出来的结果应该相同 —— 不同就说明有一边的实现漂了。

## 安全边界

| | |
|---|---|
| **只读（引擎强制）** | 数据库以 `mode=ro` 打开 —— 写操作在 SQLite 层面就被拒，不是靠代码自觉。另加授权回调拒绝 `ATTACH` / `DETACH`（`mode=ro` 不挡这两个，而 `ATTACH` 能创建新库文件）。写操作走 `kg_add` / `kg_edit` / `file_write`，让 Quick 维护索引和计量 |
| **不执行、不联网** | 无 `eval` / `exec` / `subprocess` / `pickle`，不发任何网络请求。依赖只有 `fastmcp` 一个第三方包，其余全是标准库 |
| **SQL 全参数化** | 没有一处把变量拼进 SQL 字符串，参数一律 `?` 绑定 |
| **访问范围收窄** | 只读三处：Quick 的索引库（`mode=ro`）、`<vault>/wiki/**/*.md`、`<vault>/raw/**/*.md`。不碰其它任何路径 |
| **`vault` 参数有闸** | 必须存在 `wiki/` 子目录、且该目录（或其子目录）在 Quick 里注册过。否则拒绝 |

最后一条是特意加的。`vault` 由 agent 填，而 agent 的输入可能来自 `raw/` 里的
**不可信素材** —— 如果不校验，一段藏在素材里的指令就能让工具去读 vault 之外的
目录并把内容回传。两道闸把可达范围锁在注册过的 vault 内。

（`rglob` 默认不跟随符号链接目录，所以 `wiki/` 里放一个指向 `/etc` 的软链也扫不出东西。）

### 它不会做的事

如果要过安全评审，这几条可以直接核对源码：

- 不写任何文件、不建目录、不改权限、不改环境变量
- 不开 socket、不发 HTTP、不做 DNS 查询
- 不起子进程、不加载动态库、不反序列化
- 不读 vault 和 Quick 索引库之外的路径，不读 `.md` 以外的文件类型
- 不修改 Quick 的任何状态 —— 装上和卸掉，Quick 的行为完全一样
