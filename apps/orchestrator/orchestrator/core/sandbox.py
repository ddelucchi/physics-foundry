"""Generated-code sandbox boundary for Physics Foundry.

This module intentionally prefers explicit failure over unsandboxed fallback.
Static source validation is defense-in-depth only; generated code is executed
only when the currently supported isolation backend is available.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .processes import process_manager
from .sandbox_policy import (
    command_available,
    validate_python_source,
    validate_workspace_path,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXECUTION_BACKEND = "firejail"


class CodeSandbox:
    """Prototype sandbox wrapper that refuses unsafe backend fallbacks."""

    def __init__(self, sandbox_type: str = SUPPORTED_EXECUTION_BACKEND):
        self.sandbox_type = sandbox_type
        self.base_timeout = 60.0
        self.memory_limit = "512M"
        self.temp_dirs: List[Path] = []

    @staticmethod
    def _unsupported(execution_id: str, reason: str) -> Dict[str, Any]:
        return {
            "success": False,
            "status": "unsupported",
            "error": reason,
            "stdout": "",
            "stderr": "",
            "execution_id": execution_id,
        }

    def backend_available(self) -> bool:
        """Return whether the selected isolation executable exists."""

        return command_available(self.sandbox_type)

    def _parse_memory_limit(self, limit: str) -> int:
        """Parse a compact byte limit such as ``512M`` or ``2G``."""

        normalized = limit.strip().upper()
        if normalized.endswith("M"):
            return int(normalized[:-1]) * 1024 * 1024
        if normalized.endswith("G"):
            return int(normalized[:-1]) * 1024 * 1024 * 1024
        return int(normalized)

    def _create_firejail_profile(self) -> str:
        """Return the project firejail profile.

        The workspace itself is supplied with ``--private=<workspace>`` at
        execution time so a profile never contains a stale global temp path.
        """

        return f"""# Physics Foundry generated-code profile
