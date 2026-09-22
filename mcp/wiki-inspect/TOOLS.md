# wiki-inspect MCP Server

给 Quick 里的 agent 提供**只读校验层** —— 全量扫 vault 里的 `.md`，补上内置工具的三处缺口。

## 为什么需要它

Quick 内置的 `kg_*` 工具足够读写图谱，但有三处不够：

| 缺口 | 后果 |
|---|---|
| `kg_search` 的 edges 有 **3 条上限** | 枢纽页的边被截断，边数永远数不准 |
| 没有「全量扫一遍」的工具 | 死链、孤儿页、frontmatter 缺失要逐页问，既慢又漏 |
| agent 现场写校验代码结果不稳定 | 常见错法：边没按 `(from, to)` 去重、没剥掉代码块里的 `[[X]]` 语法示例、sandbox 拦住读盘 |

**这个 server 全部从 `.md` 文件解析，不查索引库。** 新版 Quick 把索引、chunk、
实体、`kg_add` 灌的节点和边都放在云端 Quick Space，本机 `knowledge_v1.db` 里跟
vault 有关的表都是 0 行 —— 唯一还读本机库的是权限层（`allowed_folders.db`，
判断文件夹注册状态）。

分工：

| 层 | 查什么 | 用什么 |
|---|---|---|
| **文件层** | 死链、孤儿页、frontmatter、`index.md` 一致性、`type` 有没有放对目录、缺页候选、枢纽分布、准确边数 | 本 server |
| **注册层** | 文件夹注册了没、agent 有没有读写权限、`sync_status` 同步完没 | 本 server（`wiki_index_status`） |
| **图谱层** | 实体在图谱里有没有节点、`kg_add` 灌的边写进去没 | **`kg_search`** —— Quick 内置，本机查不了 |
| **索引层** | 索引建到哪一步、什么时候建的、chunk 数 | **`file_rag_status`** —— 同上 |

## 四个工具（全部只读）

```
wiki_lint(vault="~/Wiki-Vault", brief=False)
```

9 项确定性检查，全部从 `.md` 解析（编号沿用历史序号，不连续）：

| # | 检查 | 级别 |
|---|---|---|
| 1 | 死链 —— `[[X]]` 指向不存在的页 | error |
| 2 | 孤儿页 —— 零入链（豁免 `sources/`；当天新建或 `status: stub` 单列为「待接线」） | warn |
| 3 | frontmatter 完整性 —— `type` / `tags` / `status` / `summary` 缺没缺 | warn |
| 4 | `index.md` 一致性 —— 盘上的页和目录登记的对不对得上 | warn |
| 9 | `type` 取值 —— 是四类之一，且和所在子目录对应（`concept` → `concepts/`） | warn |
| 10 | 索引时效 —— 报盘上 `newest_mtime`；**另一半要你用 `file_rag_status` 取 `rag_index_time` 来比** | info |
| 13 | 文件夹注册 —— 读权限层，没注册报 error | info / error |
| 14 | 缺页候选 —— 见下 | info |
| 15 | 枢纽分布 —— 入链排名前几页 | info |

**缺页候选**扫 `raw/` 素材里被结构化列为族成员（表格第一列、列表项粗体开头）
但 wiki 里没有页的名字。只用结构信号，不用语义猜测 —— 每一项都附出现次数和源文件，
建不建页由 agent 判断。

`brief=True` 只返回结论和问题项，全绿时约 80 字符。先用 brief 看有没有问题，
有问题再取完整结果。

```
wiki_edges(page=None, vault="~/Wiki-Vault")
```

从 `.md` 解析全部双链，**不受 `kg_search` 的 3 条上限**。给 `page` 只返回该页的
出链和入链（元文件 `index` / `log` 单独查时也能看到出链，虽然它们不计入全局边数）；
不给则返回全量边和死链清单。

```
wiki_index_status(vault="~/Wiki-Vault")
```

报文件夹的**注册状态** —— 读本机权限层 `allowed_folders.db`：注册了哪些路径、
agent 有没有读写权限、`sync_status` / `storage_type`、添加时间，以及盘上有多少 `.md`。

**注册 ≠ 建了索引。** 添加文件夹只给权限，索引由客户端的文件同步管道另外建。
索引进度、chunk 数、索引时间戳都在云端 —— 那些用 `file_rag_status` 查。

```
wiki_hubs(limit=15, vault="~/Wiki-Vault")
```

