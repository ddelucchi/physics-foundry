# Orchestrator tests

Tests are intentionally separated by evidence level.

## Dependency-light portfolio contract

`test_portfolio_contract.py` checks semantics that can run in ordinary hosted CI without GPU/render/model dependencies:

- fixture mode is explicit opt-in;
- capability status is boolean and inspectable;
- deterministic fixture plans are labeled as fixtures;
- Pydantic list/dict defaults are isolated between model instances;
- fixture/unsupported terminal states are distinct from real completion/error.

Run from the repository root:

```bash
PYTHONPATH=apps/orchestrator pytest -q apps/orchestrator/tests/test_portfolio_contract.py
```

## Other tests

`test_error_handling.py` covers the error/recovery subsystem and may require the broader orchestrator environment.

## Evidence boundary

Passing dependency-light tests establishes orchestration/model semantics only. It does **not** establish local-LLM availability, sandbox hardening, Manim/Blender/Taichi execution, or a real prompt-to-video artifact chain.
