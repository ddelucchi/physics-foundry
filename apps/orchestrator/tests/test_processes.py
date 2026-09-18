"""Dependency-light tests for subprocess timeout and output limits."""

from __future__ import annotations

import sys

import pytest

from orchestrator.core.processes import (
    ProcessOutputLimitError,
    ProcessRunner,
    ProcessTimeoutError,
)


@pytest.mark.asyncio
async def test_process_runner_captures_small_output() -> None:
    runner = ProcessRunner()
    result = await runner.run_with_timeout(
        [sys.executable, "-c", "print(\'bounded-output\')"],
        timeout=5.0,
        max_output_bytes=4096,
    )

    assert result.returncode == 0
    assert b"bounded-output" in result.stdout


@pytest.mark.asyncio
async def test_process_runner_rejects_excessive_stdout() -> None:
    runner = ProcessRunner()

    with pytest.raises(ProcessOutputLimitError, match="stdout"):
        await runner.run_with_timeout(
            [sys.executable, "-c", "print(\'x\' * 20000)"],
            timeout=5.0,
            max_output_bytes=1024,
        )


@pytest.mark.asyncio
async def test_process_runner_enforces_timeout() -> None:
    runner = ProcessRunner()

    with pytest.raises(ProcessTimeoutError):
        await runner.run_with_timeout(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.05,
            max_output_bytes=4096,
        )
