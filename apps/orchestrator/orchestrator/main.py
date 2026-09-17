"""
Physics Foundry FastAPI orchestrator.

Research-prototype orchestration service with observability, quality-analysis,
and explicitly opt-in sandbox execution.
"""

import asyncio
import logging
import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .core.dsl_models import (
    SceneRequest, PipelineStatus, PipelineLogEntry, LogLevel,
    QualityMetrics, FrameAnalysis, ErrorCode
)
from .core.observability import (
    setup_observability_stack, 
    observability_manager, 
    system_monitor,
    pipeline_operations_total,
    operation_duration_seconds
)
from .core.media_pipeline import initialize_media_pipeline, media_pipeline
from .core.quality_gates import quality_analyzer, default_quality_gate
from .core.sandbox import sandbox_manager, execute_safe_code

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemStatus(BaseModel):
    """System health status"""
    status: str
    timestamp: datetime
    version: str
    ocio_config: Optional[str] = None
    gpu_available: bool = False
    sandbox_ready: bool = False
    quality_gates_enabled: bool = True
    observability: Dict[str, bool] = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    """Pipeline configuration"""
    llm_model: str = "gpt-neox-20b-q4"
    max_gpu_layers: int = 28
    render_quality: str = "preview"
    target_framerate: int = 30
    ocio_config: Optional[str] = None
    enable_sandbox: bool = True
    quality_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "ssim_minimum": 0.85,
            "vmaf_minimum": 70.0,
            "text_legibility_minimum": 0.80,
        }
    )


# Global state
active_pipelines: Dict[str, PipelineStatus] = {}
websocket_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    
    # Startup
    logger.info("🚀 Starting Physics Foundry Orchestrator")
    
    # Initialize observability stack
    setup_observability_stack(
        prometheus_port=9090,
        jaeger_endpoint=os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces"),
        sentry_dsn=os.getenv("SENTRY_DSN")
    )
    
    # Initialize media pipeline
    ocio_config = os.getenv("OCIO", "/config/ocio/config.ocio")
    if not initialize_media_pipeline(ocio_config):
        logger.warning("Media pipeline initialization failed - some features disabled")
    
    # Start system monitoring
    asyncio.create_task(system_monitor.start_monitoring())
    
    logger.info("✅ Physics Foundry Orchestrator ready")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Physics Foundry Orchestrator")
    system_monitor.stop_monitoring()
    sandbox_manager.cleanup_all()


app = FastAPI(
    title="Physics Foundry Orchestrator",
    version="0.2.0",
    description="Research-prototype physics visualization orchestration pipeline",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health and status endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/status", response_model=SystemStatus)
async def system_status():
    """Comprehensive system status"""
    
    # Check GPU availability
    gpu_available = False
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True)
        gpu_available = result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        pass
    
    # Check OCIO config
    ocio_config = os.getenv("OCIO")
    ocio_available = ocio_config and Path(ocio_config).exists()
    
    return SystemStatus(
        status="operational",
        timestamp=datetime.utcnow(),
        version="0.2.0",
        ocio_config=ocio_config if ocio_available else None,
        gpu_available=gpu_available,
        sandbox_ready=shutil.which("firejail") is not None,
        quality_gates_enabled=True,
        observability={
            "prometheus": True,
            "tracing": observability_manager.tracer is not None,
            "sentry": os.getenv("SENTRY_DSN") is not None
        }
    )


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Pipeline management endpoints
@app.post("/api/pipeline/create")
async def create_pipeline(request: SceneRequest, background_tasks: BackgroundTasks):
    """Create new video generation pipeline"""
    
    pipeline_id = f"pipeline_{int(datetime.utcnow().timestamp())}"
    
    # Initialize pipeline status
    pipeline_status = PipelineStatus(
        pipeline_id=pipeline_id,
        status="planning",
        current_step=1,
        total_steps=10,
        progress=0.0,
        current_operation="Initializing pipeline",
        logs=[
            PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.INFO,
                message=f"Pipeline created for topic: {request.topic}",
                component="orchestrator",
                metadata={"topic": request.topic, "duration": request.duration}
            )
        ]
    )
    
    active_pipelines[pipeline_id] = pipeline_status
    
    # Start pipeline processing in background
    background_tasks.add_task(process_pipeline, pipeline_id, request)
    
    # Emit websocket event
    await broadcast_pipeline_event({
        "type": "pipeline_created",
        "pipeline_id": pipeline_id,
        "data": pipeline_status.dict()
    })
    
    pipeline_operations_total.labels(operation="create_pipeline", status="started").inc()
    
    return {"pipeline_id": pipeline_id, "status": "created"}