按入链数排名找枢纽页，同时报零入链的页，并判断整体是**网状**还是**星形**
（入链过半集中在前 3 页 = 星形，说明其余页多是各自连主页、彼此不互链）。

Lint 时用来判断结构健康：核心概念应该是枢纽，新页入链少才正常。

输出形如：

```
结构：网状（前 3 页占入链 19%）

LLM Wiki                    入 13  出 8    concept   ← 跨簇枢纽
AWS Agent Registry          入 12  出 10   entity
AgentCore Runtime           入 11  出 7    entity

零入链 (0):
```

> **数边有两种口径。** 三个工具报的 `total_edges` 都是**按 `(from, to)` 去重后**的
> 唯一有向边数，且解析前剥掉了代码块和行内代码（讲双链语法的页里 `` `[[X]]` `` 是
> 示例，不算链接）。自己按 `[[` 硬数出来的会更大 —— 那是含重复、含示例的原始
> wikilink 数。三个工具应该给出**完全相同**的数字，不一致就说明有 bug。

## 安装

**① 放到 Quick 的 mcp-servers 目录**

```bash
mkdir -p ~/.quickwork/mcp-servers
cp -R mcp/wiki-inspect ~/.quickwork/mcp-servers/
```

**② 注册到 Quick 的 MCP 配置**

编辑 `~/.quickwork/profiles/<你的-profile>/mcp_config.json`，在 `mcpServers` 里加一段：

```json
"wiki-inspect": {
  "command": "uv",
  "args": ["run", "--with", "fastmcp", "python", "-c",
           "import os,runpy; runpy.run_path(os.path.expanduser(\"~/.quickwork/mcp-servers/wiki-inspect/server.py\"), run_name=\"__main__\")"],
  "env": { "UV_HTTP_TIMEOUT": "120" }
}
```

> 路径的 `~` 由 Python 的 `os.path.expanduser` 展开，所以这份配置**任何人导入都能直接用**，
> 不需要替换用户名。（`uv run` 自己不展开 `~`，直接写 `~/...server.py` 会报
> `Failed to spawn`。）

profile 目录名形如 `enterprise-xxxxxxxx-us-west-2`，看 `~/.quickwork/profiles/` 下
哪个注册了你的 vault。国内网络装 `fastmcp` 慢的话，可以在 `env` 里加一个
`UV_DEFAULT_INDEX` 指向你信任的 pip 镜像。

完整步骤和排查见 [INSTALL.md](INSTALL.md)。

**③ 重启 Quick**，然后在对话里确认工具可用：

```
跑一次 wiki_lint
```

## 边界

- **图谱层查不了。** 实体在图谱里有没有节点、`kg_add` 灌的边写进去没 —— 那些在云端，
  用 `kg_search` 在 Quick 里核（随机抽 3～5 个页名查，别全查，费 token）。
- **索引状态查不了。** 索引进度、chunk 数、索引时间戳用 `file_rag_status`。
- **查不了 5 项**，那些只有 LLM 能做：矛盾、过期声明、缺页、缺交叉引用、数据缺口。
  这 5 项交给 agent 自己判断（`AGENTS.md` 的 Lint 清单里有）。
- 工具设计成「结论 + 按需展开」：`brief=True` 给结论，`items` 截断在 40 条 ——
  无条件倒出全部细节反而更费 token。

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
| **只读（引擎强制）** | 唯一读的库（`allowed_folders.db`）以 `mode=ro` 打开 —— 写操作在 SQLite 层面就被拒，不是靠代码自觉。另加授权回调拒绝 `ATTACH` / `DETACH`（`mode=ro` 不挡这两个，而 `ATTACH` 能创建新库文件）。写操作走 `kg_add` / `kg_edit` / `file_write`，让 Quick 维护索引和计量 |
| **不执行、不联网** | 无 `eval` / `exec` / `subprocess` / `pickle`，不发任何网络请求。依赖只有 `fastmcp` 一个第三方包，其余全是标准库 |
| **SQL 只有一条，且是常量** | 唯一的 SQL 是 `SELECT ... FROM allowed_folders`，没有一处把变量拼进去 |
| **访问范围收窄** | 只读三处：`allowed_folders.db`（`mode=ro`）、`<vault>/wiki/**/*.md`、`<vault>/raw/**/*.md`。不碰其它任何路径 |
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
- 不读 vault 和 `allowed_folders.db` 之外的路径，不读 `.md` 以外的文件类型
- 不修改 Quick 的任何状态 —— 装上和卸掉，Quick 的行为完全一样
