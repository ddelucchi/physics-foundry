# Physics Foundry Development Guide

This guide describes the repository as it exists today. The project is a research prototype; some renderer, media, and autonomous-generation paths remain incomplete.

## Prerequisites

- Node.js 20+ and npm
- Python 3.11
- Git
- optional renderer/toolchain dependencies for the specific experiments you want to run

A GPU is optional for the core GUI/orchestrator development path.

## GUI

```bash
npm ci
npm run dev:gui
```

Quality checks:

```bash
npm run lint
npm run format:check
npm test
npm run build
```

## Orchestrator

```bash
cd apps/orchestrator
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pytest -q
```

On Windows:

```powershell
.venv\Scripts\activate
```

Run the API during development:

```bash
python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000
```

## Optional just commands

A root `justfile` mirrors the common development commands for contributors who use the `just` command runner.

```bash
just --list
just dev-gui
just dev-api
just test
just lint
```

The justfile intentionally contains only commands backed by the current repository. Proposed renderer/deployment commands belong in design documents until corresponding implementations exist.

## Architecture

- `apps/gui` is the canonical React/Vite interface.
- `apps/orchestrator` is the canonical FastAPI service.
- `config` contains local runtime/color-management configuration.
- `docs` contains design notes and target-state documents.
- `scripts` contains supporting local utilities.

## Contribution standard

A new feature should:

1. distinguish implemented behavior from target behavior;
2. include a reproducible test or validation procedure where practical;
3. avoid embedding machine-local absolute paths;
4. fail visibly rather than swallowing build/test errors;
5. keep secrets outside version control;
6. update the README when the implementation boundary materially changes.
