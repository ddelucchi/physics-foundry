"""Dependency-light subprocess execution with bounded output and timeout semantics."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional


class ProcessTimeoutError(TimeoutError):
    """Raised when a child process exceeds its declared timeout."""


class ProcessOutputLimitError(RuntimeError):
    """Raised when a child exceeds the configured stdout/stderr byte limit."""


class ProcessRunner:
    """Run child processes with process-group termination and bounded capture."""

    DEFAULT_MAX_OUTPUT_BYTES = 2 * 1024 * 1024

    async def run_with_timeout(
        self,
        cmd: List[str],
        timeout: float,
        heartbeat_interval: float = 10.0,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        process_id: Optional[str] = None,
        max_output_bytes: Optional[int] = None,
    ) -> subprocess.CompletedProcess:
        """Run one command with bounded stdout/stderr and terminate on failure.

        The byte cap is applied independently to stdout and stderr. Exceeding
        either limit terminates the whole child process group so a noisy child
        cannot turn pipe capture into an unbounded-memory denial of service.

        heartbeat_interval and process_id are retained for compatibility with
        existing call sites and do not imply telemetry collection.
        """

        del heartbeat_interval
        identifier = process_id or f"proc_{int(time.time() * 1_000_000)}"
        limit = self.DEFAULT_MAX_OUTPUT_BYTES if max_output_bytes is None else int(max_output_bytes)
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if limit <= 0:
            raise ValueError("max_output_bytes must be positive")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            start_new_session=(os.name == "posix"),
        )

        stdout_task = asyncio.create_task(
            self._read_bounded(process.stdout, limit, "stdout", identifier)
        )
        stderr_task = asyncio.create_task(
            self._read_bounded(process.stderr, limit, "stderr", identifier)
        )
        wait_task = asyncio.create_task(process.wait())
        tasks = (stdout_task, stderr_task, wait_task)

        try:
            stdout, stderr, _ = await asyncio.wait_for(
                asyncio.gather(*tasks),
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            await self._terminate(process)
            await self._cancel_tasks(tasks)
            raise ProcessTimeoutError(
                f"Process {identifier} timed out after {timeout}s"
            ) from exc
        except ProcessOutputLimitError:
            await self._terminate(process)
            await self._cancel_tasks(tasks)
            raise
        except BaseException:
            await self._terminate(process)
            await self._cancel_tasks(tasks)
            raise

        return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)

    @staticmethod
    async def _read_bounded(
        stream: Optional[asyncio.StreamReader],
        limit: int,
        stream_name: str,
        identifier: str,
    ) -> bytes:
        if stream is None:
            return b""

        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = await stream.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ProcessOutputLimitError(
                    f"Process {identifier} exceeded {limit} bytes on {stream_name}"
                )
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    async def _cancel_tasks(tasks) -> None:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _terminate(self, process: asyncio.subprocess.Process) -> None:
        """Terminate the child and, on POSIX, its dedicated process group."""

        if process.returncode is not None:
            return

        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
        else:
            process.terminate()

        try:
            await asyncio.wait_for(process.wait(), timeout=2.0)
            return
        except asyncio.TimeoutError:
            pass

        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
        else:
            process.kill()

        try:
            await asyncio.wait_for(process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            return


process_manager = ProcessRunner()
