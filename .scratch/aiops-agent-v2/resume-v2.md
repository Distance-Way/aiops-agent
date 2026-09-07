# AIOps Agent v2 简历终稿

## 版本 A：云计算与算力工程师

**AIOps Agent：智能运维诊断与算力调度平台** | 独立开发
2026.09 - 至今

技术栈：Python/FastAPI、Linux、Docker Compose、Kubernetes、Prometheus/Grafana、GitHub Actions、Vue 3

项目介绍：面向 Linux 服务器与容器化服务运维场景，构建 Agent 自动化诊断与算力调度平台。系统自动采集 CPU、内存、磁盘、端口与日志状态，并按 Worker 容量和任务优先级调度执行诊断任务。

个人职责：
1. 实现 Linux 资源采集与诊断工具：CPU、内存、磁盘、进程、端口与日志检索，工具带超时与输出截断保护；
2. 设计 Worker 注册、心跳、容量上报与调度闭环：按优先级和 CPU/内存余量领取 Diagnostic Job，资源不足自动排队；
3. 基于 FastAPI 封装统一运维 API，接入 API Key 鉴权、限流、SQLite 持久化与请求审计；
4. 使用 Docker Compose 编排 API、Worker、Prometheus、Grafana，提供 Kubernetes Deployment/Service/ConfigMap 清单，并通过 GitHub Actions 完成测试与镜像构建检查。

## 版本 B：后端工程师

**AIOps Agent：AI 运维诊断 Agent 与任务调度后端** | 独立开发
2026.09 - 至今

技术栈：Python/FastAPI、SQLite、RAG、Vue 3、Docker、Prometheus、pytest、GitHub Actions

项目介绍：面向服务器与日志排障场景的 AI Agent 后端服务。用户通过 Vue 页面或 REST API 提问，后端完成会话管理、模型调用、工具执行、RAG 检索与任务状态流转。

个人职责：
1. 基于 FastAPI 实现会话、对话、文档、Worker、Diagnostic Job 等 REST API，接入 API Key 鉴权、限流与 SQLite 持久化；
2. 实现 Agent 编排与 Function Calling 循环，限制最大工具轮数和输出长度；实现 RAG 文档分块、本地向量化与来源引用；
3. 设计 Control Plane + Worker 调度：Worker 注册/心跳/领取/回传，按优先级与容量执行系统状态、日志、端口和日志分类推理；
4. 开发 Vue 3 任务与 Worker 管理页；使用 pytest 覆盖 API、调度、Worker 与 UI 服务测试，通过 Docker Compose、Prometheus 与 GitHub Actions 完成交付。
