---
type: concept
tags: [a2a, message, part, artifact, data-model]
status: developing
summary: A2A 数据模型里承载内容的三个对象——Message（带 role 的通信轮次）、Part（最小内容单元）、Artifact（任务产出）。
---
# A2A 消息与内容模型

[[Agent2Agent]] [[A2A 三层规范结构|数据模型层]]里承载内容的对象，三者层层组成：

- **Message**——client 与 remote agent 之间的一个**通信轮次**，有 `role`（`user` 或 `agent`，对应 proto 的 `Role` 枚举），含一个或多个 `Part`。
- **Part**——Message 或 Artifact 内的**最小内容单元**，可含文本、文件引用或结构化数据。这支撑了 A2A「Modality Agnostic」原则——文本、音视频（经文件引用）、结构化数据/表单、乃至嵌入式 UI 组件都以 Part 承载。
- **Artifact**——agent 作为 [[A2A Task|任务]]结果生成的**输出**（文档、图像、结构化数据），由 `Part` 组成。

## 在流与推送里的角色

任务处理中，Artifact 的增量通过 `TaskArtifactUpdateEvent` 交付；配合 `TaskStatusUpdateEvent`（状态变化）构成 [[A2A 协议操作|流式]]和 [[Push Notifications|push]] 两种模式的事件流。webhook 的 StreamResponse 载荷恰含 task/message/statusUpdate/artifactUpdate 之一。

常见叫法：A2A 消息模型、Message/Part/Artifact、内容单元、通信轮次、Role、user/agent 角色、artifact 产出、modality agnostic。

## 关联
- 所属协议: [[Agent2Agent]]
- 结构层: [[A2A 三层规范结构]]
- 任务产出: [[A2A Task]]
- 操作: [[A2A 协议操作]]
- 原文: [[A2A Specification]]