quiet
net none
private-dev
private-etc passwd,group,hostname,hosts,nsswitch.conf
nonewprivs
caps.drop all
seccomp
rlimit-as {self._parse_memory_limit(self.memory_limit)}
rlimit-cpu {int(self.base_timeout)}
rlimit-fsize 104857600
rlimit-nofile 32
nogroups
noinput
nosound
notv
nou2f
novideo
"""

    def create_sandbox_profile(
        self,
        workspace: Path,
        profile_name: str = "physics_foundry",
    ) -> Path:
        """Create a per-execution firejail profile.

        nsjail is detected separately by the capability layer but is not used
        here until its mount/seccomp contract is independently verified.
        """

        if self.sandbox_type != SUPPORTED_EXECUTION_BACKEND:
            raise RuntimeError(
                f"Sandbox backend {self.sandbox_type!r} is not a verified execution path"
            )

        profile_path = workspace / f"{profile_name}.firejail"
        profile_path.write_text(self._create_firejail_profile(), encoding="utf-8")
        return profile_path

    def _write_extra_files(self, workspace: Path, extra_files: Dict[str, str]) -> None:
        """Stage caller-provided text files without permitting path traversal."""

        for filename, content in extra_files.items():
            validation = validate_workspace_path(filename)
            if not validation["safe"]:
                raise ValueError(f"Invalid staged file {filename!r}: {validation['reason']}")

            destination = workspace / validation["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    async def execute_python_code(
        self,
        code: str,
        script_name: str = "generated_script.py",
        extra_files: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute generated Python only through the verified sandbox backend."""

        execution_id = uuid.uuid4().hex[:12]
        effective_timeout = timeout or self.base_timeout

        script_validation = validate_workspace_path(script_name)
        if not script_validation["safe"]:
            return self._unsupported(
                execution_id,
                f"Invalid script path: {script_validation['reason']}",
            )

        source_validation = validate_python_source(code)
        if not source_validation["safe"]:
            return {
                **self._unsupported(
                    execution_id,
                    f"Code validation failed: {source_validation['reason']}",
                ),
                "blocked_imports": source_validation["blocked_imports"],
                "dangerous_calls": source_validation["dangerous_calls"],
            }

        if self.sandbox_type != SUPPORTED_EXECUTION_BACKEND:
            return self._unsupported(
                execution_id,
                (
                    f"Sandbox backend {self.sandbox_type!r} is not a verified execution "
                    "path; direct execution is intentionally disabled"
                ),
            )

        if not self.backend_available():
            return self._unsupported(
                execution_id,
                "firejail is not available; generated code was not executed",
            )

        if not command_available("python3"):
            return self._unsupported(
                execution_id,
                "python3 is not available inside the execution environment",
            )

        workspace = Path(tempfile.mkdtemp(prefix="physics_foundry_python_"))
        self.temp_dirs.append(workspace)
        profile_path: Optional[Path] = None

        try:
            relative_script = Path(script_validation["path"])
            script_path = workspace / relative_script
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(code, encoding="utf-8")

            if extra_files:
                self._write_extra_files(workspace, extra_files)

            profile_path = self.create_sandbox_profile(
                workspace,
                f"profile_{execution_id}",
            )

            command = [
                "firejail",
                "--quiet",
                f"--profile={profile_path}",
                f"--private={workspace}",
                f"--chdir={workspace}",
                "/usr/bin/env",
                "-i",
                "PATH=/usr/bin:/bin",
                "PYTHONNOUSERSITE=1",
                "python3",
                relative_script.as_posix(),
            ]

            result = await process_manager.run_with_timeout(
                command,
                timeout=effective_timeout,
                process_id=f"sandbox_{execution_id}",
            )

            return {
                "success": result.returncode == 0,
                "status": "complete" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout.decode("utf-8", errors="replace"),
                "stderr": result.stderr.decode("utf-8", errors="replace"),
                "execution_id": execution_id,
                "timeout": effective_timeout,
                "workspace": str(workspace),
                "backend": SUPPORTED_EXECUTION_BACKEND,
            }

        except Exception as exc:
            logger.exception("Sandboxed Python execution failed")
            return {
                "success": False,
                "status": "error",
                "error": f"Sandbox execution error: {exc}",
                "stdout": "",
                "stderr": "",
                "execution_id": execution_id,
                "backend": SUPPORTED_EXECUTION_BACKEND,
            }
        finally:
            if profile_path is not None and profile_path.exists():
                profile_path.unlink()

    async def execute_blender_script(
        self,
        python_script: str,
        blend_file: Optional[Path] = None,
        output_path: Optional[Path] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute a Blender script only when the firejail path is available.

        Host-path staging for ``blend_file`` and ``output_path`` is deliberately
        not implemented yet because silently exposing arbitrary host paths would
        defeat the repository's current isolation contract.
        """

        execution_id = uuid.uuid4().hex[:12]
        effective_timeout = timeout or (self.base_timeout * 3)

        if blend_file is not None or output_path is not None:
            return self._unsupported(
                execution_id,
                "External Blender input/output path staging is not yet verified",
            )

        source_validation = validate_python_source(python_script)
        if not source_validation["safe"]:
            return {
                **self._unsupported(
                    execution_id,
                    f"Code validation failed: {source_validation['reason']}",
                ),
                "blocked_imports": source_validation["blocked_imports"],
                "dangerous_calls": source_validation["dangerous_calls"],
            }

        if self.sandbox_type != SUPPORTED_EXECUTION_BACKEND:
            return self._unsupported(
                execution_id,
                "Blender execution has no verified nsjail path; direct fallback is disabled",
            )
        if not self.backend_available():
            return self._unsupported(
                execution_id,
                "firejail is not available; Blender code was not executed",
            )
        if not command_available("blender"):
            return self._unsupported(
                execution_id,
                "Blender is not available; generated Blender code was not executed",
            )

        workspace = Path(tempfile.mkdtemp(prefix="physics_foundry_blender_"))
        self.temp_dirs.append(workspace)
        profile_path: Optional[Path] = None

        try:
            script_path = workspace / "blender_script.py"
            script_path.write_text(python_script, encoding="utf-8")
            profile_path = self.create_sandbox_profile(
                workspace,
                f"blender_{execution_id}",
            )

            command = [
                "firejail",
                "--quiet",
                f"--profile={profile_path}",
                f"--private={workspace}",
                f"--chdir={workspace}",
                "/usr/bin/env",
                "-i",
                "PATH=/usr/bin:/bin",
                "blender",
                "--background",
                "--python",
                script_path.name,
            ]

            result = await process_manager.run_with_timeout(
                command,
                timeout=effective_timeout,
                process_id=f"blender_sandbox_{execution_id}",
            )

            return {
                "success": result.returncode == 0,
                "status": "complete" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout.decode("utf-8", errors="replace"),
                "stderr": result.stderr.decode("utf-8", errors="replace"),
                "execution_id": execution_id,
                "workspace": str(workspace),
                "backend": SUPPORTED_EXECUTION_BACKEND,
            }

        except Exception as exc:
            logger.exception("Sandboxed Blender execution failed")
            return {
                "success": False,
                "status": "error",
                "error": f"Blender sandbox error: {exc}",
                "execution_id": execution_id,
                "backend": SUPPORTED_EXECUTION_BACKEND,
            }
        finally:
            if profile_path is not None and profile_path.exists():
                profile_path.unlink()

    def cleanup_all_workspaces(self) -> None:
        """Remove temporary workspaces created by this sandbox instance."""

        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    logger.exception("Failed to clean sandbox workspace %s", temp_dir)
        self.temp_dirs.clear()


class SandboxManager:
    """Track sandbox instances so their retained workspaces can be cleaned."""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.active_sandboxes: Dict[str, CodeSandbox] = {}

    def get_sandbox(
        self,
        sandbox_type: str = SUPPORTED_EXECUTION_BACKEND,
    ) -> CodeSandbox:
        if len(self.active_sandboxes) >= self.max_concurrent:
            oldest_id = next(iter(self.active_sandboxes))
            self.cleanup_sandbox(oldest_id)

        sandbox_id = uuid.uuid4().hex[:12]
        sandbox = CodeSandbox(sandbox_type)
        self.active_sandboxes[sandbox_id] = sandbox
        return sandbox

    def cleanup_sandbox(self, sandbox_id: str) -> None:
        if sandbox_id in self.active_sandboxes:
            self.active_sandboxes[sandbox_id].cleanup_all_workspaces()
            del self.active_sandboxes[sandbox_id]

    def cleanup_all(self) -> None:
        for sandbox_id in list(self.active_sandboxes):
            self.cleanup_sandbox(sandbox_id)


sandbox_manager = SandboxManager()


async def execute_safe_code(
    code: str,
    code_type: str = "python",
    timeout: Optional[float] = None,
    extra_files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """High-level generated-code execution entry point.

    The current verified backend contract is deliberately limited to firejail.
    If it is unavailable, execution returns ``unsupported`` rather than running
    directly on the host.
    """

    sandbox = sandbox_manager.get_sandbox(SUPPORTED_EXECUTION_BACKEND)

    if code_type == "python":
        return await sandbox.execute_python_code(
            code,
            timeout=timeout,
            extra_files=extra_files,
        )
    if code_type == "blender":
        return await sandbox.execute_blender_script(code, timeout=timeout)

    return {
        "success": False,
        "status": "unsupported",
        "error": f"Unsupported code type: {code_type}",
        "execution_id": "unsupported",
    }
