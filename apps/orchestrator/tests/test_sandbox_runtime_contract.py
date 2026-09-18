"""Dependency-light behavioral tests for sandbox failure semantics.

These tests monkeypatch external capability detection/process execution. They
verify that missing or unverified isolation can never fall through to direct
host execution. They do not establish real firejail runtime isolation.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.core import sandbox as sandbox_module
from orchestrator.core.sandbox import CodeSandbox


@pytest.mark.asyncio
async def test_missing_firejail_returns_unsupported_without_process_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = CodeSandbox("firejail")
    monkeypatch.setattr(instance, "backend_available", lambda: False)

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("process execution must not be reached")

    monkeypatch.setattr(
        sandbox_module.process_manager,
        "run_with_timeout",
        fail_if_called,
    )

    result = await instance.execute_python_code("x = 1")

    assert result["success"] is False
    assert result["status"] == "unsupported"
    assert "not available" in result["error"]


@pytest.mark.asyncio
async def test_unverified_nsjail_backend_never_executes_directly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = CodeSandbox("nsjail")

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("process execution must not be reached")

    monkeypatch.setattr(
        sandbox_module.process_manager,
        "run_with_timeout",
        fail_if_called,
    )

    result = await instance.execute_python_code("x = 1")

    assert result["success"] is False
    assert result["status"] == "unsupported"
    assert "not a verified execution path" in result["error"]


@pytest.mark.asyncio
async def test_blender_unverified_backend_has_no_direct_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = CodeSandbox("nsjail")

    async def fail_if_called(*args, **kwargs):
        raise AssertionError("Blender must not execute directly")

    monkeypatch.setattr(
        sandbox_module.process_manager,
        "run_with_timeout",
        fail_if_called,
    )

    result = await instance.execute_blender_script("import bpy")

    assert result["success"] is False
    assert result["status"] == "unsupported"
    assert "direct fallback is disabled" in result["error"]


def test_extra_file_traversal_is_rejected_before_staging(tmp_path: Path) -> None:
    instance = CodeSandbox("firejail")

    with pytest.raises(ValueError, match="parent-directory traversal"):
        instance._write_extra_files(tmp_path, {"../escape.txt": "nope"})


def test_firejail_profile_disables_network_and_drops_privilege() -> None:
    profile = CodeSandbox("firejail")._create_firejail_profile()

    assert "net none" in profile
    assert "nonewprivs" in profile
    assert "caps.drop all" in profile
    assert "seccomp" in profile
