# Physics Foundry Portfolio Roadmap

This roadmap is intentionally narrower than the product vision. It defines the work required for the repository to serve as a defensible software-engineering portfolio artifact.

## Definition of portfolio-ready

Physics Foundry is portfolio-ready when a fresh checkout can reproduce at least one complete real pipeline:

```text
prompt
  -> validated scene plan
  -> generated Manim source
  -> isolated execution
  -> rendered MP4
  -> measured quality report
```

The run must use a documented example, retain reviewable intermediate artifacts, and fail with explicit diagnostics when a dependency or stage is unavailable.

## Completed hardening groundwork

- [x] Remove the old sleep-based production path that could end in `complete` without media.
- [x] Add explicit `fixture_complete` and `unsupported` terminal meanings.
- [x] Add opt-in deterministic fixture planning.
- [x] Add dependency/capability reporting.
- [x] Remove direct generated-code host fallback when isolation is unavailable or unverified.
- [x] Add static generated-code import/call/path policy.
- [x] Add dependency-light policy and no-fallback behavioral tests.
- [x] Replace randomized GUI system telemetry with backend status/capability reads.
- [x] Replace the simulated client-side video pipeline with backend job creation/status polling.
- [x] Replace randomized QA/code/alignment presentation with deterministic, labeled demo behavior.
- [x] Remove stale duplicate root frontend and stale duplicate root PRD.
- [x] Rebuild README/development/product docs around evidence rather than target architecture.

## P0: one real Manim vertical slice

- [x] Provide deterministic fixture planning for orchestration development.
- [ ] Introduce a dedicated validated scene-plan model for the reference slice.
- [ ] Generate runnable Manim source from the bounded reference request.
- [ ] Persist generated source before execution.
- [ ] Execute the source through the supported isolation path on a suitable host.
- [ ] Produce a non-empty MP4.
- [ ] Run at least one real quality-analysis step on that produced artifact.
- [ ] Persist plan, source, command, exit status, logs, render, and quality result.
- [ ] Add fixture-mode API/job lifecycle integration coverage.
- [ ] Add a single documented clean-checkout reproduction command/script.

Tracked by issue #17.

## P1: reproducibility and failure semantics

- [x] Document the core Node/Python development paths.
- [x] Add a dependency-light GitHub Actions workflow that can fail normally once a runner starts.
- [ ] Resolve the current GitHub runner/infrastructure condition where jobs terminate before checkout with zero steps.
- [ ] Add API lifecycle coverage for fixture mode.
- [ ] Add WebSocket state-transition coverage for fixture mode.
- [x] Make missing/unwired external dependencies report explicit capability/unsupported states rather than simulated success.
- [ ] Normalize renderer/dependency/timeout failures into a small public error-code taxonomy.

## P2: sandbox runtime evidence

- [x] Per-execution workspace construction.
- [x] Reject absolute and parent-traversal staging paths.
- [x] Remove unverified nsjail execution and Blender direct fallback.
- [x] Strip the child environment to an explicit allowlist.
- [x] Build a Firejail profile with network denial, `nonewprivs`, capability drop, seccomp, and memory/CPU constraints.
- [x] Add dependency-light tests proving missing/unverified isolation cannot reach process execution.
- [ ] Verify network denial from inside a real sandboxed child.
- [ ] Verify inherited secrets/environment are absent on a real host.
- [ ] Verify filesystem boundaries and output confinement on a real host.
- [ ] Verify timeout/process-tree termination on a real host.
- [ ] Verify one successful bounded Manim execution through the same isolation path.

Tracked by issue #27.

## P3: scientific and visual quality

- [x] Separate deterministic GUI QA presentation from measured QA claims.
- [ ] Define the minimal measured checks for the reference Manim artifact.
- [ ] Compute and retain at least one real metric from the produced MP4/frames.
- [ ] Add a short human-review note for physics correctness on the reference scene.
- [ ] Keep render success and scientific correctness as separate review dimensions.

## P4: renderer breadth

Only after the Manim vertical slice is reproducible:

- [ ] Taichi reference scene.
- [ ] Blender reference scene.
- [ ] renderer-selection experiment.
- [ ] multi-renderer composition.

Renderer count is not itself a completion metric. Each renderer needs a reproducible artifact and explicit failure behavior.

## P5: audio and timing

- [x] Support real local audio selection/playback in the GUI without claiming alignment.
- [x] Label current alignment timings/confidence as deterministic demo data.
- [ ] reference narration input retained with an artifact run.
- [ ] real transcription/alignment path.
- [ ] timeline synchronization.
- [ ] loudness normalization.
- [ ] final assembly test.

## Claims discipline

Public documentation uses the following distinction:

- **Implemented:** executable and inspectable in the repository under documented conditions.
- **Implemented scaffold:** useful interfaces/infrastructure exist, but the full capability is not demonstrated.
- **Deterministic demo / fixture:** synthetic or test data whose provenance is explicit and which is not presented as measured production output.
- **Runtime verification pending:** implementation exists but needs evidence on the required external system.
- **Verified:** a repeatable test, retained artifact, or benchmark establishes the exact claim.
- **Planned:** design intent only.

No feature is promoted because an interface, TODO, configuration key, installed binary, or attractive dashboard exists.
