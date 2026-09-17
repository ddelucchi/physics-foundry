# Physics Foundry

Physics Foundry is a local-first research prototype for AI-assisted physics visualization. It explores how a physics prompt can move through typed planning, orchestration, renderer-specific code generation, execution, media processing, and quality-analysis stages without pretending that every downstream stage is already autonomous or production-ready.

## Current status

Implemented infrastructure includes:

- FastAPI orchestration service
- typed request/response and pipeline-state models
- REST and progress/event plumbing
- error classification and recovery infrastructure
- observability and metrics hooks
- sandbox/execution interfaces
- media-pipeline and quality-gate modules
- React/Vite user interface
- renderer-oriented workflow concepts for Manim, Taichi, Blender, and related tools
- local OpenAI-compatible model integration points

Still experimental or incomplete:

- fully autonomous prompt-to-video execution
- reliable renderer selection across all supported engines
- complete renderer execution on every path
- automatic semantic repair of generated scenes
- production audio alignment and final assembly
- deployment hardening

Some pipeline paths remain mocked, simulated, or scaffolded. The repository should be evaluated as software architecture and research tooling, not as a finished autonomous studio.

## Repository layout

```text
apps/
  gui/            React/Vite interface
  orchestrator/   FastAPI orchestration service
config/           runtime and color-management configuration
docs/             design and portfolio notes
scripts/          local development utilities
```

The canonical UI lives under `apps/gui`; the canonical Python service lives under `apps/orchestrator`.

## GUI development

```bash
cd apps/gui
npm ci
npm run lint
npx prettier --check .
npx vitest run
npm run build
```

## Orchestrator development

Python 3.11 is the current target.

```bash
cd apps/orchestrator
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
pytest -q
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`.

## CI policy

The repository CI is intentionally strict: build, lint, format, or test failures are failures. The previous workflow pattern that swallowed failures with shell fallbacks has been removed.

CI validates the software that actually exists. It does not manufacture placeholder tests during the workflow.

## Design principles

### Typed state over prompt soup

Pipeline stages communicate through explicit structures rather than treating an entire project as one untyped LLM conversation.

### Local-first execution

The architecture supports local model servers and local renderer execution so the orchestration layer is not inherently tied to one hosted model provider.

### Observable failure

Errors are classified and carried through explicit recovery paths. A failed renderer or model request should not be silently converted into a successful pipeline state.

### Evidence before quality claims

A visual-quality score is only as meaningful as its measurable inputs and validation procedure. The project therefore treats automated quality analysis as experimental tooling, not as proof of publication-quality output.

## Security

Do not commit model-provider keys, local tokens, or renderer credentials. Runtime secrets belong in ignored environment/local configuration. See [SECURITY.md](SECURITY.md).

## License

Physics Foundry is licensed under the MIT License. See [LICENSE](LICENSE).
