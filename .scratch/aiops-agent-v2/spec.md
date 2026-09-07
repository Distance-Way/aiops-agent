# AIOps Agent v2 Spec

## Problem Statement

当前 AIOps Agent 只有单进程的同步对话与诊断能力，无法展示“多执行者按容量领取运维任务”的算力调度场景，也无法直接支撑云计算与算力岗位的面试叙事。

## Solution

在现有 Agent、RAG、API、Vue 与可观测性之上，加入 Control Plane + Worker 的 Diagnostic Job 调度闭环：用户或前端提交 Job，Control Plane 按 Priority 与 Capacity 调度给空闲 Worker，Worker 执行受控诊断/推理动作并回传结果；所有状态在 SQLite 中持久化，Prometheus 暴露队列与 Worker 指标。

## User Stories

1. As a control-plane user, I want to submit a Diagnostic Job with priority and resource requests, so that it can be queued and picked up by an available Worker.
2. As a control-plane user, I want to list and inspect jobs and their status, so that I can see what is queued, running, succeeded or failed.
3. As a Worker operator, I want my Worker to register itself with CPU/memory capacity, so that the scheduler knows what can be allocated.
4. As a Worker, I want to heartbeat my availability, so that a stale or dead Worker is not selected for new jobs.
5. As a Worker, I want to claim the next fitting Diagnostic Job, so that jobs are executed only when capacity exists.
6. As a Worker, I want to complete a claimed job with a result or error, so that job state advances and capacity is released.
7. As a scheduler user, I want high-priority jobs served before normal/low jobs of the same resource profile, so that urgent diagnostics are not blocked by routine work.
8. As a scheduler user, I want jobs that do not fit any Worker to remain queued, so that they are picked up later instead of failing.
9. As an operator, I want Worker count, queue depth and job completion metrics, so that platform health is observable.
10. As an operator, I want a Vue view for Workers and Diagnostic Jobs, so that I can submit and observe jobs without calling the API manually.
11. As a developer, I want the existing Agent/RAG/chat API to keep working, so that v2 does not force a rewrite of the current product.

## Implementation Decisions

- Existing FastAPI application becomes the Control Plane and keeps owning API Key auth, rate limiting, SQLite and metrics.
- Storage gains two domain tables: `workers` and `diagnostic_jobs`; job state transitions are queued -> running -> succeeded/failed.
- Scheduling is explicit and lazy: a claim request scans queued jobs, orders by priority then created_at, and assigns the first job that fits the requesting Worker's remaining Capacity.
- Worker Capacity is calculated from registered capacity minus jobs currently running on that Worker; no separate allocation ledger.
- Worker communicates over HTTP polling using the same API Key; no Redis or cloud broker is introduced in v2.
- Worker execution supports controlled job types only: `system_status`, `service_check`, `query_logs` and `log_inference`; arbitrary shell is not allowed.
- `log_inference` uses a tiny deterministic local model so AI inference remains offline and testable.
- The existing synchronous Agent chat API is unchanged; v2 adds the Diagnostic Job surface beside it.
- Vue static frontend gains a Jobs and Workers view without introducing a separate build pipeline.
- Docker Compose runs control plane and Worker processes from the same image; Kubernetes manifests mirror that deployment.

## Testing Decisions

- The primary seam is the public HTTP API: tests register a Worker, submit Jobs, claim and complete them through TestClient, and assert observable state transitions.
- A second seam is the local inference function: known log samples must map to stable labels and confidence values.
- Existing Agent/RAG tests must stay green; v2 tests use the same temporary SQLite fixture.
- Unit tests do not mock internal scheduler collaborators; they exercise the control-plane HTTP boundary.

## Out of Scope

- Redis/Kafka, cloud providers, GPU-aware scheduling, retries with backoff, distributed SQLite, job cancellation and multi-tenant isolation.
- Replacing or migrating the existing chat/RAG storage model.

## Further Notes

Interview framing should focus on why the poll-based Control Plane is a reasonable MVP trade-off, how Capacity is tracked, and where a message queue or Kubernetes scheduler would change the design.
