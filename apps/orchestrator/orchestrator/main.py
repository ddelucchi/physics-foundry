"""Physics Foundry FastAPI orchestrator.

The service is an active prototype. Production mode must never report a
successful render when a required generation/render capability is not wired.
Deterministic fixture mode exists only for testing orchestration semantics.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .core.capabilities import FIXTURE_MODE_ENV, capability_matrix, fixture_mode_enabled
from .core.dsl_models import (
    LogLevel,
    PipelineLogEntry,
    PipelineStatus,
    PipelineStatusType,
    SceneRequest,
)
from .core.fixtures import build_fixture_plan
from .core.observability import (
    observability_manager,
    operation_duration_seconds,
    pipeline_operations_total,
    setup_observability_stack,
    system_monitor,
)
from .core.sandbox import execute_safe_code, sandbox_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SystemStatus(BaseModel):
    """System and capability status."""

    status: str
    timestamp: datetime
    version: str
    mode: str
    gpu_available: bool = False
    sandbox_ready: bool = False
    quality_gates_enabled: bool = False
    capabilities: Dict[str, bool] = Field(default_factory=dict)
    observability: Dict[str, bool] = Field(default_factory=dict)


active_pipelines: Dict[str, PipelineStatus] = {}
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""

    del app
    logger.info("Starting Physics Foundry Orchestrator")

    setup_observability_stack(
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
        sentry_dsn=os.getenv("SENTRY_DSN"),
    )

    monitor_task = asyncio.create_task(system_monitor.start_monitoring())
    logger.info(
        "Physics Foundry Orchestrator ready in %s mode",
        "fixture" if fixture_mode_enabled() else "prototype",
    )

    try:
        yield
    finally:
        logger.info("Shutting down Physics Foundry Orchestrator")
        system_monitor.stop_monitoring()
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        sandbox_manager.cleanup_all()


app = FastAPI(
    title="Physics Foundry Orchestrator",
    version="0.3.0",
    description="Prototype orchestration service for local-first physics-media workflows",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Report service liveness, not renderer readiness."""

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "mode": "fixture" if fixture_mode_enabled() else "prototype",
    }


@app.get("/status", response_model=SystemStatus)
async def system_status():
    """Return explicit dependency/capability status."""

    capabilities = capability_matrix()
    return SystemStatus(
        status="prototype",
        timestamp=datetime.utcnow(),
        version="0.3.0",
        mode="fixture" if fixture_mode_enabled() else "prototype",
        gpu_available=capabilities["nvidia_smi"],
        sandbox_ready=capabilities["sandbox_execution_supported"],
        quality_gates_enabled=capabilities["frame_qa_python"],
        capabilities=capabilities,
        observability={
            "prometheus": True,
            "tracing": observability_manager.tracing_configured,
            "sentry": observability_manager.sentry_configured,
        },
    )


@app.get("/capabilities")
async def capabilities():
    """Expose dependency readiness independently of service liveness."""

    return {
        "mode": "fixture" if fixture_mode_enabled() else "prototype",
        "capabilities": capability_matrix(),
        "note": (
            "A capability flag reports dependency availability only; it does not "
            "by itself establish an end-to-end verified renderer path."
        ),
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""

    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/pipeline/create")
async def create_pipeline(request: SceneRequest, background_tasks: BackgroundTasks):
    """Create a pipeline job and process it asynchronously."""

    pipeline_id = f"pipeline_{int(datetime.utcnow().timestamp() * 1_000_000)}"
    pipeline_status = PipelineStatus(
        pipeline_id=pipeline_id,
        status=PipelineStatusType.PLANNING,
        current_step=0,
        total_steps=3 if fixture_mode_enabled() else 1,
        progress=0.0,
        current_operation="Initializing pipeline",
        logs=[
            PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.INFO,
                message=f"Pipeline created for topic: {request.topic}",
                component="orchestrator",
                metadata={
                    "topic": request.topic,
                    "duration": request.duration,
                    "fixture_mode": fixture_mode_enabled(),
                },
            )
        ],
    )

    active_pipelines[pipeline_id] = pipeline_status
    background_tasks.add_task(process_pipeline, pipeline_id, request)

    await broadcast_pipeline_event(
        {
            "type": "pipeline_created",
            "pipeline_id": pipeline_id,
            "data": pipeline_status.model_dump(),
        }
    )
    pipeline_operations_total.labels(operation="create_pipeline", status="started").inc()

    return {
        "pipeline_id": pipeline_id,
        "status": "created",
        "mode": "fixture" if fixture_mode_enabled() else "prototype",
    }


