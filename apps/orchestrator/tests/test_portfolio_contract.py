"""Dependency-light tests for portfolio and sandbox claim semantics."""

from datetime import datetime

import pytest

from orchestrator.core.capabilities import (
    FIXTURE_MODE_ENV,
    capability_matrix,
    fixture_mode_enabled,
)
from orchestrator.core.dsl_models import (
    LogLevel,
    PipelineLogEntry,
    PipelineStatus,
    PipelineStatusType,
    SceneRequest,
)
from orchestrator.core.fixtures import build_fixture_plan
from orchestrator.core.sandbox_policy import (
    validate_python_source,
    validate_workspace_path,
)


def _pipeline(pipeline_id: str) -> PipelineStatus:
    return PipelineStatus(
        pipeline_id=pipeline_id,
        status=PipelineStatusType.PLANNING,
        current_step=0,
        total_steps=1,
        progress=0.0,
        current_operation="test",
    )


def test_fixture_mode_requires_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(FIXTURE_MODE_ENV, raising=False)
    assert fixture_mode_enabled() is False

    for value in ("1", "true", "yes", "on"):
        monkeypatch.setenv(FIXTURE_MODE_ENV, value)
        assert fixture_mode_enabled() is True

    for value in ("0", "false", "off", ""):
        monkeypatch.setenv(FIXTURE_MODE_ENV, value)
        assert fixture_mode_enabled() is False


def test_capability_matrix_is_explicit_boolean_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(FIXTURE_MODE_ENV, raising=False)
    matrix = capability_matrix()

    assert matrix["fixture_mode"] is False
    assert "manim_cli" in matrix
    assert "ffmpeg" in matrix
    assert "firejail" in matrix
    assert "nsjail" in matrix
    assert "sandbox_execution_supported" in matrix
    assert "local_llm_configured" in matrix
    assert all(isinstance(value, bool) for value in matrix.values())


def test_fixture_plan_is_deterministic_and_labeled() -> None:
    request = SceneRequest(topic="simple harmonic motion", duration=20, seed=7)

    first = build_fixture_plan(request)
    second = build_fixture_plan(request)

    assert first == second
    assert first["fixture"] is True
    assert first["topic"] == "simple harmonic motion"
    assert first["seed"] == 7
    assert all(scene["engine"] == "manim" for scene in first["scenes"])


def test_pipeline_defaults_are_isolated_between_instances() -> None:
    first = _pipeline("first")
    second = _pipeline("second")

    first.logs.append(
        PipelineLogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO,
            message="first only",
            component="test",
        )
    )

    assert len(first.logs) == 1
    assert second.logs == []
    assert second.artifacts == []
    assert second.workers == []


def test_fixture_and_unsupported_are_distinct_terminal_states() -> None:
    assert PipelineStatusType.FIXTURE_COMPLETE != PipelineStatusType.COMPLETE
    assert PipelineStatusType.UNSUPPORTED != PipelineStatusType.ERROR


def test_workspace_policy_rejects_absolute_and_parent_paths() -> None:
    assert validate_workspace_path("scene.py")["safe"] is True
    assert validate_workspace_path("assets/data.json")["safe"] is True
    assert validate_workspace_path("../secret.txt")["safe"] is False
    assert validate_workspace_path("/etc/passwd")["safe"] is False


def test_static_policy_allows_bounded_scientific_source() -> None:
    source = """
from math import sin
import numpy as np
from manim import Scene
x = np.array([sin(0.0)])
"""
    result = validate_python_source(source)
    assert result["safe"] is True
    assert result["blocked_imports"] == []
    assert result["dangerous_calls"] == []


def test_static_policy_rejects_process_and_network_imports() -> None:
    result = validate_python_source("import subprocess\nimport requests\n")
    assert result["safe"] is False
    assert "subprocess" in result["blocked_imports"]
    assert "requests" in result["blocked_imports"]


def test_static_policy_rejects_dynamic_execution_and_shell_calls() -> None:
    source = """
import math
eval('2 + 2')
math.system('echo unsafe')
"""
    result = validate_python_source(source)
    assert result["safe"] is False
    assert "eval" in result["dangerous_calls"]
    assert "system" in result["dangerous_calls"]


def test_static_policy_rejects_relative_imports() -> None:
    result = validate_python_source("from .local_module import value\n")
    assert result["safe"] is False
    assert "relative import" in result["blocked_imports"]
