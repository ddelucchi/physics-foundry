# Physics Foundry - Product Requirements Document

> **Document status:** target-state architecture and product requirements. The repository [README](../README.md) is authoritative for current implementation status. Checkboxes and aspirational KPIs below are design targets, not independently verified performance claims.

## Overview

Physics Foundry is a **modular, error-coded, multi-model, fully-local** target architecture for physics-video generation research. It leverages **multiple LLMs via OpenAI-compatible local servers**, live token streaming, **headless Blender (Cycles CUDA/OptiX)**, **Manim (OpenGL/Cairo)**, **Taichi (CUDA/GPU autoselect)**, **OpenTimelineIO** as timeline authority, **OCIO** color management, **FFmpeg** with hardware acceleration, **Whisper.cpp** and **Montreal Forced Aligner** for precise audio synchronization, **Piper TTS** for offline narration, and **Prometheus + OpenTelemetry** for comprehensive observability.

## Architecture Principles

### Local-First AI
- **OpenAI-compatible LLM server** with streaming token support (llama.cpp)
- **Multiple model roles**: planner, critic, aligner, code generator
- **GGUF quantized models** with GPU layer offloading
- **Complete privacy** - no external API dependencies

### Multi-Engine Rendering
- **Intelligent engine selection** based on content type and complexity
- **Manim**: Mathematical equations, graphs, 2D animations
- **Taichi**: Fluid dynamics, particle systems, field visualizations  
- **Blender**: 3D models, realistic physics, cinematic sequences
- **Graceful degradation**: OptiX→CUDA→CPU fallbacks

### Timeline-Centric Workflow
- **OpenTimelineIO** as single source of timing truth
- **Word-level markers** from audio alignment
- **Frame-first rendering** for crash resumability
- **Content-addressable storage** with SHA-256 checksums

### Error-Coded Reliability
- **Structured error codes** (SUBSYS-CATEGORY-NNN format)
- **Auto-remediation rules** built into each error type
- **Fallback strategies** for common failure modes
- **Health monitoring** with nvidia-smi integration

## Core Components

### GUI Application (`/apps/gui/`)
- **Tauri + React + Vite + TypeScript** desktop application
- **Real-time WebSocket** connection to orchestrator
- **Consolidated RenderPreview** component with multiple modes:
  - `basic`: Simple playback and analysis
  - `enhanced`: Advanced controls and batch processing
  - `frameQA`: Frame-by-frame quality analysis
  - `comprehensive`: Full pipeline monitoring
- **Live token streaming** from LLM during script generation
- **Audio alignment workspace** with waveform visualization
- **System monitor** with GPU utilization tracking

### Orchestrator Backend (`/apps/orchestrator/`)
- **FastAPI + WebSockets** for real-time pipeline updates
- **OpenTimelineIO integration** for timeline management
- **Multi-worker coordination** (Blender/Manim/Taichi)
- **Quality assurance** with SSIM/optical flow analysis
- **Audio alignment** with Whisper.cpp and MFA
- **Prometheus metrics** and **OpenTelemetry traces**
- **Error registry** with auto-fix suggestions

### Shared Packages (`/packages/`)
- **JSON Schema** definitions for DSL validation
- **Generated TypeScript/Python types** from schemas
- **Plugin architecture** for extensible rendering engines

## Configuration Management

### Runtime Configuration (`/config/runtime.config.json`)
```json
{
  "llm": {
    "endpoint": "http://127.0.0.1:8080/v1",
    "models": [
      {"name": "gpt-neox-20b-q4", "n_gpu_layers": 28},
      {"name": "mistral-7b-instruct-q5", "n_gpu_layers": 35}
    ],
    "roles": {
      "planner": "gpt-neox-20b-q4",
      "script_critic": "mistral-7b-instruct-q5"
    }
  },
  "render": {
    "device": "OPTIX",
    "fallback_device": "CUDA",
    "preview_samples": 8,
    "final_samples": 128
  },
  "color": {
    "ocio_config": "config/ocio/config.ocio",
    "display": "Rec.709",
    "eotf": "BT.1886"
  }
}
```

