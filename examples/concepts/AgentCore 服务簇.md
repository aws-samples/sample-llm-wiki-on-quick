---
type: concept
tags: [aws, agentcore, platform, cluster]
status: developing
summary: Amazon Bedrock AgentCore 是一簇可独立或组合使用的模块化服务（13 个），覆盖 agent 的构建、部署、运营；Runtime/Gateway/Registry 只是其中三个。
---
# AgentCore 服务簇

**Amazon Bedrock AgentCore 不是单个服务，而是一簇模块化服务**——截至本素材（2026-09-02 [[AgentCore 服务簇总览 (AWS Docs)]]）共 **13 个**，可**独立或组合使用**，框架无关、模型无关。本页是这一簇的枢纽索引；产品实体本身见 [[Amazon Bedrock AgentCore]]。

> 为什么单开这页：本 vault 早期只从 [[AWS Agent Registry (AWS Blog)]] 了解到 Runtime 和 Gateway 两个组件，一度把 AgentCore 当作「含两组件的托管平台」。总览素材表明它是一整簇服务，故建此枢纽页纠正框定。

## 13 个服务

### 运行与编排
- [[AgentCore Runtime]]——serverless agent 托管，每会话独占 microVM 隔离。
- [[AgentCore Harness]]——托管 agent loop，单次 API 调用定义并运行 agent。
- [[AgentCore Gateway]]——把 API/Lambda/服务转成 MCP 工具的统一入口。

### 状态与身份
- [[AgentCore Memory]]——短期 + 长期记忆，跨会话持久、可跨 agent 共享。
- [[AgentCore Identity]]——agent 身份、访问与认证管理，兼容现有 IdP。

### 工具沙箱
- [[AgentCore Code Interpreter]]——隔离沙箱执行代码（Python/JS/TS）。
- [[AgentCore Browser]]——云端浏览器运行时，agent 操作 web 应用。

### 质量与治理
- [[AgentCore Observability]]——基于 OpenTelemetry 的追踪/调试/监控。
- [[AgentCore Evaluations]]——自动化 agent 评估，结果并入 Observability。
- [[AgentCore Optimization]]——基于 Evaluations 的持续改进 + A/B 测试。
- [[AgentCore Policy]]——用自然语言或 Cedar 写规则，经 Gateway 拦截工具调用。
- [[AWS Agent Registry|AgentCore Registry]]——agent/工具/技能的集中治理目录（本 vault 以 [[AWS Agent Registry]] 记之）。

### 支付
- [[AgentCore Payments]]——用 x402/MPP 让 agent 做微交易支付。

## 服务间怎么咬合

Runtime/Harness 跑 agent，Gateway 供工具，Memory 存状态，Identity 管认证，Code Interpreter/Browser 是内置工具，Observability 收遥测、Evaluations 评估、Optimization 据评估改进、Policy 卡工具调用边界，Registry 编目一切。多数服务把遥测汇入 [[AgentCore Observability]]，多条治理路径经 [[AgentCore Gateway]] 落地。

常见叫法：AgentCore 服务簇、AgentCore 服务、Amazon Bedrock AgentCore 组件、AgentCore 模块、agentic 平台服务、AgentCore 13 个服务、AgentCore capabilities。

## 关联
- 产品实体: [[Amazon Bedrock AgentCore]]
- 素材: [[AgentCore 服务簇总览 (AWS Docs)]]
- 成员（运行）: [[AgentCore Runtime]]、[[AgentCore Harness]]、[[AgentCore Gateway]]
- 成员（状态/身份）: [[AgentCore Memory]]、[[AgentCore Identity]]
- 成员（沙箱）: [[AgentCore Code Interpreter]]、[[AgentCore Browser]]
- 成员（质量/治理）: [[AgentCore Observability]]、[[AgentCore Evaluations]]、[[AgentCore Optimization]]、[[AgentCore Policy]]、[[AWS Agent Registry]]
- 成员（支付）: [[AgentCore Payments]]
