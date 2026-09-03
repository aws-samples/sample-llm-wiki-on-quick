---
type: concept
tags: [a2a, agent-card, discovery, jws, signing]
status: developing
summary: A2A Server 发布的 JSON 元数据文档，描述其身份、能力、技能、服务端点与认证要求；可经 well-known URI 发现、用 JWS 签名。
---
# Agent Card

Agent Card 是 [[Agent2Agent]] Server（remote agent）**MUST** 发布的 JSON 元数据文档，描述 server 的身份、能力、技能、服务端点和认证要求。client 用它来发现合适的 agent 并配置交互。它是 [[A2A 三层规范结构|数据模型层]]的发现对象（proto 的 `AgentCard` 及 `AgentProvider`/`AgentCapabilities`/`AgentSkill`/`AgentInterface`/`AgentCardSignature`）。

## 发现机制

- **Well-Known URI**——`https://{server_domain}/.well-known/agent-card.json`。
- **Registries/Catalogs**——查询策展的 agent 目录。这正是 [[AWS Agent Registry]] 编目 A2A Agent 记录的场景。
- **Direct Configuration**——预配置的 URL 或内容。

## 协议声明

`supportedInterfaces` SHOULD 按偏好顺序声明所有支持的协议组合（JSON-RPC / gRPC / HTTP+JSON），第一条为首选；client MUST 解析并选第一个支持的 transport、用对应 URL、按所选接口的 `tenant` 值设每个请求。

## 签名（JWS）

Agent Card MAY 用 JSON Web Signature（JWS，RFC 7515）签名以保真。签名前 MUST 用 JSON Canonicalization Scheme（JCS，RFC 8785）规范化：按 Protocol Buffer 字段存在语义处理默认值（optional 未设省略、REQUIRED 始终在）、词典序排 key、去无意义空白、排除 `signatures` 字段本身。protected header MUST 含 `alg`/`typ`/`kid`，MAY 含 `jku`（JWKS URL）。验证方 SHOULD 至少验一个签名后才信任、公钥经 HTTPS 取、过期/吊销 key MUST NOT 用、多签名 MAY 支持 key 轮换。

## 缓存

Agent Card 变化不频繁，server SHOULD 带 `Cache-Control`(max-age) 和 `ETag`（由 version 或内容 hash 派生），MAY 带 `Last-Modified`；client SHOULD 遵循 RFC 9111、过期后用条件请求（If-None-Match / If-Modified-Since）。

常见叫法：Agent Card、agent 卡片、agent 元数据文档、well-known agent card、AgentCard、JWS 签名、agent 发现文档、supportedInterfaces。

## 关联
- 所属协议: [[Agent2Agent]]
- 结构层: [[A2A 三层规范结构]]
- 被编目于: [[AWS Agent Registry]]
- 原文: [[A2A Specification]]
