---
type: concept
tags: [mcp, primitives, prompts, resources, tools]
status: developing
summary: MCP server 向 client 提供的三种基本构件——Prompts（用户控制）、Resources（应用控制）、Tools（模型控制），按控制方区分。
---
# MCP 服务器原语

[[Model Context Protocol]] 里 server 向 client 提供的三种基本构件（primitives），为语言模型添加上下文。三者按**控制方**区分：

| 原语 | 控制方 | 描述 | 例子 |
|---|---|---|---|
| **Prompts** | 用户控制 | 用户选择调用的交互式模板/指令 | 斜杠命令、菜单项 |
| **Resources** | 应用控制 | client 附加并管理的结构化上下文数据 | 文件内容、git 历史 |
| **Tools** | 模型控制 | 暴露给 LLM 采取行动或取信息的可执行函数 | API POST 请求、写文件 |

「控制方」是理解三者差异的关键：Prompts 由用户主动触发，Resources 由 client 应用决定附加什么，Tools 交给模型自主调用（因此 [[MCP 安全与信任]]特别强调 tool 是任意代码执行、调用前须用户同意）。

## 与能力、客户端功能的关系

server 要提供某原语，须在[[能力协商|能力]]里通告。对应地，client 也能向 server 提供功能——主要是 **[[Elicitation]]**（server 发起、向用户索取额外信息），在本版通过 [[MRTR 与 InputRequiredResult]] 模式实现。

常见叫法：MCP 服务器原语、server primitives、三种原语、Prompts/Resources/Tools、提示/资源/工具、server features、服务器功能。

## 关联
- 所属协议: [[Model Context Protocol]]
- 通告机制: [[能力协商]]
- 安全约束: [[MCP 安全与信任]]
- client 侧对应: [[MRTR 与 InputRequiredResult]]
- client 侧功能: [[Elicitation]]
