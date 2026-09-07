# AIOps Agent Context

AIOps Agent 是一个把自然语言运维问题转成受控诊断动作，并把诊断能力交付给对话与任务调度入口的智能运维平台。

## Language

**Agent Conversation**
用户与 Agent 之间的多轮问答会话。会话保存用户消息、助手消息与工具执行审计。
_Avoid_: chat、聊天记录

**Diagnostic Job**
提交给调度系统的独立工作单元，包含类型、优先级、资源请求与执行参数。
_Avoid_: task、work order

**Worker**
注册到控制面并提供计算容量的执行者。Worker 心跳上报存活状态，领取并执行 Diagnostic Job。
_Avoid_: node、agent instance

**Capacity**
Worker 当前可用的 CPU 核数与内存（MB）。Capacity 用于判断 Job 能否被调度。
_Avoid_: quota、资源数

**Priority**
Job 的调度顺序类别：high、normal、low。同优先级按提交时间先到先得。
_Avoid_: level、等级

**Runbook**
已上传并分块向量化的排障手册知识，供 RAG 检索。
_Avoid_: 文档、知识

**Control Plane**
承载 API、调度器、状态存储与可观测性的服务；Worker 只从 Control Plane 领取任务并回传结果。
_Avoid_: master、主服务
