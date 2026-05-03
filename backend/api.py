from __future__ import annotations

import json
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .run_manager import RunManager
from .schemas import ModelPreset, RunCreatedResponse, RunRecord, RunRequest, ToolInfo


TOOLS = [
    ToolInfo(
        name="Base_Generator_Tool",
        display_name="通用生成工具",
        description="用 LLM 直接完成通用问答、总结和轻量推理。",
        requires_api_key=["DASHSCOPE_API_KEY or OPENAI_API_KEY"],
        recommended_engine="self",
    ),
    ToolInfo(
        name="Python_Coder_Tool",
        display_name="Python 计算工具",
        description="生成并执行受限 Python 代码，适合数学和简单计算。",
        requires_api_key=["DASHSCOPE_API_KEY or OPENAI_API_KEY"],
        recommended_engine="self",
    ),
    ToolInfo(
        name="Google_Search_Tool",
        display_name="Google 搜索工具",
        description="使用 Gemini grounding 搜索公开互联网信息。",
        requires_api_key=["GOOGLE_API_KEY"],
        recommended_engine="Default",
    ),
    ToolInfo(
        name="Wikipedia_Search_Tool",
        display_name="Wikipedia RAG 工具",
        description="检索 Wikipedia 并抽取相关页面信息。",
        requires_api_key=["OPENAI_API_KEY"],
        recommended_engine="self",
    ),
]

MODEL_PRESETS = [
    ModelPreset(name="dashscope", provider="Alibaba Cloud DashScope", description="默认 Qwen 推理后端。"),
    ModelPreset(name="dashscope-qwen-plus", provider="Alibaba Cloud DashScope", description="DashScope Qwen Plus。"),
    ModelPreset(name="deepseek-chat", provider="DeepSeek", description="DeepSeek Chat API。"),
    ModelPreset(name="gpt-4o", provider="OpenAI", description="OpenAI GPT-4o。"),
    ModelPreset(name="vllm-local-model", provider="OpenAI-compatible", description="本地 vLLM/OpenAI-compatible 服务。", supports_base_url=True),
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgentFlow Lite MVP API",
        version="0.1.0",
        description="Product-facing API wrapper around the Windows-compatible AgentFlow solver.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = RunManager()
    app.state.run_manager = manager

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/tools", response_model=List[ToolInfo])
    async def list_tools() -> List[ToolInfo]:
        return TOOLS

    @app.get("/api/models", response_model=List[ModelPreset])
    async def list_models() -> List[ModelPreset]:
        return MODEL_PRESETS

    @app.post("/api/runs", response_model=RunCreatedResponse, status_code=202)
    async def create_run(payload: RunRequest) -> RunCreatedResponse:
        record = manager.create_run(payload)
        return RunCreatedResponse(
            run_id=record.run_id,
            status=record.status,
            events_url=f"/api/runs/{record.run_id}/events",
            detail_url=f"/api/runs/{record.run_id}",
        )

    @app.get("/api/runs", response_model=List[RunRecord])
    async def list_runs() -> List[RunRecord]:
        return manager.list_runs()

    @app.get("/api/runs/{run_id}", response_model=RunRecord)
    async def get_run(run_id: str) -> RunRecord:
        try:
            return manager.get_run(run_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    @app.get("/api/runs/{run_id}/events")
    async def stream_run_events(run_id: str, after: int = Query(default=0, ge=0)) -> StreamingResponse:
        async def event_source():
            try:
                async for event in manager.iter_events(run_id, after_event_id=after):
                    payload = event.model_dump(mode="json")
                    yield f"id: {event.event_id}\nevent: {event.type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
            except KeyError:
                error_payload = {"detail": f"Run '{run_id}' not found."}
                yield f"event: error\ndata: {json.dumps(error_payload, ensure_ascii=False)}\n\n"

        return StreamingResponse(event_source(), media_type="text/event-stream")

    return app


app = create_app()
