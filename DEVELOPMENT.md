# Physics Foundry Development Guide

This guide describes the repository as it exists today. For product direction, see [`docs/PRD.md`](docs/PRD.md). For capability evidence, see [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md) and [`docs/CLAIMS.md`](docs/CLAIMS.md).

## Repository structure

```text
physics-foundry/
├── apps/
│   ├── gui/                  # canonical React/Vite interface
│   └── orchestrator/         # FastAPI orchestration service
├── packages/                 # shared/plugin-oriented packages
├── config/                   # runtime and renderer configuration
├── docs/                     # evidence, roadmap, product vision
├── scripts/                  # development helpers
├── SECURITY.md
└── package.json              # workspace coordinator
```

The repository root is not a second frontend. `apps/gui/` is the canonical GUI source tree.

## Prerequisites

For the dependency-light development path:

- Node.js 20+
- npm 10+
- Python 3.11
- Git

Optional renderer/model/media dependencies are not required for the contract suite. Their availability is reported through the orchestrator capability endpoint.

## Install the GUI

From the repository root:

```bash
npm ci
```

Run the GUI:

```bash
npm run dev:gui
```

Build it:

```bash
npm run build:gui
```

Run GUI tests:

```bash
npm run test:gui
```

Lint and formatting checks:

```bash
npm run lint
npm run format:check
```

## Install the orchestrator

The full orchestrator package contains optional/heavier media and AI dependencies. From the repository root:

```bash
cd apps/orchestrator
python -m pip install -e .
```

Run the service:

```bash
python -m uvicorn orchestrator.main:app --reload --port 8000
```

Or, after installation, from the repository root:

```bash
npm run dev:api
```

Useful endpoints:

```text
GET  /health
GET  /status
GET  /capabilities
GET  /metrics
POST /api/pipeline/create
GET  /api/pipeline/{pipeline_id}/status
```

The GUI uses `http://127.0.0.1:8000` by default. Override it with:

```bash
VITE_ORCHESTRATOR_URL=http://127.0.0.1:8000 npm run dev:gui
```

## Dependency-light contract tests

These tests are intentionally runnable without GPU, renderer, local-model, FFmpeg, or Firejail runtime dependencies.

```bash
python -m pip install \
  "pydantic>=2.5,<3" \
  "pytest>=7.4,<9" \
  "pytest-asyncio>=0.21,<1"

PYTHONPATH=apps/orchestrator pytest -q \
  apps/orchestrator/tests/test_portfolio_contract.py \
  apps/orchestrator/tests/test_sandbox_runtime_contract.py
```

They verify semantics such as:

- explicit fixture-mode opt-in;
- deterministic fixture planning;
- capability reporting;
- isolation of Pydantic mutable defaults;
- distinct `fixture_complete`, `unsupported`, `complete`, and `error` states;
- generated-code import/call restrictions;
- staging-path traversal rejection;
- no direct host-execution fallback when sandbox support is absent or unverified.

## Data provenance in the GUI

The frontend distinguishes three sources of displayed data:

- **demo:** deterministic synthetic values for presentation/UI development;
- **fixture:** deterministic backend values for orchestration tests;
- **live:** values returned by an actual backend, renderer, analyzer, or measurement source.

Do not introduce randomized telemetry or simulated readiness that visually resembles a live measurement. New panels should either use real backend state or label their data source explicitly.

## Adding a capability

A new integration should move through these stages:

```text
interface
  ↓
explicit unsupported behavior
  ↓
deterministic tests
  ↓
real external execution
  ↓
retained artifact / benchmark
  ↓
public claim promotion
```

Do not skip from “interface exists” to “production-ready.”

## Generated-code execution

Generated Python/renderer code is untrusted input.

The current execution contract requires the supported Firejail path. Static AST/path checks are defense-in-depth and do not replace runtime isolation. If the required sandbox backend is unavailable, the correct result is `unsupported`, not direct host execution.

Before promoting the sandbox to verified runtime isolation, test it on an appropriate Linux host for:

- network denial;
- environment/secret stripping;
- filesystem boundaries;
- path traversal;
- process-tree timeout termination;
- output confinement;
- missing-backend behavior;
- Blender/Python no-fallback behavior.

See [`SECURITY.md`](SECURITY.md) and issue #27.

## Reference artifact discipline

The highest-priority engineering milestone is issue #17. A reference run should retain:

```text
prompt
scene plan
generated source
execution command
exit status
logs
rendered MP4
quality measurement
configuration / dependency notes
```

A fixture or UI demo does not substitute for that artifact chain.

## Pull-request discipline

Before merging a capability change:

1. update or add tests;
2. verify failure semantics;
3. remove or label synthetic output;
4. update `docs/IMPLEMENTATION_STATUS.md` when the implementation state changes;
5. update `docs/CLAIMS.md` only when the evidence supports stronger public wording;
6. keep README instructions reproducible from a clean checkout.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the public contribution rule.
