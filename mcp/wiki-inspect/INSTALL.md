# wiki-inspect 安装步骤

## Step 1 放 server 文件

```bash
mkdir -p ~/.quickwork/mcp-servers/wiki-inspect
cp server.py ~/.quickwork/mcp-servers/wiki-inspect/
```

## Step 2 注册到 Quick

两条路：**UI 导入**（省事）或**直接改配置文件**（可靠）。

---

### 路线 A：UI 导入

导入这个文件：

```
mcp/wiki-inspect/import-wiki-inspect.json
```

#### ⚠️ 一个文件只能放一个 server

**Quick 的导入器只读 `mcpServers` 里的第一个条目，其余会被静默丢弃。**

所以如果你的文件里有两项：

```json
{
  "mcpServers": {
    "run":          { ... },
    "wiki-inspect": { ... }
  }
}
```

导入会「成功」，但进去的是 `run`，`wiki-inspect` 根本没进 —— **看起来像失败，实际是导错了对象。**
本目录只提供单 server 的 `import-wiki-inspect.json`，要装多个就分多次导入。

#### 导入器认哪些字段

`name`、`description`、`command`、`args`、`url`、`headers`、`env`。

`mcpServers` 的 key 会被当成 server 名字（代码里 `name: i || e.name`），
所以带 `mcpServers` 包装比裸的单 server 定义更明确 —— 名字不用另外填。

---

### 路线 B：直接改配置文件（推荐）

配置文件在：

```
~/.quickwork/profiles/<你的-profile>/mcp_config.json
```

profile 目录名形如 `enterprise-xxxxxxxx-us-west-2`。不确定是哪个就跑：

```bash
ls -d ~/.quickwork/profiles/*/ | while read d; do
  [ -f "$d/mcp_config.json" ] && echo "$d"
done
```

**这条路不走导入器**，所以没有「只读第一个」的限制，一个文件里放多少 server 都行。

#### 已经有别的 server 时：注意逗号

JSON 的规则：**项与项之间要有逗号，最后一项后面不能有逗号。**

假设你原来只有一项：

```
"run": {
  ...
}          ← 这里原来没有逗号，因为它是最后一项
```

要在它后面加 `wiki-inspect`，**必须先给这个 `}` 补一个逗号**，变成 `},`。
漏了这一步就报格式错误 —— 这是最常见的原因。

加完长这样：

```json
{
  "mcpServers": {
    "run": {
      "command": "uv",
      "args": ["run", "--with", "fastmcp", "..."],
      "env": { "UV_HTTP_TIMEOUT": "120" }
    },
    "wiki-inspect": {
      "description": "Quick 上 LLM Wiki 的只读校验层",
      "command": "uv",
      "args": [
        "run",
        "--with",
        "fastmcp",
        "~/.quickwork/mcp-servers/wiki-inspect/server.py"
      ],
      "env": {
        "UV_HTTP_TIMEOUT": "120"
      }
    }
  }
}
```

#### 没有别的 server 时：直接覆盖

```bash
cp import-wiki-inspect.json ~/.quickwork/profiles/<你的-profile>/mcp_config.json
```

**注意这会覆盖掉文件里原有的全部 server。** `builder-mcp` 不用担心 —— Quick 默认就有，
不需要在这个文件里声明。

`UV_HTTP_TIMEOUT` 是给首次下载 `fastmcp` 留的余量，网络快的话可以把整个
`"env": { ... }` 删掉（删完注意前一项末尾不能留逗号）。

国内装 `fastmcp` 慢的话，可以自己加一个 `UV_DEFAULT_INDEX` 指向**你信任的**
pip 镜像 —— 默认配置里不预设第三方源。

#### 改完先验格式

```bash
python3 -c "import json; json.load(open('$HOME/.quickwork/profiles/<你的-profile>/mcp_config.json')); print('✅ 格式合法')"
```

报错就说明还有逗号或括号问题。

## Step 3 重启 Quick

配置只在启动时读，改完必须重启。

## Step 4 验证工具可用

在 Quick 对话里：

```
跑一次 wiki_lint
```

正常应该返回类似：

```
内容页 38 / 实体 38 / linksTo 172 / 需处理 0 项
```

四个工具都试一下：

```
wiki_lint(brief=True)          → 只要结论，省 token
wiki_edges(page="某个页名")     → 那一页的全部边，不受 3 条上限
wiki_index_status()            → 索引配置和时间戳
wiki_hubs()                    → 入链排名 + 网状/星形判定
```

## 排查

**导入「成功」但工具不出现** —— 最可能是导入了含多个 server 的文件，
Quick 只取了第一个。用 `import-wiki-inspect.json`（只含一项），或走路线 B 改配置文件。

**工具不出现** —— 检查三件事：

1. JSON 格式（用上面那条 `python3 -c` 验）
2. `server.py` 路径对不对：`ls ~/.quickwork/mcp-servers/wiki-inspect/server.py`
3. `uv` 装了没：`command -v uv`。没装的话 `brew install uv` 或
   `curl -LsSf https://astral.sh/uv/install.sh | sh`

**工具报「找不到注册了此 vault 的 profile 库」** —— 说明 `~/Wiki-Vault` 还没在
Quick 里注册成文件夹。先做 `SETUP.md` 的 Step 2。

**首次调用慢** —— `uv run --with fastmcp` 第一次要下载 fastmcp，之后有缓存就快了。
配置里的 `UV_HTTP_TIMEOUT: 120` 就是给这一次留的余量。

**报 `Failed to spawn: ~/.quickwork/... No such file or directory`** —— 配置里的 `~`
没被展开。`args` 是直接 spawn 进程、不过 shell 的，波浪号得由客户端展开。
Quick 会展开，所以在 Quick 里写 `~` 没问题；换成别的 MCP 客户端撞到这个错，
把那一项改成绝对路径（`echo $HOME` 看你的用户目录）。
