---
type: concept
tags: [a2a, push-notifications, webhook, async]
status: developing
summary: A2A 经 server 发起的 HTTP POST 到 client webhook 交付的异步任务更新，用于长任务或断连场景；载荷是 StreamResponse。
---
# Push Notifications

Push Notifications 是 [[Agent2Agent]] 的一种异步任务更新交付方式：经 **server 发起的 HTTP POST** 到 client 提供的 webhook URL 交付，用于长任务或 client 断连的场景。它与同步请求/响应、流式并列为 A2A 三种交互模态，体现「Async First」原则。

## 配置与载荷

- **配置**——通过 [[A2A 协议操作|Create/Get/List/Delete Push Notification Config]] 四个操作管理，需 agent 声明 push 能力（否则 `PushNotificationNotSupportedError`）。配置 MUST 持续到任务完成或显式删除。
- **载荷**——webhook 收到的是 `StreamResponse` 对象（与流式相同格式），恰含 `task` / `message` / `statusUpdate` / `artifactUpdate` 之一，Content-Type 为 `application/a2a+json`。
- **认证**——agent MUST 按 `TaskPushNotificationConfig.authentication` 带认证凭据（Bearer、Basic 等标准 HTTP 认证）。

## 交付保证与 client 责任

- agent MUST 至少尝试交付一次，MAY 指数退避重试，SHOULD 设 10–30 秒超时，MAY 连续失败若干次后停止。
- client MUST 回 2xx 确认、SHOULD 幂等处理（可能重复投递）、MUST 校验 task ID 匹配预期、SHOULD 验证通知来源。

常见叫法：Push Notifications、推送通知、webhook 通知、异步任务更新、server 发起 POST、TaskPushNotificationConfig、断连场景更新。

## 关联
- 所属协议: [[Agent2Agent]]
- 配置操作: [[A2A 协议操作]]
- 更新对象: [[A2A Task]]
- 原文: [[A2A Specification]]
