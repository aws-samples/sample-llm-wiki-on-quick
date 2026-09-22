# LLM Wiki on Amazon Quick

在 [Amazon Quick](https://aws.amazon.com/quick/) 桌面端跑一套 [Karpathy 的 LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) —— 不装向量数据库、不装 embedding 运行时、不装图数据库。

> **LLM Wiki 的思路是先编译，后查询。** 素材导入后 LLM 提前完成提取、整合、关联，产出一套互相链接的 markdown 维基，查询直接读它。新增资料时自动更新已有词条、标记冲突 —— 知识持续变厚，而不是每次从零推导。

![架构](docs/images/architecture.png)

> ⚠️ **动手前先读 [SECURITY.md](SECURITY.md)。** 这套方案让 agent 读取你放进
> `raw/` 的素材（通常来自互联网），并据此写文件、改知识图谱、执行代码。
> 那份文档说明这条链路的风险和四条控制建议 —— 只摄入可信来源、把 `raw/`
> 当不可信输入、Agent access 按最小必要给、vault 里不放凭证和敏感数据。

## 这个仓库提供什么

| 目录 | 内容 |
|---|---|
| **`scaffold/`** | 目录骨架 + `AGENTS.md`（schema 层：约定 + 三个操作 + 校验规程），`cp -R` 就能用 |
| **`agent/`** | 把 `AGENTS.md` 做成常驻 Quick agent 的完整说明 |
| **`mcp/wiki-inspect/`** | 只读内省 MCP：4 个工具补上 Quick 内置工具读不到的三处 |
| **`skill/quick-wiki-ops/`** | Claude Code 的操作手册 + 独立校验脚本（与 `wiki_lint` 同一套确定性检查） |
| **`examples/`** | 一次真实运行的完整产出：62 页 / 316 条边 / 零死链 |
| **`docs/`** | 抽取规则模板、定时任务 prompt、架构图源文件 |

## 快速开始

**前置**：Amazon Quick 桌面端，Pro 或以上订阅。

### 1. 铺骨架

```bash
git clone https://github.com/aws-samples/sample-llm-wiki-on-quick.git
cp -R sample-llm-wiki-on-quick/scaffold/ ~/Wiki-Vault/
```

```
~/Wiki-Vault/
├── AGENTS.md              schema 层：约定 + 三个操作 + 校验规程
├── raw/                   不可变素材（人写，LLM 只读）
│   ├── articles/  papers/  assets/
└── wiki/                  LLM 拥有
    ├── index.md           内容目录
    ├── log.md             操作日志
    ├── concepts/          抽象：模式、协议、方法
    ├── entities/          具体：产品、服务、人、工具
    ├── sources/           素材摘要页
    └── synthesis/         解读、对比、问答归档
```

### 2. 注册文件夹

**Settings → Capabilities → My Computer → Local Folders → Add folder**

| # | 路径 | Agent access | Allow full file context | Always remember |
|---|---|---|---|---|
| 1 | `~/Wiki-Vault` | **✓** | ✗ | ✗ |
| 2 | `~/Wiki-Vault/raw` | ✓ | **✓** | ✗ |
| 3 | `~/Wiki-Vault/wiki` | ✓ | **✓** | ✗ |

`Indexing` 下的两个开关，作用不同：

| 开关 | 作用 | 建议 |
|---|---|---|
| **Allow full file context for enhanced searching** | 建关键词 + 语义索引 | **开** |
| **Always remember file information** | 自动抽取实体和边进知识图谱 | **不开**（见下） |

**添加文件夹 ≠ 建索引。** 只添加只授予 agent 读写权限，索引是独立的第二步 ——
不开 Indexing，`file_rag_search` 会直接报「folder is not indexed」。

**第二个开关不开。** 知识图谱**要用**，但不靠自动抽取 —— 由 agent 在写页时用 `kg_add`
显式灌。wiki 页的实体名、类型、摘要都由 frontmatter 定死了，一文件一实体；
自动抽取会把正文里的普通术语也抽成 `Defined Term` 节点（实测：一段讲负载均衡的填充
文字产出了「缓存层」「限流器」「对象存储」等碎片节点），把已经清晰的结构搅乱。

不开这个开关不影响 `kg_add` —— 它和文件夹抽取是两套独立管线，哪怕抽取一次都没跑，
图也是完整可用的。**但 `kg_add` 写的是云端图谱**（实测：灌一个节点后本机数据库里
查不到，`kg_search` 立刻命中）—— 这个开关控制的是「文件全文要不要上传 + 要不要自动
抽取」，不是「数据留不留在本机」。

**索引在云端，文件会上传。** 开 Indexing 等于把该文件夹的文件**全文上传**到你账号下的
Quick Space，索引建在云端而不是本机。上传→可检索约 **1 分钟**（实测 20 个文件
平均 68s）。这带来的取舍见下方「[索引在云端意味着什么](#索引在云端意味着什么)」，
安全影响见 [SECURITY.md](SECURITY.md#-vault-里不放凭证和敏感个人数据)。

两条约束：

- **根目录只给 Agent access，不开 Indexing** —— agent 需要读写整棵树的权限，
  但索引按子目录分别建，根上再开一层是重复上传。
  **只注册 vault 这一棵**，不要把 `~` 或 `~/Documents` 整个交出去
  （见 [SECURITY.md](SECURITY.md#-agent-access-按最小必要范围给)）
- **同一棵树上父子目录不能都开 Indexing** —— 会被拒
  （`Cannot enable indexing: subfolder X is already indexed`）。先注册根（不开索引），
  再加 `raw` 和 `wiki`

#### 索引在云端意味着什么

三项检索能力都在，实测确认：关键词命中唯一词、语义检索在字面零重叠时命中正确文件、
`kg_search` 读得到抽取出的实体。**LLM Wiki 的三个操作都能正常跑。**

需要知道的四点：

| | |
|---|---|
| **同一 Space 内跨文件夹召回** | 语义检索会召回同一个 Quick Space 里**其它文件夹**的相关段落。想要检索范围互不干扰，就别把无关的文件夹注册进来 |
| **索引状态本地查不到** | 文件、chunk、实体、`kg_add` 灌的节点和边**全在云端**，本机数据库里没有副本。索引进度用 `file_rag_status` 查，图谱用 `kg_search` 查 |
| **`index_directory` 工具用不上** | 它跑在云端后端，看不到你设备上的本地路径，直接调会报 `Directory not found`。索引由 Quick 客户端的文件同步管道自动建立，不需要手工触发 |
| **删本地文件会同步删云端副本** | 不用额外清理 |

#### `wiki-inspect` 查文件层，`kg_search` 查图谱层

因为索引和图谱都在云端，`wiki-inspect` 的四个工具**全部从 `.md` 解析**，
本机只读一个库 —— `allowed_folders.db`（权限层，判断文件夹注册状态）。
分工是这样：

| 层 | 查什么 | 用什么 |
|---|---|---|
| **文件层** | 死链、孤儿页、frontmatter、`index.md` 一致性、`type` 有没有放对目录、缺页候选、枢纽分布、准确边数 | `wiki_lint` / `wiki_hubs` / `wiki_edges` |
| **注册层** | 文件夹注册了没、agent 有没有读写权限、`sync_status` 同步完没 | `wiki_index_status`（读 `allowed_folders.db`） |
| **图谱层** | 实体在图谱里有没有节点、`kg_add` 灌的边写进去没 | **`kg_search`** —— 在 Quick 里查，本机查不了 |
| **索引层** | 索引建到哪一步、什么时候建的、chunk 数 | **`file_rag_status`** —— 同上 |

> **数边有两种口径。** `wiki_lint` / `wiki_hubs` / `wiki_edges` 报的 `total_edges`
> 是**按 `(from, to)` 去重后**的唯一有向边数，且解析前剥掉了代码块（讲双链语法的页里
> `` `[[...]]` `` 不算链接）。自己按 `[[` 硬数出来的会更大 —— 那是含重复、含代码块
> 示例的原始 wikilink 数。三个工具的数字应该完全一致，不一致就说明有 bug。

### 3. 装 wiki-inspect MCP

```bash
mkdir -p ~/.quickwork/mcp-servers
cp -R mcp/wiki-inspect ~/.quickwork/mcp-servers/
```

连带 `import-wiki-inspect.json` 和文档一起过去，导入时路径就在手边。

导入 `~/.quickwork/mcp-servers/wiki-inspect/import-wiki-inspect.json`，或直接改
`~/.quickwork/profiles/<profile>/mcp_config.json`。

> 这份 JSON **导入后直接可用**，不需要改任何路径 —— 里面的 `~` 由 Python 展开。

重启 Quick 后验证：

```
跑一次 wiki_lint
```

⚠️ **一个 JSON 只能放一个 server** —— Quick 的导入器只读 `mcpServers` 的第一个 key。
详见 [mcp/wiki-inspect/INSTALL.md](mcp/wiki-inspect/INSTALL.md)。

> **为什么排在建 agent 之前** —— `AGENTS.md` 里引用 `wiki_lint` 十几次，
> 而装 MCP 必须重启 Quick。先装好再建 agent，建完就能立刻验证。

### 4. 建 Quick agent

```
建一个 agent，名字叫「LLM Wiki Agent」。
instructions 用 ~/Wiki-Vault/AGENTS.md 的全文，原样放进去，不要改写、不要精简。
```

它能直接读那个文件（根目录有 Agent access）。`instructions` 上限 50000 字符，
`AGENTS.md` 约 8000。**建完记得 publish** —— 新建的可能只是本地草稿。

配套字段和完整说明见 [agent/README.md](agent/README.md)。

MCP 已在上一步装好，建完可以立刻验证整条链路：

```
跑一次 wiki_lint
```

骨架刚铺好、没 ingest 任何素材，这时应报 0 内容页 —— 能正常返回就说明 agent
认得 MCP 工具、vault 路径也对。

## 跑起来

放一份素材进 `raw/articles/`，选中 agent：

```
ingest raw/articles/<文件名>
```

它会先讨论要点等你确认，然后一口气做完：写摘要页 → 建 concept/entity 页 →
解读进 `synthesis/` → 更新 `index.md` → 追加 `log.md` → 灌边 → 触发索引。

之后：

```
<直接提问>          # Query：先读 index 定位，再检索，答案带出处
跑一次 Lint         # 体检，只报告不动手
自动 ingest <文件>   # 跳过讨论直接做（批量灌入时用）
```

## 三个操作

| 操作 | 做什么 |
|---|---|
| **Ingest** | 读素材 → 产出摘要 → 同步更新全部关联词条。一份文档往往触发十余个页面的修改 |
| **Query** | 检索 Wiki 页面生成回答。优质结论直接写回知识库，把对话产出固化为知识 |
| **Lint** | 定期体检。排查内容矛盾、过时论断、孤立页面，挖掘信息缺口 |

Lint 有两条路，各管一半：

```bash
# 确定性校验（9 项）—— 脚本或 MCP
python3 skill/quick-wiki-ops/scripts/quick_wiki_lint.py
python3 skill/quick-wiki-ops/scripts/quick_wiki_lint.py --strict   # 有问题退出码 1
```

```
# 语义判断（5 项）—— 只有 LLM 能做
跑一次 Lint
```

**两条路都要跑**：脚本负责能精确判定的部分（计数、字段、链接完整性），
agent 负责需要读懂内容才能判断的部分（矛盾、过时、缺口）。互为对照 ——
任何一边单独用都会漏。

## 检索怎么用

| 要找什么 | 用什么 | 为什么不用别的 |
|---|---|---|
| 内容（按意思找） | `file_rag_search` | `kg_search(semantic)` 只检索实体的**那一句** summary |
| 按页面类型筛 | `kg_search(category="Concept")`，支持多值 | `folder_path` 存注册路径，整个 `wiki/` 一行、值都一样 |
| 谁引用了 X | 全文检索 `[[X]]` 字面量 | `kg_search` 的 edges 有 **3 条上限**，枢纽页会被截断 |

**语义检索是必需项。** 用日常说法提问时（「一个 agent 想让另一个 agent 帮它干活，
怎么找到对方」），字面词往往在全库一次都没出现过，关键词检索必然空手而归 ——
只有语义检索能落到正确的页上。

## 关于 MCP

**核心流程零 MCP 依赖。** `kg_search` / `kg_add` / `kg_edit` / `file_rag_search` /
`file_write` / `run_python` 全是 Quick 桌面端**内置**的。

有一处措辞容易误解：`run_python` 的 `tools` 参数，官方说「可注入 MCP 工具」，
实际注入的是**当前会话可用的任何工具**，内置的也算：

```python
run_python(
  code='...',
  tools=["kg_search", "kg_add", "kg_edit"]   # ← 注入内置的 kg_* 工具
)
```

不需要配任何 server。传了之后它们在 Python 命名空间里变成同步函数，
「解析文件 → 查库现状 → 算差集 → 批量写入」能在一次调用里闭环，
**数据不经过对话上下文**。

**唯一需要自建 MCP 的是内省层**，因为内置工具有三处读不到：

| 缺口 | MCP 工具 |
|---|---|
| 边的元数据 | `wiki_edges()` |
| 索引时间戳（判断索引是否滞后） | `wiki_index_status()` |
| `kg_search` 的 3 条边上限（枢纽页被截断） | `wiki_edges("<页名>")` 拿全量 |

把校验收进一次工具调用，比让 agent 现场写代码逐页查更省 token、也更稳定。

**内省层坚持只读** —— 校验只读取状态，从不写入。写操作一律走 `kg_add` / `file_write`，
让 Quick 自己维护索引和计量。四个工具不执行外部命令、不联网、SQL 全参数化，
`vault` 参数限定在注册过的目录内 —— 详见
[mcp/wiki-inspect/TOOLS.md](mcp/wiki-inspect/TOOLS.md#安全边界)。

## 一次完整运行的产出

一次完整运行（11 份素材：Karpathy gist、Bush 1945、MCP 规范、A2A 规范、
AWS Agent Registry 公告、AgentCore 服务簇/Runtime/Gateway 官方文档等）：

| | |
|---|---|
| 内容页 | **62** |
| `linksTo` 边 | **316** |
| 死链 | **0** |
| lint | 9 项全绿 |

产出全部在 [`examples/`](examples/) 下，可以直接对照。


## 已知限制

- **文件要全文上传云端** —— 开 Indexing 就等于把该文件夹的文件传到你账号下的
  Quick Space，索引建在云端。合规上要求笔记不出本机的话，这套方案不适用
- **索引不是实时的** —— 按 `Scan interval` 定时扫描（默认 30 分钟）；扫到后
  上传→可检索还要约 1 分钟。所以写页后要显式触发索引
- **`wiki-inspect` 查不了图谱层** —— 索引和图谱都在云端，本机没有副本，所以这套工具
  全部改成从 `.md` 解析：死链、孤儿页、frontmatter、`index.md` 一致性、`type` 目录、
  缺页候选、枢纽分布、准确边数都能查；**实体在图谱里有没有节点、边有没有灌进去**
  只能在 Quick 里用 `kg_search` 核，索引进度用 `file_rag_status`
- **KG 抽取的 `special_instructions` 是软约束** —— 若自行开启 `Always remember`，
  抽取器不保证遵守你写的规则，产出需要人工校正
- **agent 读到的素材正文和你的指令同一条通道** —— 被投毒的素材可以影响 agent 行为。
  只摄入可信来源，新素材先手动跑一次再交给定时任务，见 [SECURITY.md](SECURITY.md)
- **vault 里不要放凭证或敏感个人数据** —— agent 读得到，且 `wiki/` 的内容会过云端
  做 embedding

## 目录说明

```
sample-llm-wiki-on-quick/
├── SECURITY.md                动手前必读：风险链路 + 四条控制建议
├── scaffold/                  cp -R 到 ~/Wiki-Vault/
│   ├── AGENTS.md              schema 正本
│   ├── raw/{articles,papers,assets}/
│   └── wiki/{index,log}.md + {concepts,entities,sources,synthesis}/
├── agent/README.md            建 Quick agent 的完整步骤 + instructions 全文
├── mcp/wiki-inspect/
│   ├── server.py              4 个只读工具
│   ├── INSTALL.md             安装 + 排查
│   ├── TOOLS.md               工具说明
│   └── import-wiki-inspect.json
├── skill/quick-wiki-ops/      Claude Code 用
│   ├── SKILL.md               操作手册：工具分工、豁免清单、避坑
│   └── scripts/quick_wiki_lint.py
├── examples/                  一次真实运行的 62 页产出
└── docs/
    ├── sync-task-prompt.md        定时任务 prompt
    └── images/architecture.*      架构图（含 .drawio 源）
```

## 参考

- [Andrej Karpathy — `llm-wiki.md`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)（2026-04）
- [What is Amazon Quick?](https://docs.aws.amazon.com/quick/latest/userguide/what-is.html)
- [Amazon Quick on desktop](https://docs.aws.amazon.com/quick/latest/userguide/amazon-quick-desktop.html)
- [Connectors（桌面端）](https://docs.aws.amazon.com/quick/latest/userguide/connections-desktop.html)
- [Skills and agents（桌面端）](https://docs.aws.amazon.com/quick/latest/userguide/skills-and-agents-desktop.html)

## Security

动手前请先读 [SECURITY.md](SECURITY.md) —— 这套方案让 agent 读取你放进 `raw/` 的
素材并据此写文件、改知识图谱、执行代码，那份文档说明风险链路和四条控制建议。

漏洞报告见 [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications)。

## Contributing

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

MIT-0（MIT No Attribution）—— 可以自由使用、修改、分发，无需保留版权声明。
详见 [LICENSE](LICENSE)。
