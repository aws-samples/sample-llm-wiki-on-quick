---
type: concept
tags: [a2a, operations, streaming, tasks]
status: developing
summary: A2A 所有实现必须支持的绑定无关核心操作——Send Message、流式消息、Get/List/Cancel/Subscribe Task，以及四个 Push Notification Config 操作。
---
# A2A 协议操作

[[Agent2Agent]] 的[[A2A 三层规范结构|抽象操作层]]，绑定无关，所有实现都必须支持：

## 消息与任务操作

- **Send Message**——发起交互的主操作。client 发消息，收到追踪处理的 [[A2A Task|Task]] 或直接的 [[A2A 消息与内容模型|Message]]；MUST 立即返回，任务处理 MAY 异步继续。
- **Send Streaming Message**——处理中实时流式更新。返回初始 Task/Message 后跟零或多个 `TaskStatusUpdateEvent`/`TaskArtifactUpdateEvent`，任务达[[A2A Task|终态]]时流关闭。需 agent 声明 streaming 能力。
- **Get Task**——取任务当前状态（状态、artifacts、可选 history），用于轮询或取终态。
- **List Tasks**——列任务，**游标分页**（pageToken/nextPageToken，nextPageToken MUST 始终存在，末页为空串），MUST 按状态时间戳降序、只返回已认证 client 可见的任务。
- **Cancel Task**——请求取消进行中任务，成功不保证（可能已完成或不支持）。
- **Subscribe to Task**——对已有任务建流式连接，首事件 MUST 是当前 Task（防 GetTask 与 Subscribe 之间丢信息）。

## Push Notification Config 操作

Create / Get / List / Delete 四个操作管理任务的 webhook 推送配置，需 agent 声明 push 能力。详见 [[Push Notifications]]。

## 交互模态

A2A 支持三种：同步请求/响应、流式（SSE 实时更新）、异步 push 通知（长任务或断连场景）。这体现「Async First」原则。

常见叫法：A2A 协议操作、core operations、Send Message、流式消息、Get/List/Cancel Task、Subscribe to Task、任务操作、绑定无关操作。

## 关联
- 所属协议: [[Agent2Agent]]
- 操作对象: [[A2A Task]]
- 内容: [[A2A 消息与内容模型]]
- 异步: [[Push Notifications]]
- 原文: [[A2A Specification]]
