---
type: concept
tags: [a2a, task, lifecycle, state]
status: developing
summary: A2A 管理的基本工作单元，有唯一 ID、有状态、经历定义好的生命周期，终态为 COMPLETED/FAILED/CANCELED/REJECTED。
---
# A2A Task

Task 是 [[Agent2Agent]] 管理的**基本工作单元**：有唯一 ID、**有状态**、经历一套定义好的生命周期。它是 [[A2A 三层规范结构|数据模型层]]的核心对象（对应 proto 的 `Task`、`TaskStatus`、`TaskState`）。

## 生命周期与终态

任务状态由 `TaskState` 枚举表示，**终态**有四个：`TASK_STATE_COMPLETED`、`TASK_STATE_FAILED`、`TASK_STATE_CANCELED`、`TASK_STATE_REJECTED`。达终态后：

- 不能再向该任务发消息（否则 `UnsupportedOperationError`）。
- 流式连接（[[A2A 协议操作|Send Streaming / Subscribe]]）MUST 关闭。
- 取消非终态任务用 Cancel Task，但成功不保证。

## 怎么产生和追踪

- **产生**——[[A2A 协议操作|Send Message]] 时 agent MAY 创建新 Task 异步处理，或对简单交互直接返回 [[A2A 消息与内容模型|Message]]。
- **追踪**——Get Task 轮询、Subscribe to Task 订阅流、或经 [[Push Notifications]] webhook 收异步更新。
- **产出**——任务结果是 [[A2A 消息与内容模型|Artifact]]（由 Part 组成）。
- **分组**——可选的 `Context` 标识符把相关任务和消息逻辑分组。

流事件 `TaskStatusUpdateEvent`（状态变化）和 `TaskArtifactUpdateEvent`（artifact 更新）在流式和 push 两种模式里都用。

常见叫法：A2A Task、任务、工作单元、TaskState、任务生命周期、任务终态、COMPLETED/FAILED/CANCELED/REJECTED、有状态任务。

## 关联
- 所属协议: [[Agent2Agent]]
- 操作: [[A2A 协议操作]]
- 内容: [[A2A 消息与内容模型]]
- 异步更新: [[Push Notifications]]
- 原文: [[A2A Specification]]
