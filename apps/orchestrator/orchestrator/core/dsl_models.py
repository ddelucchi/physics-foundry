"""Pydantic models for scene DSL and pipeline events."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EngineType(str, Enum):
    MANIM = "manim"
    TAICHI = "taichi"
    BLENDER = "blender"


class LevelType(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PipelineStatusType(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    SCRIPTING = "scripting"
    RENDERING = "rendering"
    ASSEMBLING = "assembling"
    COMPLETE = "complete"
    FIXTURE_COMPLETE = "fixture_complete"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class StyleConfig(BaseModel):
    color_theme: Literal["scientific", "educational", "dramatic"] = "scientific"
    font_stack: List[str] = Field(default_factory=lambda: ["Inter", "JetBrains Mono"])
    motion_vocabulary: Literal["smooth", "dynamic", "precise"] = "smooth"


class SceneRequest(BaseModel):
    """Request model for physics video generation."""

    topic: str = Field(..., description="Physics topic to explain")
    duration: int = Field(..., ge=10, le=600, description="Target duration in seconds")
    level: LevelType = Field(default=LevelType.INTERMEDIATE, description="Difficulty level")
    style: StyleConfig = Field(default_factory=StyleConfig, description="Visual style configuration")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


class Beat(BaseModel):
    """A story beat in the script."""

    id: str
    title: str
    concept: str
    duration: float
    narration: str
    visual_description: str


class Shot(BaseModel):
    """A shot within a beat."""

    id: str
    beat_id: str
    engine: EngineType
    duration: float
    description: str
    code_directive: str
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)


class Action(BaseModel):
    """An action within a shot."""

    id: str
    shot_id: str
    tool: EngineType
    timing: Dict[str, float]
    outputs: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ScriptStructure(BaseModel):
    """Complete script structure."""

    beats: List[Beat]
    shots: List[Shot]
    actions: List[Action]
    total_duration: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineLogEntry(BaseModel):
    """Log entry for pipeline execution."""

    timestamp: datetime
    level: LogLevel
    message: str
    component: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineArtifact(BaseModel):
    """Artifact generated during pipeline execution."""

    id: str
    type: Literal["video", "audio", "image", "data", "code"]
    path: str
    size: int
    checksum: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkerStatus(BaseModel):
    """Status of a pipeline worker."""

    id: str
    type: EngineType
    status: Literal["idle", "busy", "error", "offline"]
    current_task: Optional[str] = None
    progress: float = 0.0
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)


class PipelineStatus(BaseModel):
    """Overall pipeline status."""

    pipeline_id: str
    status: PipelineStatusType
    current_step: int
    total_steps: int
    progress: float
    current_operation: str
    estimated_completion: Optional[datetime] = None
    logs: List[PipelineLogEntry] = Field(default_factory=list)
    artifacts: List[PipelineArtifact] = Field(default_factory=list)
    workers: List[WorkerStatus] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PipelineEvent(BaseModel):
    """Event emitted by pipeline for real-time updates."""

    pipeline_id: str
    event_type: Literal["status_update", "log_entry", "artifact_created", "worker_update", "error"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]


class ErrorCode(BaseModel):
    """Structured error code with remediation metadata."""

    code: str
    subsystem: str
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    command: Optional[str] = None
    stderr: Optional[str] = None
    auto_fix: Optional[str] = None
    suggestion: str
    documentation_link: Optional[str] = None


class QualityMetrics(BaseModel):
    """Directly measured or explicitly heuristic frame metrics.

    ``reference_ssim`` is populated only when a compatible reference frame is
    supplied. The remaining values are image statistics, not claims of semantic
    text recognition, temporal motion analysis, or calibrated color accuracy.
    """

    reference_ssim: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sharpness_variance: float = Field(..., ge=0.0)
    edge_density: float = Field(..., ge=0.0, le=1.0)
    clipping_fraction: float = Field(..., ge=0.0, le=1.0)
    block_boundary_ratio: float = Field(..., ge=0.0)


class QualityIssue(BaseModel):
    """Quality issue emitted from an explicit threshold or analysis failure."""

    type: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    location: Optional[Dict[str, int]] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


class FrameAnalysis(BaseModel):
    """Measured frame statistics plus a transparent heuristic gate score."""

    frame_index: int
    timestamp: float
    metrics: QualityMetrics
    issues: List[QualityIssue] = Field(default_factory=list)
    heuristic_score: float = Field(..., ge=0.0, le=1.0)
    analysis_duration: float