@app.get("/api/pipeline/{pipeline_id}/status", response_model=PipelineStatus)
async def get_pipeline_status(pipeline_id: str):
    """Get pipeline status"""
    
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return active_pipelines[pipeline_id]


@app.post("/api/pipeline/{pipeline_id}/quality-check")
async def run_quality_check(pipeline_id: str, frame_paths: List[str]):
    """Run quality analysis on pipeline frames"""
    
    if pipeline_id not in active_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    try:
        frame_paths_obj = [Path(p) for p in frame_paths]
        
        # Run quality gate check
        gate_passed, analyses = await default_quality_gate.check_frame_sequence(frame_paths_obj)
        
        # Update pipeline status
        pipeline = active_pipelines[pipeline_id]
        pipeline.logs.append(
            PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.INFO if gate_passed else LogLevel.WARN,
                message=f"Quality check {'passed' if gate_passed else 'failed'}",
                component="quality_gate",
                metadata={"frames_analyzed": len(analyses), "gate_passed": gate_passed}
            )
        )
        
        await broadcast_pipeline_event({
            "type": "quality_check_complete",
            "pipeline_id": pipeline_id,
            "data": {
                "gate_passed": gate_passed,
                "analyses": [a.dict() for a in analyses]
            }
        })
        
        return {
            "pipeline_id": pipeline_id,
            "gate_passed": gate_passed,
            "frame_analyses": [a.dict() for a in analyses]
        }
        
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quality check failed: {str(e)}")


@app.post("/api/code/execute")
async def execute_code_safely(
    code: str,
    code_type: str = "python",
    timeout: Optional[float] = 60.0,
):
    """Execute code only when the local operator explicitly enables the sandbox API."""

    if os.getenv("PHYSICS_FOUNDRY_ENABLE_CODE_EXECUTION", "0") != "1":
        raise HTTPException(
            status_code=403,
            detail=(
                "Sandbox execution is disabled by default. "
                "Set PHYSICS_FOUNDRY_ENABLE_CODE_EXECUTION=1 only in a trusted local environment."
            ),
        )

    if code_type not in {"python", "blender"}:
        raise HTTPException(status_code=400, detail="Unsupported code type")

    bounded_timeout = min(max(float(timeout or 60.0), 1.0), 120.0)

    with operation_duration_seconds.labels(operation="code_execution").time():
        try:
            result = await execute_safe_code(code, code_type, bounded_timeout)

            pipeline_operations_total.labels(
                operation="code_execution",
                status="success" if result["success"] else "error",
            ).inc()

            return result

        except Exception as exc:
            logger.error("Code execution failed: %s", exc)
            pipeline_operations_total.labels(
                operation="code_execution", status="error"
            ).inc()
            raise HTTPException(
                status_code=500, detail="Sandbox execution failed"
            ) from exc


