# Public claims ledger

This file is intentionally conservative. Public wording should stay at or below the evidence shown here.

| Claim | Status | Evidence / boundary |
| --- | --- | --- |
| Local-first architecture | supported | Configuration and services are designed around locally controlled model/render dependencies. |
| Canonical React/Vite GUI | supported | `apps/gui/` is the sole frontend source tree; stale root duplicate was removed. |
| FastAPI orchestration service | supported | API/service code is present under `apps/orchestrator/`. |
| REST/WebSocket job and progress interfaces | supported | Job/status/event paths are implemented. |
| Dependency/capability reporting | supported | `/status`, `/capabilities`, and dependency-light helpers report explicit environment availability. |
| Backend-driven GUI pipeline state | supported | Pipeline monitor creates/polls orchestrator jobs instead of running a simulated client pipeline. |
| Backend-driven GUI system state | supported | System monitor reads orchestrator status/capabilities instead of random CPU/GPU/readiness values. |
| Deterministic GUI demo data | supported | Code, QA, and alignment presentation fixtures are deterministic and labeled as demo data. |
| Deterministic fixture mode | supported | Explicit opt-in backend mode with a distinct `fixture_complete` terminal state. |
| Production mode avoids fake render success | supported | Unwired real prompt-to-render execution terminates as `unsupported`, not `complete`. |
| Static generated-code policy | supported | Dependency-light AST/import/call checks plus workspace path-traversal rejection are implemented and covered by contract tests. |
| Direct host fallback for generated Blender/Python code | removed by design | Current sandbox wrapper requires the supported Firejail execution path; unavailable isolation returns `unsupported`. |
| Firejail execution wrapper | implemented, runtime verification pending | Per-execution workspace/profile construction, stripped child environment, network-disabled profile, privilege drop, and behavioral no-fallback tests exist. Real hostile-runtime isolation is not yet claimed. |
| nsjail execution path | **not currently claimed** | nsjail may be detected as installed, but the old unverified execution path is not used. |
| Backend frame QA statistics | implemented, artifact verification pending | Analyzer computes reference SSIM only when a compatible reference is supplied, plus Laplacian sharpness variance, edge density, clipped-pixel fraction, and an explicit 8x8 block-boundary heuristic. It does not label these as OCR, temporal motion analysis, or calibrated color accuracy. |
| Reference-based VMAF adapter | implemented, runtime verification pending | FFmpeg/libvmaf adapter requires real reference and distorted videos. Missing reference returns `not_evaluated`, never a perfect score. |
| Prometheus/OpenTelemetry hooks | implemented scaffold | Instrumentation exists; production deployment is not claimed. |
| Multiple renderer interfaces | implemented scaffold | Interfaces/workers exist; complete autonomous multi-engine behavior is not claimed. |
| Real browser playback of user-selected local audio | supported | Audio review panel uses an actual local object URL and browser audio element. It does not claim forced alignment. |
| Forced audio alignment in GUI | **not claimed** | Current word timings are deterministic presentation fixtures only. |
| Measured GUI QA metrics | **not claimed** | Current GUI QA dataset is deterministic demo data; real QA evidence must come from a produced artifact or caller-supplied frames. |
| Reproducible real prompt-to-Manim MP4 pipeline | **not yet established** | Tracked by issue #17. |
| Production-ready autonomous video generation | **not claimed** | Active prototype. |
| Hardened hostile multi-tenant code execution | **not claimed** | Security boundary remains prototype-level; see `SECURITY.md` and issue #27. |
| Guaranteed physics correctness or visual quality | **not claimed** | Generated output requires independent validation. |

## CI interpretation

The current GitHub Actions workflow is designed to run dependency-light orchestration, QA-schema, and sandbox failure-semantic contracts. Recent runs on the hardening branch have terminated before checkout with zero job steps and no retrievable job-log blob. Those runs are treated as runner/infrastructure failures, not evidence that the contract suite passed or failed.

## Promotion rule

A claim is upgraded only when supported by inspectable code plus a deterministic test, reproducible command/artifact, or documented benchmark appropriate to the claim. Interfaces, TODOs, architecture diagrams, fixture values, simulated output, and the mere presence of an external binary are not evidence of a completed real capability.
