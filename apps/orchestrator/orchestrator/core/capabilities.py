"""Dependency-light capability detection for Physics Foundry."""

import importlib.util
import os
import shutil
from typing import Dict

FIXTURE_MODE_ENV = "PHYSICS_FOUNDRY_FIXTURE_MODE"


def fixture_mode_enabled() -> bool:
    """Return True only when deterministic fixture mode is explicitly enabled."""

    return os.getenv(FIXTURE_MODE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def command_available(command: str) -> bool:
    """Return whether an external executable is discoverable on PATH."""

    return shutil.which(command) is not None


def module_available(module: str) -> bool:
    """Return whether an optional Python module is discoverable without importing it."""

    return importlib.util.find_spec(module) is not None


def capability_matrix() -> Dict[str, bool]:
    """Report dependency availability without implying end-to-end verification.

    ``nsjail`` is reported as an installed capability only. The current
    generated-code execution contract deliberately treats Firejail as the sole
    supported backend and refuses to fall back to direct host execution.
    """

    firejail = command_available("firejail")
    nsjail = command_available("nsjail")
    ffmpeg = command_available("ffmpeg")
    frame_qa_python = all(
        module_available(module)
        for module in ("cv2", "numpy", "skimage")
    )

    return {
        "fixture_mode": fixture_mode_enabled(),
        "manim_cli": command_available("manim"),
        "ffmpeg": ffmpeg,
        "blender": command_available("blender"),
        "taichi_python": module_available("taichi"),
        "latex": command_available("latex") or command_available("pdflatex"),
        "nvidia_smi": command_available("nvidia-smi"),
        "firejail": firejail,
        "nsjail": nsjail,
        "sandbox_execution_supported": firejail,
        "frame_qa_python": frame_qa_python,
        "vmaf_candidate": frame_qa_python and ffmpeg,
        "opentelemetry_python": module_available("opentelemetry.sdk"),
        "sentry_python": module_available("sentry_sdk"),
        "gpu_metrics_python": module_available("pynvml"),
        "local_llm_configured": bool(os.getenv("LLM_ENDPOINT")),
    }
