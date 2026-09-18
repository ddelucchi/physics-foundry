# Reproducibility and testing

Physics Foundry separates dependency-light contract tests, fixture integration, external-capability tests, sandbox runtime verification, and real artifact evidence. Passing one layer does not imply that a higher layer is operational.

## Evidence layers

### 1. Dependency-light contract tests

These verify semantics that should work in ordinary hosted CI:

- fixture mode requires explicit opt-in;
- capability status is inspectable and boolean;
- fixture plans are deterministic and visibly labeled;
- Pydantic collection defaults are isolated between instances;
- `fixture_complete`, `unsupported`, `complete`, and `error` remain distinct states;
- staged sandbox filenames reject absolute and parent-traversal paths;
- bounded scientific imports pass the generated-code policy;
- process/network imports, relative imports, dynamic execution, and shell-like calls are rejected by the static policy.

Run from the repository root:

```bash
python -m pip install "pydantic>=2.5,<3" "pytest>=7.4,<9"
PYTHONPATH=apps/orchestrator pytest -q apps/orchestrator/tests/test_portfolio_contract.py
```

The workflow also compiles the dependency-light contract modules and the sandbox boundary so syntax regressions fail before runtime claims are made.

### 2. Fixture integration

Fixture mode may exercise job lifecycle, progress events, persisted metadata, and deterministic planning data without external render/model dependencies. Fixture mode is opt-in via `PHYSICS_FOUNDRY_FIXTURE_MODE` and must remain distinguishable from real execution.

Fixture output is test data, not measured renderer performance.

### 3. External capability tests

Optional tests may exercise installed tools such as Manim, FFmpeg, Blender, Taichi, LaTeX, GPU runtimes, firejail, or a local model endpoint. Missing optional dependencies should be reported explicitly, never replaced by simulated production success.

The presence of a binary is only a capability signal. It is not proof that the full dependent path works.

### 4. Sandbox runtime verification

The generated-code wrapper currently requires the firejail execution path and refuses direct fallback. A suitable Linux host should verify at minimum:

1. missing firejail produces an `unsupported` result without executing source;
2. rejected imports/calls never reach a child process;
3. staged files cannot escape the per-execution workspace;
4. network access is unavailable from the child;
5. inherited secrets/environment variables are absent;
6. timeout handling terminates the child/process tree;
7. successful output remains inside the retained workspace;
8. Blender has no unsandboxed fallback path.

These tests are distinct from dependency-light CI because ordinary hosted runners may not provide the required sandbox binary/configuration.

### 5. Real reference artifact

The portfolio milestone is one bounded prompt that produces, through the real path:

1. a persisted structured plan;
2. generated Manim source persisted before execution;
3. sandboxed renderer invocation with command and exit status;
4. a non-empty MP4;
5. at least one inspectable quality measurement computed from the produced artifact;
6. logs/configuration sufficient to reproduce the run.

That real artifact chain is not yet established and remains tracked by issue #17.

## Hosted CI interpretation

GitHub Actions is intended to run layer 1. A workflow result should only be interpreted as evidence if the runner actually reaches and executes the steps. Runner/account/policy failures that terminate before checkout are infrastructure failures, not passing or failing evidence about the Python contract.

The workflow never creates synthetic tests, auto-fixes source, or swallows pytest/build failures to manufacture a green result.

## Claim rule

Architecture diagrams, interfaces, fixture values, TODOs, component tests, installed binaries, and simulated output should never be used to imply a higher evidence level than they actually establish. Public claims should be traceable to code plus an appropriate test, artifact, or benchmark, with limitations stated alongside the result.
