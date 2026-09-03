---
type: concept
tags: [mcp, security, trust, consent, tool-safety]
status: developing
summary: MCP 的安全与信任四原则——用户同意与控制、数据隐私、工具安全；协议层无法强制，由实现者建同意/授权流。
---
# MCP 安全与信任

[[Model Context Protocol]] 通过任意数据访问和代码执行路径实现强大能力，因此规范列出所有实现者必须审慎处理的安全与信任考量。

## 关键原则

1. **用户同意与控制**——用户必须显式同意并理解所有数据访问和操作，保留对「分享什么数据、采取什么行动」的控制；实现者应提供清晰的审阅/授权 UI。
2. **数据隐私**——host 在向 server 暴露用户数据前必须获显式同意，未经同意不得把资源数据传往别处，用户数据应有适当访问控制。
3. **工具安全**——[[MCP 服务器原语|Tool]] 代表任意代码执行，须谨慎对待；工具行为的描述/annotation 除非来自可信 server 否则视为**不可信**；host 调用任何 tool 前必须获用户显式同意；用户应在授权前理解每个 tool 做什么。

## 协议层不强制

MCP 协议本身**无法在协议层强制**这些原则。实现者 **SHOULD**：建健壮的同意与授权流、清楚记录安全影响、实现适当的访问控制与数据保护、在集成中遵循安全最佳实践、在功能设计中考虑隐私影响。

> 此外规范在具体处也贯彻安全默认：`icons` 的 URI 须 HTTPS/data 且按 magic bytes 校验；JSON Schema 的 `$ref` **MUST NOT** 自动解引用网络 URI；组合关键字设上限防校验器 DoS。

常见叫法：MCP 安全与信任、security and trust、安全原则、用户同意、工具安全、tool safety、数据隐私、consent。

## 关联
- 所属协议: [[Model Context Protocol]]
- 受约束的原语: [[MCP 服务器原语]]
