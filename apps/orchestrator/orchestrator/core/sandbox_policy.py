"""Dependency-light policy helpers for generated-code sandboxing.

These checks are defense-in-depth only. Static validation does not make
untrusted code safe to execute on the host; a real isolation backend is still
required by ``sandbox.py`` before generated code can run.
"""

from __future__ import annotations

import ast
import shutil
from pathlib import Path
from typing import Any, Dict

ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "bpy",
        "datetime",
        "manim",
        "math",
        "numpy",
        "pathlib",
        "random",
        "taichi",
        "typing",
    }
)

DANGEROUS_BUILTINS = frozenset(
    {"__import__", "compile", "eval", "exec"}
)

DANGEROUS_ATTRIBUTES = frozenset(
    {
        "chmod",
        "chown",
        "fork",
        "kill",
        "popen",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "rmtree",
        "spawn",
        "system",
        "unlink",
    }
)


def command_available(command: str) -> bool:
    """Return whether an executable is discoverable on ``PATH``."""

    return shutil.which(command) is not None


def validate_workspace_path(filename: str) -> Dict[str, Any]:
    """Validate that a staged filename stays inside the sandbox workspace."""

    candidate = Path(filename)
    if not filename.strip():
        return {"safe": False, "reason": "empty workspace path"}
    if candidate.is_absolute():
        return {"safe": False, "reason": "absolute workspace paths are not allowed"}
    if any(part == ".." for part in candidate.parts):
        return {"safe": False, "reason": "parent-directory traversal is not allowed"}
    if candidate.name in {"", ".", ".."}:
        return {"safe": False, "reason": "invalid workspace filename"}

    return {"safe": True, "path": candidate.as_posix()}


def _import_root(module_name: str) -> str:
    return module_name.split(".", 1)[0]


def validate_python_source(code: str) -> Dict[str, Any]:
    """Perform a conservative AST policy check on generated Python source.

    The result is intentionally described as a policy check rather than a
    security guarantee. Execution must still occur inside a real sandbox.
    """

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "safe": False,
            "reason": f"syntax error: {exc.msg}",
            "blocked_imports": [],
            "dangerous_calls": [],
        }

    blocked_imports: set[str] = set()
    dangerous_calls: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _import_root(alias.name) not in ALLOWED_IMPORT_ROOTS:
                    blocked_imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.level:
                blocked_imports.add("relative import")
            elif node.module and _import_root(node.module) not in ALLOWED_IMPORT_ROOTS:
                blocked_imports.add(node.module)

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_BUILTINS:
                dangerous_calls.add(node.func.id)
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in DANGEROUS_ATTRIBUTES
            ):
                dangerous_calls.add(node.func.attr)

    if blocked_imports or dangerous_calls:
        return {
            "safe": False,
            "reason": "source violates generated-code policy",
            "blocked_imports": sorted(blocked_imports),
            "dangerous_calls": sorted(dangerous_calls),
        }

    return {
        "safe": True,
        "reason": "source passed static policy checks",
        "blocked_imports": [],
        "dangerous_calls": [],
    }