@app.get("/api/pipeline/{pipeline_id}/status", response_model=PipelineStatus)
async def get_pipeline_status(pipeline_id: str):
    """Get pipeline status."""

    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return active_pipelines[pipeline_id]


@app.post("/api/pipeline/{pipeline_id}/quality-check")
async def run_quality_check(pipeline_id: str, frame_paths: List[str]):
    """Run measured frame statistics when the optional QA stack is installed."""

    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if not capability_matrix()["frame_qa_python"]:
        raise HTTPException(
            status_code=503,
            detail=(
                "Frame QA is unavailable. Install the orchestrator QA extra "
                "before requesting measured frame analysis."
            ),
        )

    from .core.quality_gates import default_quality_gate

    try:
        frame_paths_obj = [Path(path) for path in frame_paths]
        missing = [str(path) for path in frame_paths_obj if not path.exists()]
        if missing:
            raise HTTPException(
                status_code=400,
                detail={"message": "Frame paths do not exist", "missing": missing},
            )

        gate_passed, analyses = await default_quality_gate.check_frame_sequence(frame_paths_obj)
        pipeline = active_pipelines[pipeline_id]
        pipeline.logs.append(
            PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.INFO if gate_passed else LogLevel.WARN,
                message=f"Frame heuristic gate {'passed' if gate_passed else 'failed'}",
                component="quality_gate",
                metadata={"frames_analyzed": len(analyses), "gate_passed": gate_passed},
            )
        )

        payload = {
            "pipeline_id": pipeline_id,
            "gate_passed": gate_passed,
            "frame_analyses": [analysis.model_dump() for analysis in analyses],
        }
        await broadcast_pipeline_event(
            {
                "type": "quality_check_complete",
                "pipeline_id": pipeline_id,
                "data": payload,
            }
        )
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Quality check failed")
        raise HTTPException(status_code=500, detail=f"Quality check failed: {exc}") from exc


@app.post("/api/code/execute")
async def execute_code_safely(
    code: str,
    code_type: str = "python",
    timeout: Optional[float] = 60.0,
):
    """Execute code through the repository sandbox boundary."""

    with operation_duration_seconds.labels(operation="code_execution").time():
        try:
            result = await execute_safe_code(code, code_type, timeout)
            metric_status = str(result.get("status", "error"))
            pipeline_operations_total.labels(
                operation="code_execution",
                status=metric_status,
            ).inc()
            return result
        except Exception as exc:
            logger.exception("Code execution failed")
            pipeline_operations_total.labels(operation="code_execution", status="error").inc()
            raise HTTPException(status_code=500, detail=f"Code execution failed: {exc}") from exc


