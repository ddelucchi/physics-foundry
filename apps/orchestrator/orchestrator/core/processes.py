"""Dependency-light subprocess execution with explicit timeout semantics."""

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


class ProcessRunner:
    """Run child processes without pulling observability packages into safety code."""

    async def run_with_timeout(
        self,
        cmd: List[str],
        timeout: float,
        heartbeat_interval: float = 10.0,
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        process_id: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Run one command and terminate its process group on timeout.

        ``heartbeat_interval`` and ``process_id`` are accepted for compatibility
        with existing call sites. They do not imply telemetry collection.
        """

        del heartbeat_interval
        identifier = process_id or f"proc_{int(time.time() * 1_000_000)}"
        start_new_session = os.name == "posix"

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            start_new_session=start_new_session,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            await self._terminate(process)
            raise ProcessTimeoutError(
                f"Process {identifier} timed out after {timeout}s"
            ) from exc

        return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)

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
            # The caller already receives a timeout error; do not convert cleanup
            # difficulty into a false successful execution result.
            return


process_manager = ProcessRunner()
