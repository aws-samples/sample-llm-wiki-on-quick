---
type: concept
tags: [aws, agent-registry, shadow-ai, governance, security]
status: developing
summary: 团队未经注册就部署、无监管运行的影子 agent 和工具——企业治理的盲区；AWS Agent Registry 用组织级 auto-detection 应对。
---
# Shadow AI

指团队未经注册、无监管就部署运行的 agent 和工具（「shadow agents」/「shadow resources」）。它们是快速增长的企业治理盲区：无 owner、无审查、无审计轨迹。本 vault 从 [[AWS Agent Registry (AWS Blog)]] 了解这一问题及其应对。

## AWS Agent Registry 如何应对

- **组织级 auto-detection**——管理员在 AWS Organization 级启用一次端点检测，[[AWS Agent Registry]] 自动检测跨所有账户在 [[Amazon Bedrock AgentCore]] 的 runtime 和 Gateway 上运行的 agent 与 MCP server。
- **Detected Endpoints 视图**——检测到的资源带标识符、端点、描述符元数据汇入集中视图，作为 **draft 记录**流入标准[[记录生命周期]]（review → approve → publish 到 discovery plane）。
- **持续关系**——新 agent 部署到已连接账户时自动出现，无需发布团队操作。
- **路线图**——未来将扩展检测到 EC2 / EKS / ECS 及（经联邦）非 AWS/本地/SaaS 环境，让 registry 反映真实部署状况。

## 相关的安全考量

原文也提醒：能发现工具的人不一定该能注册新工具；工具元数据可能含内部端点或架构细节，对威胁行为者有用——要评估这些信息是否该放在广泛可读的 registry 条目里，并审计谁在查询。

常见叫法：Shadow AI、影子 AI、shadow agents、影子 agent、未注册 agent、agent sprawl、agent 蔓延、治理盲区。

## 关联
- 应对产品: [[AWS Agent Registry]]
- 检测平台: [[Amazon Bedrock AgentCore]]
- 流入流程: [[记录生命周期]]
