# LLM Wiki on Amazon Quick

在 Amazon Quick 桌面端搭一个按 [Karpathy LLM Wiki 模式](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)组织的个人知识库。

| 路径 | 内容 | 博客步骤 |
|---|---|---|
| [`scaffold/`](scaffold/) | vault 骨架 + `AGENTS.md`（agent instructions） | Step 1 |
| [`mcp/wiki-inspect/`](mcp/wiki-inspect/) | 只读校验 MCP server | Step 3 |
| [`prompts.md`](prompts.md) | 全部提示词：建 agent、Ingest、Query、Lint、定时任务 | Step 4 起 |
| [`docs/images/`](docs/images/) | 架构图（png / svg / drawio） | Solution overview |

## 快速开始

```bash
git clone https://github.com/aws-samples/sample-llm-wiki-on-quick.git && cd sample-llm-wiki-on-quick
mkdir -p ~/Wiki-Vault && cp -R scaffold/ ~/Wiki-Vault/
mkdir -p ~/.quickwork/mcp-servers && cp -R mcp/wiki-inspect ~/.quickwork/mcp-servers/
```

使用前先读 [SECURITY.md](SECURITY.md)。

## License

MIT-0，见 [LICENSE](LICENSE)。
