"""Experimental isolation layer for locally generated renderer code.

Execution fails closed when the configured isolation backend is unavailable.
"""

import json
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import subprocess
import shlex
import shutil

from .observability import process_manager, RetryableOperation
from .dsl_models import LogLevel, PipelineLogEntry

logger = logging.getLogger(__name__)


class CodeSandbox:
    """Secure sandbox for executing AI-generated code"""
    
    def __init__(self, sandbox_type: str = "nsjail"):
        self.sandbox_type = sandbox_type
        self.base_timeout = 60.0  # seconds
        self.memory_limit = "512M"
        self.cpu_limit = 2  # cores
        self.temp_dirs: List[Path] = []
        
        # Allowed Python modules for code generation
        self.allowed_modules = {
            'numpy', 'math', 'random', 'typing', 'datetime',
            'manim', 'taichi', 'bpy',  # Render engines
            'pathlib', 'os'  # Limited system access
        }
        
        # Blocked modules
        self.blocked_modules = {
            'subprocess', 'os.system', 'eval', 'exec',
            'socket', 'urllib', 'requests', 'http',
            'shutil.rmtree', '__import__'
        }
    
    def create_sandbox_profile(
        self, workspace: Path, profile_name: str = "physics_foundry"
    ) -> Path:
        """Create an isolation profile bound to one workspace."""

        if self.sandbox_type == "nsjail":
            profile_content = self._create_nsjail_config(workspace)
        elif self.sandbox_type == "firejail":
            profile_content = self._create_firejail_profile()
        else:
            raise ValueError(f"Unsupported sandbox type: {self.sandbox_type}")
        
        # Write profile to temp file
        profile_path = Path(f"/tmp/{profile_name}.{self.sandbox_type}")
        with open(profile_path, 'w') as f:
            f.write(profile_content)
        
        logger.info(f"Created {self.sandbox_type} profile: {profile_path}")
        return profile_path
    
    def _create_nsjail_config(self, workspace: Path) -> str:
        """Create an nsjail configuration for one concrete workspace."""
        return f"""
name: "physics_foundry"
description: "Sandbox for AI-generated physics code"

mode: ONCE
hostname: "sandbox"

time_limit: {int(self.base_timeout)}
daemon: false
max_conns: 1

log_level: WARN

rlimit_as: {self._parse_memory_limit(self.memory_limit)}
rlimit_cpu: {int(self.base_timeout)}
rlimit_fsize: 104857600  # 100MB file size limit
rlimit_nofile: 32

clone_newnet: true  # No network access
clone_newuser: true
clone_newns: true
clone_newpid: true
clone_newipc: true
clone_newuts: true

keep_env: false
pass_fd: []

mount {{
    src: "{workspace.as_posix()}"
    dst: "/workspace"
    is_bind: true
    rw: true
}}

mount {{
    src: "/usr/lib/python3"
    dst: "/usr/lib/python3"
    is_bind: true
    rw: false
}}

mount {{
    src: "/usr/bin/python3"
    dst: "/usr/bin/python3"
    is_bind: true
    rw: false
}}

seccomp_policy_file: "/etc/nsjail/python.policy"
"""
    
    def _create_firejail_profile(self) -> str:
        """Create firejail profile for secure execution"""
        return f"""
# Physics Foundry AI Code Sandbox Profile
quiet

# Resource limits  
rlimit-as {self.memory_limit}
rlimit-cpu {int(self.base_timeout)}
rlimit-fsize 104857600

# Network isolation
net none

# Filesystem restrictions
private-dev
private-tmp
private-etc passwd,group,hostname,hosts,nsswitch.conf,resolv.conf

# Python specific
whitelist /usr/bin/python3
whitelist /usr/lib/python3

# No X11, audio, or other services
disable-mnt
no3d
nodvd  
nogroups
noinput
nonewprivs
noroot
nosound
notv
nou2f
novideo
nowhitelist ~
noexec /tmp
noexec /dev/shm

# Security 
caps.drop all
nonewprivs
noroot
seccomp !chroot
"""
    
    def _parse_memory_limit(self, limit: str) -> int:
        """Parse memory limit string to bytes"""
        if limit.endswith('M'):
            return int(limit[:-1]) * 1024 * 1024
        elif limit.endswith('G'):
            return int(limit[:-1]) * 1024 * 1024 * 1024
        else:
            return int(limit)
    
    async def execute_python_code(
        self,
        code: str,
        script_name: str = "generated_script.py",
        extra_files: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute Python code in sandbox environment"""
        
        execution_id = str(uuid.uuid4())[:8]
        timeout = timeout or self.base_timeout
        
        # Validate code before execution
        validation_result = self._validate_code_safety(code)
        if not validation_result['safe']:
            return {
                'success': False,
                'error': f"Code validation failed: {validation_result['reason']}",
                'stdout': '',
                'stderr': '',
                'execution_id': execution_id,
                'blocked_imports': validation_result.get('blocked_imports', [])
            }
        
        # Create workspace
        workspace = Path(f"/tmp/sandbox_workspace_{execution_id}").resolve()
        workspace.mkdir(exist_ok=True)
        self.temp_dirs.append(workspace)
        profile_path: Optional[Path] = None

        def workspace_path(relative_name: str) -> Path:
            relative = Path(relative_name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(
                    "Sandbox file paths must be relative and may not traverse upward"
                )
            candidate = (workspace / relative).resolve()
            if candidate != workspace and workspace not in candidate.parents:
                raise ValueError("Sandbox file path escaped the workspace")
            return candidate

        try:
            # Write main script.
            script_path = workspace_path(script_name)
            script_path.parent.mkdir(parents=True, exist_ok=True)
            with open(script_path, "w", encoding="utf-8") as handle:
                handle.write(code)

            # Write optional support files without allowing path traversal.
            if extra_files:
                for filename, content in extra_files.items():
                    file_path = workspace_path(filename)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as handle:
                        handle.write(content)

            # Create sandbox profile.
            profile_path = self.create_sandbox_profile(
                workspace, f"profile_{execution_id}"
            )
            
            # Build execution command
            if self.sandbox_type == "nsjail":
                cmd = [
                    'nsjail',
                    '--config', str(profile_path),
                    '--cwd', '/workspace',
                    '--',
                    'python3', script_name
                ]
            else:  # firejail
                cmd = [
                    'firejail',
                    f'--profile={profile_path}',
                    f'--private={workspace}',
                    'python3', script_name
                ]
            
            # Execute with timeout
            result = await process_manager.run_with_timeout(
                cmd,
                timeout=timeout,
                process_id=f"sandbox_{execution_id}"
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout.decode('utf-8', errors='replace'),
                'stderr': result.stderr.decode('utf-8', errors='replace'),
                'execution_id': execution_id,
                'timeout': timeout,
                'workspace': str(workspace)
            }
            
        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return {
                'success': False,
                'error': f"Sandbox execution error: {str(e)}",
                'stdout': '',
                'stderr': '',
                'execution_id': execution_id
            }
        
        finally:
            # Cleanup the ephemeral profile even when setup fails partway through.
            if profile_path is not None and profile_path.exists():
                profile_path.unlink()
    
    def _validate_code_safety(self, code: str) -> Dict[str, Any]:
        """Validate code for security issues"""
        import ast
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {'safe': False, 'reason': f'Syntax error: {str(e)}'}
        
        blocked_imports = []
        dangerous_calls = []
        
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.blocked_modules:
                        blocked_imports.append(alias.name)
                    elif alias.name not in self.allowed_modules:
                        # Check if it's a submodule of allowed
                        allowed = any(alias.name.startswith(f"{allowed}.") for allowed in self.allowed_modules)
                        if not allowed:
                            blocked_imports.append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.blocked_modules:
                    blocked_imports.append(node.module)
                elif node.module and node.module not in self.allowed_modules:
                    allowed = any(node.module.startswith(f"{allowed}.") for allowed in self.allowed_modules)
                    if not allowed:
                        blocked_imports.append(node.module)
            
            # Check dangerous function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                        dangerous_calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['system', 'popen', 'spawn']:
                        dangerous_calls.append(f"{node.func.value}.{node.func.attr}")
        
        if blocked_imports or dangerous_calls:
            return {
                'safe': False,
                'reason': 'Blocked imports or dangerous calls detected',
                'blocked_imports': blocked_imports,
                'dangerous_calls': dangerous_calls
            }
        
        return {'safe': True, 'reason': 'Code passed safety validation'}
    
    async def execute_blender_script(
        self,
        python_script: str,
        blend_file: Optional[Path] = None,
        output_path: Optional[Path] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute Blender script in sandbox"""
        
        execution_id = str(uuid.uuid4())[:8]
        timeout = timeout or (self.base_timeout * 3)  # Blender needs more time
        
        # Create workspace
        workspace = Path(f"/tmp/blender_workspace_{execution_id}")
        workspace.mkdir(exist_ok=True)
        self.temp_dirs.append(workspace)
        
        try:
            # Write Blender script
            script_path = workspace / "blender_script.py"
            with open(script_path, 'w') as f:
                f.write(python_script)
            
            # Prepare Blender command
            cmd = ['blender', '--background']
            
            if blend_file:
                cmd.extend(['--open', str(blend_file)])
            
            cmd.extend(['--python', str(script_path)])
            
            if output_path:
                cmd.extend(['--render-output', str(output_path)])
                cmd.append('--render-frame')
                cmd.append('1')
            
            # Create enhanced sandbox profile for Blender
            profile_content = self._create_blender_sandbox_profile()
            profile_path = workspace / "blender.profile"
            with open(profile_path, 'w') as f:
                f.write(profile_content)
            
            # Wrap in sandbox
            if self.sandbox_type != "firejail":
                return {
                    "success": False,
                    "error": (
                        "Blender execution requires the firejail backend; "
                        "direct unsandboxed fallback is intentionally disabled"
                    ),
                    "execution_id": execution_id,
                }

            sandbox_cmd = [
                "firejail",
                f"--profile={profile_path}",
                f"--private={workspace}",
            ] + cmd
            
            result = await process_manager.run_with_timeout(
                sandbox_cmd,
                timeout=timeout,
                process_id=f"blender_sandbox_{execution_id}"
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout.decode('utf-8', errors='replace'),
                'stderr': result.stderr.decode('utf-8', errors='replace'),
                'execution_id': execution_id,
                'workspace': str(workspace)
            }
            
        except Exception as e:
            logger.error(f"Blender sandbox execution failed: {e}")
            return {
                'success': False,
                'error': f"Blender sandbox error: {str(e)}",
                'execution_id': execution_id
            }
    
    def _create_blender_sandbox_profile(self) -> str:
        """Create specialized sandbox profile for Blender"""
        return f"""
# Blender Sandbox Profile
quiet

# Resource limits
rlimit-as 2G  # More memory for Blender
rlimit-cpu {int(self.base_timeout * 3)}

# Network isolation (no online assets)
net none

# Blender needs more system access
private-tmp
whitelist /usr/bin/blender
whitelist /usr/share/blender
whitelist /usr/lib/blender

# Graphics (for headless rendering)
whitelist /dev/dri
whitelist /sys/devices

# No dangerous system access
disable-mnt
no3d  # Disable 3D acceleration for safety
nodvd
noinput
nonewprivs
noroot
nosound
notv
"""
    
    def cleanup_workspace(self, execution_id: str):
        """Clean up sandbox workspace"""
        workspace = Path(f"/tmp/sandbox_workspace_{execution_id}")
        blender_workspace = Path(f"/tmp/blender_workspace_{execution_id}")
        
        for ws in [workspace, blender_workspace]:
            if ws.exists():
                try:
                    import shutil
                    shutil.rmtree(ws)
                    logger.info(f"Cleaned up workspace: {ws}")
                except Exception as e:
                    logger.error(f"Failed to cleanup {ws}: {e}")
    
    def cleanup_all_workspaces(self):
        """Clean up all temporary directories"""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.error(f"Failed to cleanup {temp_dir}: {e}")
        
        self.temp_dirs.clear()


class SandboxManager:
    """Manager for multiple sandbox instances"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.active_sandboxes: Dict[str, CodeSandbox] = {}
        self.sandbox_queue: List[str] = []
    
    def get_sandbox(self, sandbox_type: str = "nsjail") -> CodeSandbox:
        """Get or create sandbox instance"""
        if len(self.active_sandboxes) >= self.max_concurrent:
            # Cleanup oldest sandbox
            oldest_id = next(iter(self.active_sandboxes))
            self.cleanup_sandbox(oldest_id)
        
        sandbox_id = str(uuid.uuid4())[:8]
        sandbox = CodeSandbox(sandbox_type)
        self.active_sandboxes[sandbox_id] = sandbox
        
        return sandbox
    
    def cleanup_sandbox(self, sandbox_id: str):
        """Clean up specific sandbox"""
        if sandbox_id in self.active_sandboxes:
            sandbox = self.active_sandboxes[sandbox_id]
            sandbox.cleanup_all_workspaces()
            del self.active_sandboxes[sandbox_id]
    
    def cleanup_all(self):
        """Clean up all sandboxes"""
        for sandbox_id in list(self.active_sandboxes.keys()):
            self.cleanup_sandbox(sandbox_id)


# Global sandbox manager
sandbox_manager = SandboxManager()


async def execute_safe_code(
    code: str,
    code_type: str = "python",
    timeout: Optional[float] = None,
    extra_files: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    High-level interface for safe code execution
    """
    if shutil.which("firejail") is None:
        return {
            "success": False,
            "error": "firejail is required for local code execution but was not found",
            "execution_id": "unavailable",
        }

    sandbox = sandbox_manager.get_sandbox("firejail")

    if code_type == "python":
        return await sandbox.execute_python_code(code, timeout=timeout, extra_files=extra_files)
    elif code_type == "blender":
        return await sandbox.execute_blender_script(code, timeout=timeout)
    else:
        return {
            'success': False,
            'error': f"Unsupported code type: {code_type}",
            'execution_id': 'error'
        }