# WebSocket endpoint for real-time updates
@app.websocket("/ws/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: str):
    """WebSocket connection for real-time pipeline updates"""
    
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send current pipeline status if it exists
        if pipeline_id in active_pipelines:
            await websocket.send_json({
                "type": "pipeline_status",
                "pipeline_id": pipeline_id,
                "data": active_pipelines[pipeline_id].dict()
            })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected for pipeline {pipeline_id}")


async def broadcast_pipeline_event(event: Dict):
    """Broadcast event to all connected websockets"""
    
    if not websocket_connections:
        return
    
    # Send to all connections
    for websocket in websocket_connections.copy():
        try:
            await websocket.send_json(event)
        except Exception:
            # Remove dead connections
            if websocket in websocket_connections:
                websocket_connections.remove(websocket)


async def process_pipeline(pipeline_id: str, request: SceneRequest):
    """Background task to process video generation pipeline"""
    
    pipeline = active_pipelines[pipeline_id]
    
    try:
        async with observability_manager.trace_operation(
            "process_pipeline",
            {"pipeline_id": pipeline_id, "topic": request.topic},
        ):
            
            # Step 1: Plan content
            await update_pipeline_status(
                pipeline_id, 
                "planning", 
                1, 10, 
                "Planning video content structure"
            )
            
            # Simulate the planning stage without claiming a live model call.
            await asyncio.sleep(2)
            
            # Step 2: Generate script
            await update_pipeline_status(
                pipeline_id,
                "scripting", 
                2, 10,
                "Generating deterministic prototype script plan"
            )
            
            # Build a deterministic prototype script in-process. Prompt fields are
            # data, never source code, so user input cannot alter Python syntax here.
            script = {
                "topic": request.topic,
                "duration": request.duration,
                "level": request.level.value,
                "scenes": [
                    {
                        "title": "Introduction",
                        "duration": request.duration * 0.2,
                        "narration": f"Welcome to our exploration of {request.topic}",
                        "visuals": "Title animation with topic introduction",
                    },
                    {
                        "title": "Core Concepts",
                        "duration": request.duration * 0.6,
                        "narration": (
                            f"Let's examine the fundamental principles of {request.topic}"
                        ),
                        "visuals": "Mathematical equations and diagrams",
                    },
                    {
                        "title": "Summary",
                        "duration": request.duration * 0.2,
                        "narration": "Summary of the concepts covered in this prototype plan",
                        "visuals": "Recap animation",
                    },
                ],
                "generated_at": datetime.utcnow().isoformat(),
                "prototype": True,
            }

            pipeline.logs.append(
                PipelineLogEntry(
                    timestamp=datetime.utcnow(),
                    level=LogLevel.INFO,
                    message="Prototype script plan generated",
                    component="orchestrator",
                    metadata={"scene_count": len(script["scenes"]), "prototype": True},
                )
            )


            # Continue through simulated rendering states. Renderer execution is
            # intentionally not claimed by this prototype path.
            for step in range(3, 9):
                await update_pipeline_status(
                    pipeline_id,
                    "rendering",
                    step,
                    10,
                    f"Simulating render segment {step - 2}/6",
                )
                await asyncio.sleep(1)
                
            # Final assembly is also simulated in the current prototype path.
            await update_pipeline_status(
                pipeline_id,
                "assembling",
                9,
                10,
                "Simulating final assembly",
            )
            await asyncio.sleep(2)

            await update_pipeline_status(
                pipeline_id,
                "complete",
                10,
                10,
                "Prototype pipeline simulation complete",
            )

            pipeline_operations_total.labels(
                operation="process_pipeline", status="success"
            ).inc()
    
    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} failed: {e}")
        
        pipeline.status = "error"
        pipeline.current_operation = f"Error: {str(e)}"
        pipeline.logs.append(
            PipelineLogEntry(
                timestamp=datetime.utcnow(),
                level=LogLevel.ERROR,
                message=str(e),
                component="orchestrator",
                metadata={"error_type": type(e).__name__}
            )
        )
        
        await broadcast_pipeline_event({
            "type": "pipeline_error",
            "pipeline_id": pipeline_id,
            "data": {"error": str(e)}
        })
        
        pipeline_operations_total.labels(operation="process_pipeline", status="error").inc()


async def update_pipeline_status(
    pipeline_id: str,
    status: str,
    current_step: int,
    total_steps: int, 
    operation: str
):
    """Update pipeline status and broadcast to clients"""
    
    if pipeline_id not in active_pipelines:
        return
    
    pipeline = active_pipelines[pipeline_id]
    pipeline.status = status
    pipeline.current_step = current_step
    pipeline.total_steps = total_steps
    pipeline.progress = (current_step / total_steps) * 100
    pipeline.current_operation = operation
    pipeline.updated_at = datetime.utcnow()
    
    # Add log entry
    pipeline.logs.append(
        PipelineLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            message=operation,
            component="orchestrator",
            metadata={"step": current_step, "total_steps": total_steps}
        )
    )
    
    # Broadcast update
    await broadcast_pipeline_event({
        "type": "pipeline_status_update",
        "pipeline_id": pipeline_id,
        "data": pipeline.dict()
    })


@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "service": "Physics Foundry Orchestrator",
        "version": "0.2.0",
        "status": "operational",
        "features": [
            "observability_stack",
            "quality_gates",
            "opt_in_sandbox_execution",
            "realtime_monitoring",
            "ocio_color_management",
            "gpu_capability_detection"
        ],
        "endpoints": {
            "health": "/health",
            "status": "/status", 
            "metrics": "/metrics",
            "websocket": "/ws/pipeline/{pipeline_id}"
        }
    }