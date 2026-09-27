# wiki-inspect

给 Quick agent 用的只读校验工具。

## 安装

1. 拷贝目录：

   ```bash
   mkdir -p ~/.quickwork/mcp-servers
   cp -R mcp/wiki-inspect ~/.quickwork/mcp-servers/
   ```

2. 在 Quick 里导入 `~/.quickwork/mcp-servers/wiki-inspect/import-wiki-inspect.json`，或在 `~/.quickwork/profiles/<你的-profile>/mcp_config.json` 的 `mcpServers` 里加：

   ```json
   "wiki-inspect": {
     "command": "uv",
     "args": ["run", "--with", "fastmcp", "python", "-c",
              "import os,runpy; runpy.run_path(os.path.expanduser(\"~/.quickwork/mcp-servers/wiki-inspect/server.py\"), run_name=\"__main__\")"],
     "env": { "UV_HTTP_TIMEOUT": "120" }
   }
   ```

3. 重启 Quick。

## 工具

| 签名 | 作用 |
|---|---|
| `wiki_lint(brief=False)` | 8 项文件层检查：死链、孤儿页、frontmatter、`index.md` 一致性、`type` 目录、索引时效、缺页候选、枢纽分布 |
| `wiki_edges(page=None, for_kg=False)` | 双链关系；`for_kg=True` 返回去重、剥代码块、滤死链后的 `{pages, edges, dead}` |
| `wiki_hubs(limit=15)` | 入链排名、零入链页、网状 / 星形判断 |

## 安全边界

- 只读：不写文件、不读数据库，三个工具声明 `readOnlyHint`
- 不联网、不起子进程
- 只读 `~/Wiki-Vault/wiki/` 和 `~/Wiki-Vault/raw/` 下的 `.md`，路径写死，不跟随软链
