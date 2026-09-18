# Contributing

Physics Foundry is an active prototype. Contributions should make the implementation easier to reproduce and harder to overclaim.

## Before opening a PR

- Keep public claims narrower than repository evidence.
- Add or update tests for changed behavior.
- Prefer explicit failure over silent fallback when an external renderer/model is unavailable.
- Do not report placeholder metrics as measured results.
- Preserve generated plans, source, logs, and artifacts when adding an end-to-end example.
- Update `docs/IMPLEMENTATION_STATUS.md` and `docs/CLAIMS.md` when a capability changes status.

## Definition of done for a new capability

A capability is **implemented** only when its core path is represented by code and can be exercised under documented conditions. A capability is **verified** only when a repeatable test/example demonstrates the claimed behavior. Interfaces or planned integrations should remain labeled scaffold/experimental until then.
