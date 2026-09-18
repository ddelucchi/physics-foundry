"""Runtime contracts for the stdlib-only child-process boundary."""

import sys

import pytest

from orchestrator.core.processes import ProcessOutputLimitError, ProcessRunner, ProcessTimeoutError


@pytest.mark.asyncio
async def test_process_runner_returns_real_success_output() -> None:
    runner = ProcessRunner()
    result = await runner.run_with_timeout(
        [sys.executable, "-c", "print('physics-foundry')"],
        timeout=2.0,
    )

    assert result.returncode == 0
    assert result.stdout.decode().strip() == "physics-foundry"


@pytest.mark.asyncio
async def test_process_runner_preserves_nonzero_exit_code() -> None:
    runner = ProcessRunner()
    result = await runner.run_with_timeout(
        [sys.executable, "-c", "raise SystemExit(7)"],
        timeout=2.0,
    )

    assert result.returncode == 7


@pytest.mark.asyncio
async def test_process_runner_times_out_instead_of_returning_success() -> None:
    runner = ProcessRunner()

    with pytest.raises(ProcessTimeoutError, match="timed out"):
        await runner.run_with_timeout(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=0.05,
        )


@pytest.mark.asyncio
async def test_process_runner_rejects_excessive_stdout() -> None:
    runner = ProcessRunner()

    with pytest.raises(ProcessOutputLimitError, match="stdout"):
        await runner.run_with_timeout(
            [sys.executable, "-c", "print('x' * 20000)"],
            timeout=2.0,
            max_output_bytes=1024,
        )


@pytest.mark.asyncio
async def test_process_runner_accepts_explicit_small_output_cap() -> None:
    runner = ProcessRunner()
    result = await runner.run_with_timeout(
        [sys.executable, "-c", "print('bounded-output')"],
        timeout=2.0,
        max_output_bytes=4096,
    )

    assert result.returncode == 0
    assert b"bounded-output" in result.stdout
