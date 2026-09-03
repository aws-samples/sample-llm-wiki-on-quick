---
type: synthesis
tags: [a2a, discovery, delegation, agent-card, workflow]
status: developing
summary: 一个 agent 发现并委派另一个 agent 干活的端到端时序——发现 Agent Card → 选传输 → 验签/认证 → Send Message 建 Task → 追踪结果，串起散在多页的 A2A 机制。
---
# A2A 委派端到端流程

一处跨页综合：把「一个 [[Agent2Agent|A2A]] Client agent 想让另一个 agent 帮它干活」的完整时序串起来。单看各页只讲了一环——[[Agent Card]] 讲发现、[[A2A 协议操作]] 讲调用、[[A2A Task]] 讲追踪——本页把它们连成一条端到端路径。来源：[[A2A Specification]]。

## 五步时序

**1. 发现对方（找到 Agent Card）**

干活的一方是 A2A Server（remote agent），MUST 发布一份 [[Agent Card]]。派活方（Client）用三种方式之一找到它：

- **Well-Known URI**——已知对方域名，直取 `https://{server_domain}/.well-known/agent-card.json`。
- **Registries/Catalogs**——只知道「要什么能力」，去策展目录语义搜索。这正是 [[AWS Agent Registry]] 编目 A2A Agent 记录（[[四种记录类型]]之一）的场景。
- **Direct Configuration**——固定合作，预配置 URL。

**2. 选传输方式**

读 Agent Card 的 `supportedInterfaces`（按偏好顺序列 JSON-RPC / gRPC / HTTP+JSON）。Client MUST 选第一个自己支持的 transport、用对应 URL、按所选接口的 `tenant` 值设请求。

**3. 验真伪 + 认证**

- **验卡**——Agent Card MAY 带 JWS 签名；经公开目录发现陌生 agent 时，验证方 SHOULD 至少验过一个签名才信任（防假冒）。
- **认证**——按 Agent Card 声明的 securityScheme（OAuth2 / OIDC / APIKey / mTLS 等）拿到凭据。

**4. 派活（Send Message → Task）**

用 [[A2A 协议操作|Send Message]] 发起交互。agent 通常返回一个有状态的 [[A2A Task]]（也可能对简单交互直接回 [[A2A 消息与内容模型|Message]]）。这一步不需要共享内部状态——A2A 的 Opaque Execution 原则：只按声明的能力和交换的信息协作。

**5. 追踪结果**

三种拿结果的方式（对应 A2A 三种交互模态）：

- **轮询**——Get Task 取当前状态。
- **流式**——Send Streaming Message / Subscribe to Task，实时收 `TaskStatusUpdateEvent` / `TaskArtifactUpdateEvent`。
- **异步推送**——[[Push Notifications]]：长任务或断连时经 webhook 收更新。

任务达终态（COMPLETED/FAILED/CANCELED/REJECTED）时流关闭，产出是 [[A2A 消息与内容模型|Artifact]]。

## 一句话概括

**发现（Agent Card）→ 选传输 → 验签认证 → Send Message 建 Task → 轮询/流式/推送拿结果。** 发现层可以是点对点（well-known URI）也可以经目录（[[AWS Agent Registry]]），后者正是 registry 同时充当「agent 目录」的意义所在。

## 关联
- 所属协议: [[Agent2Agent]]
- 发现文档: [[Agent Card]]
- 调用操作: [[A2A 协议操作]]
- 工作单元: [[A2A Task]]
- 异步结果: [[Push Notifications]]
- 目录发现: [[AWS Agent Registry]]
- 来源: [[A2A Specification]]