### OCIO Color Management (`/config/ocio/`)
- **AgX and Filmic** view transforms
- **Rec.709/BT.1886** display compliance
- **ACEScg working space** for consistent color
- **Automatic color tagging** enforcement

## Quality Assurance System

### Automated Analysis
- **SSIM comparison** against reference frames
- **Optical flow stability** detection
- **Text legibility** assessment
- **Color accuracy** validation
- **Compression artifact** detection

### Real-Time Monitoring  
- **Frame-by-frame analysis** during rendering
- **Quality gates** with automatic retry logic
- **Visual overlay** of detected issues
- **Automatic remediation suggestions**

## Audio Pipeline

### Voice Synchronization
- **Whisper.cpp CUDA** for fast transcription
- **Montreal Forced Aligner** for word-level timing
- **OTIO marker injection** for precise sync
- **EBU R128 loudness** normalization with FFmpeg

### Scratch Audio Generation
- **Piper TTS** for offline narration during development
- **Real-time alignment** feedback for script timing
- **Voice replacement** workflow for final production

## Development Workflow

### Setup Commands
```bash
# Install dependencies
just setup

# Check system requirements  
just check

# Install LLM server with CUDA
just install-llm
```

### Development Servers
```bash
# Start all services
just dev-all

# Individual services
just dev-gui    # React/Vite frontend
just dev-api    # FastAPI backend
```

### Pipeline Operations
```bash
# Plan physics video
just plan "Quantum Mechanics" 180 intermediate

# Start preview render
just preview project-123

# Run quality checks
just qc /path/to/sequence

# Final assembly
just final project-123
```

## Error Handling

### Structured Error Codes
- **LLM-JSON-001**: Invalid DSL JSON → field repair with streaming continuation
- **BLD-OPTIX-302**: OptiX OOM → CUDA fallback with reduced samples
- **MNM-OGL-101**: OpenGL init failed → Cairo renderer fallback
- **ENC-NVENC-801**: NVENC unavailable → libx264 automatic fallback

### Auto-Remediation
Each error includes:
- **Failing command** and stderr excerpt
- **Auto-fix script** when applicable
- **GUI toggle** to promote fix to permanent setting
- **Documentation link** for manual resolution

## Extensibility

### Plugin Architecture
- **Rendering engine plugins** in `/packages/plugins/`
- **Drop-in GGUF model** support via llama.cpp server
- **OCIO config profiles** for different color workflows
- **Prometheus/OTel sink** configuration for monitoring

### Model Zoo Support
- **Any GGUF model** compatible with llama.cpp server
- **Role-based model assignment** (planner vs critic)
- **Context length** and **GPU layer** optimization
- **Streaming token support** for real-time feedback

## Deployment & Operations

### Health Monitoring
- **nvidia-smi integration** for GPU utilization
- **WebSocket heartbeats** for connection health
- **Pipeline DAG visualization** with retry states
- **OpenTelemetry distributed tracing**

### Scalability
- **Multiple concurrent pipelines** with resource allocation
- **Worker pool management** with automatic scaling
- **Content-addressable cache** with configurable limits
- **Frame-first architecture** for trivial parallelization

## Success Metrics

### Technical KPIs
- **Pipeline completion rate** > 95%
- **Average processing time** < 2x content duration  
- **Quality gate pass rate** > 90%
- **GPU utilization** > 80% during rendering

### User Experience
- **Real-time feedback** during all pipeline stages
- **One-click remediation** for common issues
- **Reproducible results** with seed-based determinism
- **Professional-grade output** meeting broadcast standards

## Implementation Status

- [x] Monorepo structure with apps/packages organization
- [x] Consolidated RenderPreview component with multiple modes
- [x] FastAPI orchestrator with WebSocket real-time updates
- [x] Runtime configuration with LLM/render/color settings
- [x] OCIO color management configuration
- [x] System check and installation scripts
- [x] Development workflow with Just commands
- [ ] Complete worker implementations (Blender/Manim/Taichi)
- [ ] Audio alignment pipeline with Whisper.cpp/MFA
- [ ] Quality analysis engine with SSIM/optical flow
- [ ] Error registry with auto-remediation
- [ ] Telemetry integration (Prometheus/OpenTelemetry)
- [ ] End-to-end pipeline testing