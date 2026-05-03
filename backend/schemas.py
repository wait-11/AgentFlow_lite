from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


DEFAULT_ENABLED_TOOLS = ["Base_Generator_Tool"]
DEFAULT_MODEL_ENGINE = ["trainable", "dashscope", "dashscope", "dashscope"]


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User task or question.")
    image_path: Optional[str] = Field(default=None, description="Optional local image path.")
    llm_engine_name: str = Field(default="dashscope")
    enabled_tools: List[str] = Field(default_factory=lambda: DEFAULT_ENABLED_TOOLS.copy(), min_length=1)
    tool_engine: Optional[List[str]] = Field(default=None)
    model_engine: List[str] = Field(default_factory=lambda: DEFAULT_MODEL_ENGINE.copy(), min_length=4, max_length=4)
    output_types: str = Field(default="final,direct")
    max_steps: int = Field(default=6, ge=1, le=30)
    max_time: int = Field(default=300, ge=1, le=3600)
    max_tokens: int = Field(default=4000, ge=256, le=32000)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    verbose: bool = Field(default=False)
    base_url: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_engine_lists(self) -> "RunRequest":
        if self.tool_engine is not None and len(self.tool_engine) != len(self.enabled_tools):
            raise ValueError("tool_engine must have the same length as enabled_tools.")
        return self


class RunEvent(BaseModel):
    event_id: int
    run_id: str
    type: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = Field(default_factory=dict)


class RunRecord(BaseModel):
    run_id: str
    status: RunStatus
    request: RunRequest
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    events: List[RunEvent] = Field(default_factory=list)


class RunCreatedResponse(BaseModel):
    run_id: str
    status: RunStatus
    events_url: str
    detail_url: str


class ToolInfo(BaseModel):
    name: str
    display_name: str
    description: str
    requires_api_key: List[str] = Field(default_factory=list)
    recommended_engine: str = "Default"


class ModelPreset(BaseModel):
    name: str
    provider: str
    description: str
    supports_base_url: bool = False
