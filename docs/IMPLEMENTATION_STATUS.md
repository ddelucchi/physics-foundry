# Implementation status

Physics Foundry is an active prototype. This ledger distinguishes implemented architecture, tested orchestration semantics, deterministic demo behavior, and still-unverified external rendering/isolation behavior.

| Area | Status | Evidence / boundary |
| --- | --- | --- |
| Canonical React/Vite interface | implemented prototype | `apps/gui/`; stale root duplicate removed and unreachable template primitives pruned |
| FastAPI service | implemented | `apps/orchestrator/orchestrator/main.py` |
| REST/WebSocket orchestration interfaces | implemented | pipeline/status/event endpoints |
| Capability detection | implemented + dependency-light tests | `core/capabilities.py`, `test_portfolio_contract.py` |
| Fixture-plan construction | implemented + dependency-light tests | `core/fixtures.py`, `test_portfolio_contract.py` |
| Fixture/real terminal-state separation | implemented | `fixture_complete`, `unsupported`, `complete`, `error` are distinct states |
| Production simulated-success behavior | removed | unwired real prompt-to-render path reports `unsupported` instead of sleeping to `complete` |
| GUI pipeline monitor | implemented against backend API | creates/polls orchestrator jobs; no client-side fake completion/progress engine |
| GUI system monitor | implemented against backend API | reads `/status` and `/capabilities`; random hardware/model readiness removed |
| GUI code review surface | deterministic demo | no random “live AI” revisions and no fake rendered state |
| GUI audio review surface | mixed: real playback + deterministic demo alignment | local file playback is real; forced alignment is not wired or claimed |
| GUI QA analysis surface | deterministic demo | read-only fixture values; no analyzer/remediation job is implied |
| Backend frame QA | implemented, retained-artifact verification pending | reference SSIM when a compatible reference is supplied; sharpness variance, edge density, clipping fraction, and 8x8 block-boundary heuristic otherwise |
| QA public schema semantics | implemented + dependency-light contract | misleading unimplemented `optical_flow_stability`, `text_legibility`, `color_accuracy`, and generic `overall_score` fields removed |
| Reference-based VMAF adapter | implemented, runtime verification pending | requires FFmpeg/libvmaf plus two real videos; missing reference returns `not_evaluated` |
| Generated-code static policy | implemented + dependency-light tests | `core/sandbox_policy.py`: import/call policy and workspace path validation |
| Direct unsandboxed generated-code fallback | removed | `core/sandbox.py` refuses execution when supported isolation is unavailable/unverified |
| Sandbox no-fallback behavioral tests | implemented | missing Firejail/unverified nsjail/Blender fallback cannot reach process execution |
| Firejail execution wrapper | implemented, runtime verification pending | per-execution workspace/profile, stripped child environment, network-disabled profile, privilege drop; real-host hostile isolation verification still required |
| nsjail execution | intentionally disabled as verified path | installed-tool detection may report nsjail, but execution does not use the previous unverified path |
| Blender arbitrary host-path staging | intentionally unsupported | avoids exposing arbitrary host paths until a bounded staging contract exists |
| Unused media-pipeline startup coupling | removed | API no longer imports/initializes an unreferenced OCIO/audio scaffold during service boot |
| Prometheus/OpenTelemetry hooks | implemented scaffold | observability modules; production deployment not claimed |
| Renderer abstraction | implemented scaffold | renderer/plugin interfaces exist |
| Real prompt → generated source → Manim → MP4 → measured QA | **not yet verified** | issue #17 |
| Multi-engine autonomous rendering | experimental | not a current portfolio claim |
| Automatic quality remediation | **not claimed** | no closed-loop remediation path is presented as implemented |
| Forced audio alignment stack | experimental/planned integration | GUI no longer simulates alignment execution |

## Status vocabulary

- **implemented**: behavior exists in code under documented conditions.
- **implemented prototype**: a functioning product surface exists but broader production robustness is not claimed.
- **implemented scaffold**: interfaces/infrastructure exist, but the complete capability is not demonstrated end to end.
- **deterministic demo**: synthetic presentation data with stable values and explicit provenance; not a measured capability.
- **verified**: a reproducible test or retained reference artifact demonstrates the claim.
- **runtime verification pending**: code exists, but its external-system behavior has not yet been demonstrated in the required environment.
- **experimental**: code/interfaces exist but behavior and robustness remain under development.

## Hosted CI note

The hardening branch's current Actions runs are terminating before checkout with zero reported job steps and no available job-log blob. That is tracked as an infrastructure/runner failure and is not counted as evidence that the dependency-light tests passed or failed.

The next evidence milestone is issue #17: one real retained Manim artifact chain. Sandbox runtime hardening/verification remains tracked by issue #27. Fixture completion and deterministic GUI demonstrations are deliberately not counted as rendered-video completion.
