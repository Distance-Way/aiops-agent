# AIOps Agent

AIOps Agent 是一个面向服务器与日志排障场景的智能运维诊断与监控服务。

用户通过 Vue 3 页面或 REST API 用自然语言提问“服务器状态如何、日志为什么报错、磁盘满了怎么办”，系统自动调用系统状态、日志检索与排障手册 RAG 工具，输出带来源与处置建议的回答。

## 功能

- FastAPI 会话与多轮对话 API
- Mock LLM / OpenAI 兼容模型双模式
- Agent 工具调用：系统状态、进程/端口、日志检索、排障手册检索
- 排障手册上传、分块、本地向量化与 RAG 来源引用
- API Key 鉴权与限流
- 结构化日志与 Prometheus 指标
- Vue 3 演示前端（对话、知识库、系统状态）
- pytest 自动化测试、Docker 与 GitHub Actions CI

## 项目结构

```text
app/
├── main.py             # 应用入口
├── config.py           # 环境配置
├── schemas.py          # Pydantic 模型
├── db.py               # SQLite 存储
├── security.py         # 鉴权与限流
├── logging_config.py   # JSON 日志
├── monitoring.py       # 系统状态采集
├── rag.py              # 文档分块、向量、检索
├── tools.py            # 工具注册与诊断工具
├── agent.py            # Agent 循环与 LLM 适配
└── api.py              # REST API
web/                    # Vue 3 演示前端
tests/                  # pytest 测试
docs/                   # 需求与设计文档
```

## 本地运行（Windows）

```powershell
cd aiops-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

打开：

- Vue 页面：<http://127.0.0.1:8000/ui/>
- Swagger API：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/healthz>
- Prometheus 指标：<http://127.0.0.1:8000/metrics>

## API 示例

默认开发 Key 为 `dev-key-change-me`，正式使用前通过 `APP_API_KEY` 修改。

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d '{"message":"查看服务器状态"}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/documents \
  -H "X-API-Key: dev-key-change-me" \
  -F "file=@disk-manual.md"
```

```bash
curl -X POST http://127.0.0.1:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d '{"query":"磁盘满了怎么处理","top_k":3}'
```

## 连接真实模型

默认使用 Mock 模型，无 Key 即可测试。使用 OpenAI 兼容接口：

```powershell
$env:LLM_PROVIDER="openai"
$env:LLM_API_KEY="sk-xxx"
$env:LLM_BASE_URL="https://api.deepseek.com/v1"
$env:LLM_MODEL="deepseek-chat"
uvicorn app.main:app --reload --port 8000
```

完整配置项见 `.env.example`。

## 测试

```bash
pytest -q
```

## Docker

```bash
docker compose up --build
```

默认访问 <http://127.0.0.1:8000/ui/>。

## 设计文档

- 需求规格：`docs/01-requirements.md`
- 系统设计：`docs/02-system-design.md`