@app.websocket("/ws/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: str):
    """WebSocket connection for real-time pipeline updates."""

    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        if pipeline_id in active_pipelines:
            await websocket.send_json(
                {
                    "type": "pipeline_status",
                    "pipeline_id": pipeline_id,
                    "data": active_pipelines[pipeline_id].model_dump(),
                }
            )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        logger.info("WebSocket disconnected for pipeline %s", pipeline_id)


async def broadcast_pipeline_event(event: Dict):
    """Broadcast an event to live websocket clients."""

    for websocket in websocket_connections.copy():
        try:
            await websocket.send_json(event)
        except Exception:
            if websocket in websocket_connections:
                websocket_connections.remove(websocket)


async def process_fixture_pipeline(pipeline_id: str, request: SceneRequest):
    """Exercise deterministic orchestration without pretending to render media."""

    await update_pipeline_status(
        pipeline_id,
        PipelineStatusType.PLANNING,
        1,
        3,
        "Fixture: validating bounded request",
    )

    fixture_plan = build_fixture_plan(request)
    pipeline = active_pipelines[pipeline_id]
    pipeline.logs.append(
        PipelineLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            message="Fixture scene plan created",
            component="fixture",
            metadata=fixture_plan,
        )
    )

    await update_pipeline_status(
        pipeline_id,
        PipelineStatusType.SCRIPTING,
        2,
        3,
        "Fixture: exercising orchestration state transition",
    )
    await asyncio.sleep(0)

    await update_pipeline_status(
        pipeline_id,
        PipelineStatusType.FIXTURE_COMPLETE,
        3,
        3,
        "Fixture orchestration complete; no media was rendered",
    )
    pipeline_operations_total.labels(operation="process_pipeline", status="fixture_complete").inc()


async def process_pipeline(pipeline_id: str, request: SceneRequest):
    """Process a job without converting unimplemented stages into fake success."""

    try:
        async with observability_manager.trace_operation(
            "process_pipeline",
            {
                "pipeline_id": pipeline_id,
                "topic": request.topic,
                "fixture_mode": fixture_mode_enabled(),
            },
        ):
            if fixture_mode_enabled():
                await process_fixture_pipeline(pipeline_id, request)
                return

            message = (
                "Real prompt-to-render execution is not yet wired as a verified path. "
                f"Set {FIXTURE_MODE_ENV}=1 only for deterministic orchestration tests; "
                "fixture completion never represents a rendered video."
            )
            await update_pipeline_status(
                pipeline_id,
                PipelineStatusType.UNSUPPORTED,
                1,
                1,
                message,
                level=LogLevel.WARN,
            )
            pipeline_operations_total.labels(operation="process_pipeline", status="unsupported").inc()
    except Exception as exc:
        logger.exception("Pipeline %s failed", pipeline_id)
        pipeline = active_pipelines[pipeline_id]
        pipeline.status = PipelineStatusType.ERROR
        pipeline.current_operation = f"Error: {exc}"
        pipeline.updated_at = datetime.utcnow()
        pipeline.logs.append(
            PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.ERROR,
                message=str(exc),
                component="orchestrator",
                metadata={"error_type": type(exc).__name__},
            )
        )
        await broadcast_pipeline_event(
            {
                "type": "pipeline_error",
                "pipeline_id": pipeline_id,
                "data": {"error": str(exc)},
            }
        )
        pipeline_operations_total.labels(operation="process_pipeline", status="error").inc()


async def update_pipeline_status(
    pipeline_id: str,
    status: PipelineStatusType,
    current_step: int,
    total_steps: int,
    operation: str,
    level: LogLevel = LogLevel.INFO,
):
    """Update status and broadcast it."""

    if pipeline_id not in active_pipelines:
        return

    pipeline = active_pipelines[pipeline_id]
    pipeline.status = status
    pipeline.current_step = current_step
    pipeline.total_steps = total_steps
    pipeline.progress = (current_step / total_steps) * 100
    pipeline.current_operation = operation
    pipeline.updated_at = datetime.utcnow()
    pipeline.logs.append(
        PipelineLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=operation,
            component="orchestrator",
            metadata={"step": current_step, "total_steps": total_steps},
        )
    )

    await broadcast_pipeline_event(
        {
            "type": "pipeline_status_update",
            "pipeline_id": pipeline_id,
            "data": pipeline.model_dump(),
        }
    )


@app.get("/")
async def root():
    """Describe the service without claiming unavailable execution paths."""

    return {
        "service": "Physics Foundry Orchestrator",
        "version": "0.3.0",
        "status": "prototype",
        "mode": "fixture" if fixture_mode_enabled() else "prototype",
        "capabilities_endpoint": "/capabilities",
        "note": (
            "The service exposes orchestration, observability, sandbox, and optional measured frame-QA infrastructure. "
            "Real prompt-to-render completion is reported only when that path is verified."
        ),
    }
