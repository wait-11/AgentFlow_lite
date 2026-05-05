# AgentFlow Lite — 推理流程运行指南

基于 [AgentFlow](https://github.com/lupantech/AgentFlow) (ICLR 2026) 的 Windows 推理适配版本。

## 环境要求

- Python 3.11
- Windows / Linux / macOS
- 至少一个 LLM API Key（DashScope 或 OpenAI）

## 1. 安装

### macOS / Linux

```bash
# 安装 uv 包管理器
python3 -m pip install uv

# 创建虚拟环境
uv venv -p 3.11

# 安装依赖（跳过 vllm，推理不需要）
uv pip install -r agentflow/requirements_inference.txt --python .venv/bin/python

# 安装项目级依赖
uv pip install aiohttp flask fastapi uvicorn psutil setproctitle graphviz agentops dashscope fire --python .venv/bin/python

# 安装 agentflow 项目本身（dev 模式）
uv pip install -e . --python .venv/bin/python
```

### Windows PowerShell

```powershell
# 安装 uv 包管理器
python -m pip install uv

# 创建虚拟环境
uv venv -p 3.11

# 安装依赖（跳过 vllm，推理不需要）
uv pip install -r agentflow/requirements_inference.txt --python .venv\Scripts\python.exe

# 安装项目级依赖
uv pip install aiohttp flask fastapi uvicorn psutil setproctitle graphviz agentops dashscope fire --python .venv\Scripts\python.exe

# 安装 agentflow 项目本身（dev 模式）
uv pip install -e . --python .venv\Scripts\python.exe
```

> **注意**：如果 `requirements_inference.txt` 不存在，手动从 `agentflow/requirements.txt` 中移除 `vllm==0.8.5` 一行后使用。

## 2. 配置 API Key

```bash
# 从模板创建 .env 文件
cp agentflow/.env.template agentflow/.env

# 编辑 agentflow/.env，至少填入以下之一：
#   DASHSCOPE_API_KEY=sk-xxxxxx    (阿里百炼，推荐)
#   OPENAI_API_KEY=sk-xxxxxx       (OpenAI)
```

## 3. 运行

### 方式一：快速演示

macOS / Linux:

```bash
PYTHONIOENCODING=utf-8 .venv/bin/python quick_start.py
```

Windows PowerShell:

```powershell
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\python.exe quick_start.py
```

### 方式二：跑单道 Benchmark 题

macOS / Linux:

```bash
cd test
PYTHONIOENCODING=utf-8 ../.venv/bin/python solve.py \
  --index 0 \
  --task bamboogle \
  --data_file bamboogle/data/data.json \
  --llm_engine_name dashscope \
  --enabled_tools "Base_Generator_Tool,Wikipedia_Search_Tool" \
  --tool_engine "dashscope,dashscope" \
  --model_engine "trainable,dashscope,dashscope,dashscope" \
  --max_steps 10 \
  --max_time 300 \
  --temperature 0.0
```

Windows PowerShell:

```powershell
cd test
$env:PYTHONIOENCODING = "utf-8"
..\.venv\Scripts\python.exe solve.py `
  --index 0 `
  --task bamboogle `
  --data_file bamboogle/data/data.json `
  --llm_engine_name dashscope `
  --enabled_tools "Base_Generator_Tool,Wikipedia_Search_Tool" `
  --tool_engine "dashscope,dashscope" `
  --model_engine "trainable,dashscope,dashscope,dashscope" `
  --max_steps 10 `
  --max_time 300 `
  --temperature 0.0
```

### 参数说明

| 参数 | 含义 | 可选值 |
|------|------|--------|
| `--llm_engine_name` | 主 LLM 引擎 | `dashscope`, `gpt-4o`, `deepseek-chat` |
| `--enabled_tools` | 启用的工具列表 | `Base_Generator_Tool`, `Wikipedia_Search_Tool`, `Google_Search_Tool`, `Python_Coder_Tool` |
| `--tool_engine` | 每个工具的引擎 | 与 enabled_tools 一一对应 |
| `--model_engine` | 4个Agent的引擎 | `[planner_main, planner_fixed, verifier, executor]` |
| `--index` | 题目序号 | 0 ~ N-1 |
| `--max_steps` | 最大推理步数 | 默认 10 |
| `--max_time` | 最大推理时间(秒) | 默认 300 |

### 可用的 Benchmark 任务

```
test/bamboogle/    - 125题，多跳搜索推理
test/hotpotqa/     - 多跳问答
test/musique/      - 多跳推理
test/2wiki/        - 双实体问答
test/aime24/       - 数学推理
test/gpqa/         - 科学推理
test/gaia/         - Agent 推理
test/medqa/        - 医学问答
test/gameof24/     - 24点游戏
test/amc23/        - 数学竞赛
```

## 4. 平台注意事项

- Windows 建议设置 `PYTHONIOENCODING=utf-8`，否则 emoji 可能导致 GBK 编码报错
- vllm 无法在 Windows 上安装（仅支持 Linux/macOS），推理不需要它
- Windows 虚拟环境激活路径：`.venv\Scripts\activate`
- macOS / Linux 虚拟环境激活路径：`.venv/bin/activate`

## 5. 推理流程架构

```
问题输入
    │
    ▼
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│ Planner │───▶│ Executor │───▶│ Memory  │───▶│ Verifier │
│ 分析问题 │    │ 调用工具  │    │ 记录结果 │    │ 判断停止  │
│ 选择工具 │    │ 执行命令  │    │          │    │          │
└─────────┘    └──────────┘    └─────────┘    └────┬─────┘
     ▲                                              │
     └──────────── CONTINUE (继续) ◀────────────────┘
                        │
                        ▼ STOP (停止)
                  ┌──────────┐
                  │ 输出答案  │
                  └──────────┘
```

## 参考

- 原项目: [lupantech/AgentFlow](https://github.com/lupantech/AgentFlow)
- 论文: [In-the-Flow Agentic System Optimization](https://arxiv.org/abs/2510.05592) (ICLR 2026)
