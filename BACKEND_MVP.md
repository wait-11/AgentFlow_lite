# AgentFlow Lite Backend MVP

本后端 MVP 是一个独立的 FastAPI 应用，位于项目根目录的 `backend/`。它把现有 Windows 可运行的 AgentFlow solver 包装成 HTTP API，并通过 SSE 将 AgentFlow 的执行轨迹实时推给前端。

当前目标不是重写 AgentFlow 算法，而是把 solver 内部的 Planner、Executor、Memory、Verifier 执行过程暴露出来，方便前端做轨迹可视化，也方便后续做 benchmark、误差分析和训练数据导出。

## 启动后端

推荐使用 Windows 一键启动脚本：

```powershell
.\start_backend.bat
```

启动成功后访问：

```text
http://127.0.0.1:8010/
```

Swagger API 文档：

```text
http://127.0.0.1:8010/docs
```

健康检查：

```text
http://127.0.0.1:8010/api/health
```

## PyCharm 启动

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
- 默认会清理 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 等代理变量，避免 DashScope / OpenAI 请求被错误代理到本地端口。
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
| `GET` | `/api/runs/{run_id}/events` | 通过 SSE 实时查看任务事件流 |

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

创建成功后返回：

```json
{
  "run_id": "run-...",
  "status": "queued",
  "events_url": "/api/runs/run-.../events",
  "detail_url": "/api/runs/run-..."
}
```

## 查询结果

`POST /api/runs` 只代表任务已经提交，推理会在后台线程中执行。如果返回中看到：

```json
{
  "status": "running",
  "output": null
}
```

说明任务尚未完成，可以稍后查询：

```powershell
Invoke-RestMethod http://127.0.0.1:8010/api/runs/<run_id>
```

完成后会看到：

```json
{
  "status": "completed",
  "output": {
    "direct_output": "...",
    "final_output": "...",
    "memory": {},
    "step_count": 1,
    "execution_time": 12.34
  }
}
```

最终简短答案通常在：

```text
output.direct_output
```

详细答案通常在：

```text
output.final_output
```

## SSE 事件流

浏览器或前端可以访问：

```text
http://127.0.0.1:8010/api/runs/<run_id>/events
```

SSE 每条事件都会包含：

```json
{
  "event_id": 1,
  "run_id": "run-...",
  "type": "planner_action",
  "message": "Planner selected the next action.",
  "timestamp": "2026-05-07T10:00:00Z",
  "data": {}
}
```

服务端发送格式为标准 SSE：

```text
id: 1
event: planner_action
data: {"event_id":1,"run_id":"run-...","type":"planner_action","message":"...","data":{}}
```

## 任务生命周期事件

这些事件描述 run 的整体状态：

| 事件 | 含义 |
| --- | --- |
| `queued` | 任务已进入队列 |
| `started` | 后台 solver 开始执行 |
| `solver_constructing` | 正在构造 AgentFlow solver |
| `solver_ready` | solver 构造完成 |
| `completed` | 任务完成 |
| `failed` | 任务失败 |

## AgentFlow 轨迹事件

这些事件来自 `agentflow/agentflow/solver.py` 内部，用于前端轨迹可视化：

| 事件 | 模块 | 说明 |
| --- | --- | --- |
| `query_received` | Solver | solver 收到原始问题和运行参数 |
| `base_response` | Planner | 生成 baseline response，仅当 `output_types` 包含 `base` 时出现 |
| `query_analysis` | Planner | Step 0 问题分析 |
| `planner_action` | Planner | Planner 选择下一步 action、sub-goal 和 tool |
| `tool_unavailable` | Executor | Planner 选择了不可用工具 |
| `executor_command` | Executor | Executor 生成具体工具调用命令 |
| `tool_result` | Executor | 工具执行结果 |
| `memory_update` | Memory | Memory 记录当前 step 的 action 和结果 |
| `verifier_result` | Verifier | Verifier 判断继续还是停止 |
| `final_output` | Planner | 生成详细最终答案 |
| `direct_output` | Planner | 生成简短最终答案 |

## 关键事件数据结构

`query_analysis`：

```json
{
  "step": 0,
  "module": "planner",
  "analysis": "...",
  "duration": 1.23
}
```

`planner_action`：

```json
{
  "step": 1,
  "module": "planner",
  "raw_output": "...",
  "context": "...",
  "sub_goal": "...",
  "tool_name": "Wikipedia_Search_Tool",
  "duration": 1.23
}
```

`executor_command`：

```json
{
  "step": 1,
  "module": "executor",
  "tool_name": "Wikipedia_Search_Tool",
  "raw_output": "...",
  "analysis": "...",
  "explanation": "...",
  "command": "...",
  "duration": 1.23
}
```

`tool_result`：

```json
{
  "step": 1,
  "module": "executor",
  "tool_name": "Wikipedia_Search_Tool",
  "command": "...",
  "result": {},
  "duration": 1.23
}
```

`memory_update`：

```json
{
  "step": 1,
  "module": "memory",
  "tool_name": "Wikipedia_Search_Tool",
  "sub_goal": "...",
  "command": "...",
  "result": {},
  "memory": {}
}
```

`verifier_result`：

```json
{
  "step": 1,
  "module": "verifier",
  "raw_output": "...",
  "analysis": "...",
  "conclusion": "STOP",
  "duration": 1.23
}
```

## 前端工作台

项目根目录有一个零构建静态前端：

```text
frontend/index.html
frontend/styles.css
frontend/app.js
```

启动后端后访问：

```text
http://127.0.0.1:8010/
```

当前前端可以提交任务、查看任务状态、展示事件流和最终答案。下一步建议基于新增的 AgentFlow 轨迹事件升级为：

- Timeline：按 step 展示 `query_analysis`、`planner_action`、`executor_command`、`tool_result`、`verifier_result`。
- Memory Panel：监听 `memory_update`，展示当前 accumulated memory。
- Final Answer：监听 `final_output` / `direct_output`。
- Raw JSON：保留事件原始 JSON，方便调试和复现实验。

## 当前限制

- 任务状态仍保存在内存中，后端重启后历史任务会清空。
- solver 仍是同步执行，只是放到了后台线程中。
- SSE 已经支持 AgentFlow 轨迹事件，但前端还需要进一步做结构化展示。
- `Google_Search_Tool` 需要 `GOOGLE_API_KEY`。
- `Wikipedia_Search_Tool` 依赖英文 Wikipedia 和部分 OpenAI 配置，建议先用 `Base_Generator_Tool` 测主链路。
- 轨迹目前还没有持久化为 `events.jsonl`，后续 benchmark 和训练数据导出需要补这一层。

## 目录结构

```text
backend/                  后端 API 层
backend/api.py            FastAPI 路由入口
backend/run_manager.py    后台任务运行、状态管理、SSE 事件转发
backend/schemas.py        请求、响应、事件等数据结构
scripts/start_backend.py  PyCharm 和命令行启动入口
start_backend.bat         Windows 一键启动脚本
agentflow/agentflow/      AgentFlow 算法与推理核心
frontend/                 静态前端工作台
```
