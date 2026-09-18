"""Runtime contracts for the stdlib-only child-process boundary."""

import sys

import pytest

from orchestrator.core.processes import ProcessRunner, ProcessTimeoutError


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
