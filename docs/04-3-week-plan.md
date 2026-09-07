# AIOps Agent v2 三周巩固与求职冲刺计划

目标：把 v2 代码、架构和面试话术全部掌握，确保简历中的每条描述都有实际代码支撑。

## 每日计划

| 天 | 主题 | 任务 | 必须补的基础 vs 边做边学 |
|---|---|---|---|
| D1 | 通读项目 | 跑 `pytest -q`；启动服务；读完 `CONTEXT.md`、spec、README 与 5 张 tickets | 边做边学 |
| D2 | API 与存储 | 阅读 API/schema/db 代码；用 curl 注册 Worker、提交/查询 Job | 必补：HTTP、REST、SQLite |
| D3 | Linux/网络/Docker | 练习 `ps/ss/netstat/journalctl/df`；运行 `docker compose config`，理解端口与网络 | 必补：Linux、TCP/IP |
| D4 | 调度原理 | 阅读 `app/scheduling.py` 与生命周期测试；手绘调度状态机 | 必补：调度与优先级、容量 |
| D5 | Worker 运行时 | 阅读 `app/worker.py`；启动 Worker 验证注册、领取、执行、回传 | 边做边学：轮询协议 |
| D6 | 可观测性 | 查看 `/metrics`、结构化日志、Prometheus 配置与 Grafana 面板 | 边做边学：Prometheus/Grafana |
| D7 | 第一次复盘 | 对照 spec 自评 Ticket 01-05，跑全量测试并 commit/push | 必补：代码走查习惯 |
| D8 | Docker 实操 | `docker compose up --build`，验证 API/Worker/Prometheus/Grafana | 必补：Dockerfile/Compose/volume |
| D9 | Kubernetes | 阅读 `deploy/k8s/`，用 Kind 或理论讲清 Deployment/Service/ConfigMap | 边做边学：K8s 核心对象 |
| D10 | Linux 排障练习 | 在容器内执行系统状态、日志、端口工具，理解受控工具边界 | 必补：权限、进程、日志 |
| D11 | FastAPI 深入 | 阅读路由、中间件、鉴权、限流；补 2 个 API 测试 | 必补：FastAPI/Pydantic |
| D12 | Vue 联调 | 阅读 `web/`，为任务页增加状态筛选或自动刷新 | 必补：Vue 基础 |
| D13 | Agent/RAG | 读懂 Mock/OpenAI LLM 适配、ToolRegistry、RAG 检索 | 必补：AI 推理服务原理 |
| D14 | 第二次复盘 | 整理架构图与模块职责，全量测试并推送 | 必补：系统设计表述 |
| D15 | 面试问题库 | 准备“为什么用 HTTP polling、容量如何计算、状态机如何设计”等回答 | 边做边学 |
| D16 | 后端岗位冲刺 | 针对后端 JD 复习 API、Agent、RAG、测试、CI | 必补：后端工程能力 |
| D17 | 云计算岗位冲刺 | 针对云计算 JD 复习 Linux、Docker、K8s、调度、监控 | 必补：算力调度、云基础 |
| D18 | CI/CD 实操 | 查看 GitHub Actions 运行结果，能说明 test/compose/build 三步 | 必补：CI/CD |
| D19 | 简历走查 | 对照两份简历逐条说出代码位置与原理 | 必补：面试一致性 |
| D20 | 模拟面试 | 45 分钟自述：架构、调度、Agent/RAG、部署、监控 | 必补：表达与复盘 |
| D21 | 缓冲日 | 补齐薄弱点，整理最终提交与演示脚本 | 边做边学 |

## 知识等级目标

| 知识点 | 目标等级 |
|---|---|
| Linux 命令、权限、进程、端口、日志 | 掌握 |
| 计算机网络：TCP/IP、HTTP、DNS、反向代理 | 掌握 |
| Dockerfile、Compose、网络与数据卷 | 掌握 |
| Kubernetes 核心概念与部署对象 | 熟悉 |
| 算力调度、优先级与容量匹配 | 熟悉 |
| Python/FastAPI/Pydantic/SQLite | 掌握 |
| AI 推理与 Agent/RAG 基础 | 熟悉 |
| Vue 3 基础与前后端联调 | 熟悉 |
| Prometheus/Grafana 可观测性 | 熟悉 |
| pytest 与 GitHub Actions | 掌握 |

面试红线：不要把自己没有真正操作过的云厂商、GPU 集群、高可用说成线上经验；只讲本仓库能演示的本地闭环。
