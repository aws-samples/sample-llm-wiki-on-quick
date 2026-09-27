# LLM Wiki on Amazon Quick

在 [Amazon Quick](https://aws.amazon.com/quick/) 桌面端跑一套 [Karpathy 的 LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) —— 不装向量数据库、不装 embedding 运行时、不装图数据库。

> **LLM Wiki 的思路是先编译，后查询。** 素材导入后 LLM 提前完成提取、整合、关联，产出一套互相链接的 markdown 维基，查询直接读它。新增资料时自动更新已有词条、标记冲突 —— 知识持续变厚，而不是每次从零推导。

![架构](docs/images/architecture.png)

> ⚠️ **动手前先读 [SECURITY.md](SECURITY.md)。** agent 会读取 `raw/` 里的素材（通常来自互联网），
> 并据此写文件、改知识图谱、执行代码。

## 这个仓库提供什么

| 路径 | 内容 |
|---|---|
| [`scaffold/`](scaffold/) | vault 目录骨架 + `AGENTS.md`（agent 的 instructions） |
| [`mcp/wiki-inspect/`](mcp/wiki-inspect/) | 只读校验 MCP server：`wiki_lint`、`wiki_edges`、`wiki_hubs` |
| [`prompts.md`](prompts.md) | 全部提示词：建 agent、Ingest、Query、Lint、定时任务 |
| [`docs/images/`](docs/images/) | 架构图（png / svg / drawio） |

## 快速开始

**前置**：Amazon Quick 桌面端，Pro 或以上订阅。

### 1. 铺骨架

```bash
git clone https://github.com/aws-samples/sample-llm-wiki-on-quick.git
mkdir -p ~/Wiki-Vault && cp -R sample-llm-wiki-on-quick/scaffold/ ~/Wiki-Vault/
```

```
~/Wiki-Vault/
├── AGENTS.md              agent 的 instructions
├── raw/                   素材（人放入，agent 只读）
│   ├── articles/  papers/  assets/
└── wiki/                  agent 维护
    ├── index.md           内容目录
    ├── log.md             操作日志
    ├── concepts/          抽象：模式、协议、方法
    ├── entities/          具体：产品、服务、人、工具
    ├── sources/           素材摘要页
    └── synthesis/         解读、对比、问答归档
```

### 2. 注册文件夹

**Settings → Capabilities → My Computer → Local Folders → Add folder**，先加根目录，再加两个子目录：

| # | 路径 | Agent access | Allow full file context | Always remember |
|---|---|---|---|---|
| 1 | `~/Wiki-Vault` | ✓ | ✗ | ✗ |
| 2 | `~/Wiki-Vault/raw` | ✓ | ✓ | ✗ |
| 3 | `~/Wiki-Vault/wiki` | ✓ | ✓ | ✓ |

- **Allow full file context**：建关键词 + 语义索引，`raw/` 和 `wiki/` 都开。
- **Always remember file information**：自动抽取实体进知识图谱，只在 `wiki/` 开 —— 不开就看不到图谱；`raw/` 不开，图谱只反映编译过的知识。

### 3. 安装 MCP

```bash
mkdir -p ~/.quickwork/mcp-servers
cp -R sample-llm-wiki-on-quick/mcp/wiki-inspect ~/.quickwork/mcp-servers/
```

在 Quick 里导入 `~/.quickwork/mcp-servers/wiki-inspect/import-wiki-inspect.json`，然后重启 Quick。详见 [mcp/wiki-inspect/README.md](mcp/wiki-inspect/README.md)。

### 4. 建 agent 和定时任务

按 [prompts.md](prompts.md) 的「创建 agent」建 LLM Wiki Agent，建完 publish；再按「定时任务」建每日体检。

## License

MIT-0，见 [LICENSE](LICENSE)。
