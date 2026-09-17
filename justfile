default:
  @just --list

dev-gui:
  cd apps/gui && npm run dev

dev-api:
  cd apps/orchestrator && python -m uvicorn orchestrator.main:app --reload --host 127.0.0.1 --port 8000

build:
  cd apps/gui && npm run build

test:
  cd apps/gui && npm test
  cd apps/orchestrator && python -m pytest -q

lint:
  cd apps/gui && npm run lint
  cd apps/orchestrator && python -m ruff check orchestrator tests

format-check:
  cd apps/gui && npm run format:check
  cd apps/orchestrator && python -m black --check orchestrator tests
