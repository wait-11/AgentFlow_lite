# AgentFlow Lite 后端 MVP

本后端 MVP 是一个独立的 FastAPI 应用，位于项目根目录的 `backend/`。
它把现有 Windows 可运行的 AgentFlow solver 包装成产品化 HTTP API，方便后续接前端工作台。

## 启动后端

推荐使用 Windows 一键启动脚本：

```powershell
.\start_backend.bat
```

启动成功后打开：

```text
http://127.0.0.1:8010/
```

后端也保留 Swagger 文档：

```text
http://127.0.0.1:8010/docs
```

## 在 PyCharm 中启动

1. 打开 `scripts/start_backend.py`。
2. 右键文件，选择 `Run 'start_backend'`。
3. 启动后访问 `http://127.0.0.1:8010/docs`。

可选参数：

```powershell
.\start_backend.bat --port 8011
.\start_backend.bat --reload
.\start_backend.bat --keep-proxy
```

说明：

- 默认端口是 `8010`。
- 默认会清理 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 等代理变量，避免 DashScope 请求被错误代理到本地端口。
- 如果确实需要使用系统代理，请加 `--keep-proxy`。

## 手动启动

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8010 --reload
```

## 主要接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/models` | 获取内置模型预设 |
| `GET` | `/api/tools` | 获取前端可展示的工具列表 |
| `POST` | `/api/runs` | 创建一次 AgentFlow 推理任务 |
| `GET` | `/api/runs` | 获取当前内存中的任务列表 |
| `GET` | `/api/runs/{run_id}` | 获取指定任务状态、事件和结果 |
| `GET` | `/api/runs/{run_id}/events` | 通过 SSE 流式查看任务事件 |

## 前端工作台

项目根目录新增了零构建静态页面：

```text
frontend/index.html
frontend/styles.css
frontend/app.js
```

启动后端后访问 `http://127.0.0.1:8010/`，可以在页面里选择模型、工具、推理参数，提交任务，并查看 SSE 事件流、最终答案和最近任务。

## 创建任务示例

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8010/api/runs `
  -ContentType "application/json" `
  -Body '{
    "query": "杭州最有名的湖叫什么？",
    "llm_engine_name": "dashscope",
    "enabled_tools": ["Base_Generator_Tool"],
    "tool_engine": ["self"],
    "model_engine": ["trainable", "dashscope", "dashscope", "dashscope"],
    "max_steps": 1,
    "verbose": false
  }'
```

创建成功后会返回：

```json
{
  "run_id": "run-...",
  "status": "queued",
  "events_url": "/api/runs/run-.../events",
  "detail_url": "/api/runs/run-..."
}
```

## 查询结果

`POST /api/runs` 只代表任务已提交，推理会在后台线程执行。
如果返回中看到：

```json
"status": "running",
"output": null
```

说明任务还没完成。需要稍后重新请求：

```powershell
Invoke-RestMethod http://127.0.0.1:8010/api/runs/<run_id>
```

完成后会看到：

```json
"status": "completed",
"output": {
  "direct_output": "..."
}
```

最终答案在：

```text
output.direct_output
```

## 查看事件流

浏览器或前端可以访问：

```text
http://127.0.0.1:8010/api/runs/<run_id>/events
```

当前 MVP 事件包括：

```text
queued
started
solver_constructing
solver_ready
completed
failed
```

后续可以继续把 `query_analysis`、`action_predictor`、`tool_result`、`verifier` 等 AgentFlow 内部步骤改成实时事件，供前端时间线展示。

## 当前限制

- 任务状态保存在内存中，重启后历史任务会清空。
- solver 当前仍然是同步执行，只是放到了后台线程中。
- 当前 SSE 主要覆盖任务生命周期，还不是完整的逐步骤流式推理轨迹。
- `Google_Search_Tool` 需要 `GOOGLE_API_KEY`。
- `Wikipedia_Search_Tool` 当前依赖英文 Wikipedia 和部分 OpenAI 配置，建议先用 `Base_Generator_Tool` 测主链路。

## 目录结构

```text
backend/                  后端 API 层
backend/api.py            FastAPI 路由入口
backend/run_manager.py    后台任务运行与状态管理
backend/schemas.py        请求、响应、事件等数据结构
scripts/start_backend.py  PyCharm 和命令行启动入口
start_backend.bat         Windows 一键启动脚本
agentflow/agentflow/      AgentFlow 算法与推理核心
```
