# AIOps Agent v2 调度设计

## 目标

v2 在原有单进程 AIOps Agent 上增加 Control Plane + Worker 调度闭环，用可解释的容量匹配展示算力调度，同时保留现有 Agent/RAG/Vue 能力。

## 组件

```text
Vue UI -> FastAPI Control Plane
Control Plane -> SQLite（Workers / Diagnostic Jobs）
Worker1/Worker2 -> register + heartbeat + claim + complete HTTP API
Worker -> system_status / service_check / query_logs / log_inference
Prometheus -> Control Plane /metrics
Grafana -> Prometheus dashboard
```

## 调度模型

- Diagnostic Job 使用 `high/normal/low` 优先级；同优先级按创建顺序领取。
- Worker 注册时声明 CPU 与内存容量。
- Worker 领取任务时按“剩余容量 = 声明容量 - 运行中任务资源”匹配首个可容纳 Job。
- Job 状态：`queued -> running -> succeeded/failed`。
- Worker 心跳超过 `WORKER_TTL_SECONDS` 后不再参与调度。

## 设计取舍

Worker 与 Control Plane 之间使用 HTTP polling，而不是 Redis/RabbitMQ，保证本地零额外依赖且可测试。见 `docs/adr/0001-worker-http-polling.md`。

## 部署

- Docker Compose：`agent` + `worker` + `prometheus` + `grafana`
- Kubernetes：`deploy/k8s/` 下 API/Worker Deployment、Service 与 ConfigMap
