from __future__ import annotations

import asyncio
import json
import sys
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from agentflow.agentflow.solver import construct_solver

from .schemas import RunEvent, RunRecord, RunRequest, RunStatus


if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _make_json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(key): _make_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_make_json_safe(item) for item in value]
        return str(value)


class RunManager:
    def __init__(self, max_workers: int = 2):
        self._runs: Dict[str, RunRecord] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="agentflow-run")

    def create_run(self, request: RunRequest) -> RunRecord:
        run_id = f"run-{uuid.uuid4().hex}"
        now = _utcnow()
        record = RunRecord(
            run_id=run_id,
            status=RunStatus.QUEUED,
            request=request,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._runs[run_id] = record
        self._emit(run_id, "queued", "Run queued.", {"query": request.query})
        self._executor.submit(self._run_solver, run_id)
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> RunRecord:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            return self._runs[run_id].model_copy(deep=True)

    def list_runs(self) -> List[RunRecord]:
        with self._lock:
            return [record.model_copy(deep=True) for record in self._runs.values()]

    async def iter_events(self, run_id: str, after_event_id: int = 0) -> Iterable[RunEvent]:
        last_seen = after_event_id
        terminal_statuses = {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}
        while True:
            with self._lock:
                if run_id not in self._runs:
                    raise KeyError(run_id)
                record = self._runs[run_id]
                pending = [
                    event.model_copy(deep=True)
                    for event in record.events
                    if event.event_id > last_seen
                ]
                is_terminal = record.status in terminal_statuses

            for event in pending:
                last_seen = event.event_id
                yield event

            if is_terminal and not pending:
                return

            await asyncio.sleep(0.5)

    def get_events(self, run_id: str, after_event_id: int = 0) -> List[RunEvent]:
        with self._lock:
            if run_id not in self._runs:
                raise KeyError(run_id)
            return [
                event.model_copy(deep=True)
                for event in self._runs[run_id].events
                if event.event_id > after_event_id
            ]

    def _run_solver(self, run_id: str) -> None:
        try:
            request = self.get_run(run_id).request
            self._set_status(run_id, RunStatus.RUNNING, started_at=_utcnow())
            self._emit(run_id, "started", "Solver started.", {"llm_engine_name": request.llm_engine_name})

            tool_engine = request.tool_engine
            if tool_engine is None:
                tool_engine = ["self" for _ in request.enabled_tools]

            self._emit(
                run_id,
                "solver_constructing",
                "Constructing AgentFlow solver.",
                {
                    "enabled_tools": request.enabled_tools,
                    "tool_engine": tool_engine,
                    "model_engine": request.model_engine,
                },
            )

            solver = construct_solver(
                llm_engine_name=request.llm_engine_name,
                enabled_tools=request.enabled_tools,
                tool_engine=tool_engine,
                model_engine=request.model_engine,
                output_types=request.output_types,
                max_steps=request.max_steps,
                max_time=request.max_time,
                max_tokens=request.max_tokens,
                root_cache_dir=str(Path("solver_cache") / run_id),
                verbose=request.verbose,
                base_url=request.base_url,
                temperature=request.temperature,
            )
            self._emit(run_id, "solver_ready", "Solver constructed.")
            output = solver.solve(request.query, image_path=request.image_path)

            safe_output = _make_json_safe(output)
            self._set_status(
                run_id,
                RunStatus.COMPLETED,
                output=safe_output,
                finished_at=_utcnow(),
            )
            self._emit(
                run_id,
                "completed",
                "Run completed.",
                {
                    "step_count": safe_output.get("step_count"),
                    "execution_time": safe_output.get("execution_time"),
                    "direct_output": safe_output.get("direct_output"),
                },
            )
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            self._set_status(run_id, RunStatus.FAILED, error=error, finished_at=_utcnow())
            self._emit(
                run_id,
                "failed",
                "Run failed.",
                {"error": error, "traceback": traceback.format_exc()},
            )

    def _set_status(self, run_id: str, status: RunStatus, **updates: Any) -> None:
        with self._lock:
            record = self._runs[run_id]
            data = record.model_dump()
            data.update(updates)
            data["status"] = status
            data["updated_at"] = _utcnow()
            self._runs[run_id] = RunRecord(**data)

    def _emit(self, run_id: str, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        with self._lock:
            record = self._runs[run_id]
            event = RunEvent(
                event_id=len(record.events) + 1,
                run_id=run_id,
                type=event_type,
                message=message,
                data=_make_json_safe(data or {}),
            )
            record.events.append(event)
            record.updated_at = _utcnow()
