# GUI data-provenance boundary

Physics Foundry deliberately separates presentation fixtures from service-backed state.

- **Demo:** deterministic synthetic values used to exercise interface behavior. Demo values are not measurements.
- **Fixture:** deterministic backend/test values used to verify orchestration semantics. Fixture completion is not rendered-media completion.
- **Live:** values returned by an actual service, renderer, analyzer, local browser resource, or measurement path.

Current GUI boundary:

| Surface | Provenance |
| --- | --- |
| Request ledger | local UI records |
| Pipeline | live orchestrator REST state when the service is reachable |
| System | live `/status` + `/capabilities` state when the service is reachable |
| Code review | deterministic demo revisions |
| Audio review | real local browser playback + deterministic alignment fixture |
| QA dashboard | deterministic demo metrics |
| Frame review | real local browser image preview + deterministic QA fixture |

A component may not label random, delayed, canned, or hard-coded values as live telemetry. A successful demo interaction may not be surfaced as evidence that the underlying backend capability exists.

The canonical frontend is `apps/gui/`. The old root-level duplicate frontend and unreachable enhanced prototype screens have been removed from the hardening branch.
