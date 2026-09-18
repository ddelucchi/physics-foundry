# Physics Foundry Product Vision

This document describes the **target product direction** for Physics Foundry. It is not an implementation-status document and must not be used as evidence that every component below is operational.

For current evidence, use [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) and [`CLAIMS.md`](CLAIMS.md).

## Product thesis

Physics Foundry explores a local-first scientific-media workflow in which a bounded physics request can be transformed into a structured scene plan, generated renderer code, observable execution jobs, reviewable media artifacts, and quality-analysis results.

The long-term product should make every transformation inspectable. A user should be able to see not only the final video, but also the plan, generated source, execution environment, renderer logs, artifacts, quality measurements, and any remediation decisions.

## Design principles

### 1. Evidence before automation

The system should never report successful production output merely because a simulated workflow completed. Real execution, fixtures, demos, unsupported states, and errors must remain distinguishable.

### 2. Local-first, capability-aware operation

The intended deployment model favors locally controlled models, renderers, media tools, and artifacts. The application should detect what is actually available on the current machine and degrade by reporting unavailable capabilities rather than inventing success.

### 3. Typed orchestration

Planning, rendering, quality analysis, and artifact management should communicate through explicit schemas and status models rather than ad-hoc state.

### 4. Renderer independence

Manim, Taichi, Blender, or future engines should sit behind separable interfaces. A renderer integration is considered complete only after its real artifact path is reproducible.

### 5. Generated code is untrusted

Static source policy is defense-in-depth only. Real generated-code execution must occur through a verified isolation boundary, with no silent direct-host fallback.

### 6. Human-reviewable artifacts

Plans, generated source, commands, logs, media outputs, checksums, quality measurements, and revisions should be retained whenever practical so a run can be audited and reproduced.

## Target workflow

```text
physics request
    ↓
structured scene plan
    ↓
script / visual beat representation
    ↓
renderer selection
    ↓
generated source
    ↓
validation + isolated execution
    ↓
rendered media artifact
    ↓
measured quality checks
    ↓
human review / bounded remediation
    ↓
assembly + export
```

The current portfolio milestone intentionally implements and verifies this workflow one narrow vertical slice at a time rather than claiming full autonomous coverage.

## Product surfaces

### GUI

Target responsibilities:

- project creation and inspection;
- pipeline/job status;
- generated-source review;
- renderer logs and artifacts;
- QA visualization;
- audio/timing review;
- capability and system-state visibility;
- explicit provenance labels for demo, fixture, and live data.

Current implementation status varies by panel. Pipeline and system monitoring are backend-driven; other presentation surfaces remain partly demo/prototype behavior.

### Orchestrator

Target responsibilities:

- validate incoming requests;
- construct typed plans;
- coordinate renderer jobs;
- expose status and logs over REST/WebSocket paths;
- report capability availability;
- enforce generated-code execution boundaries;
- persist artifacts and metadata;
- coordinate quality checks and bounded retries.

### Renderer integrations

Potential engine roles:

- **Manim:** equations, derivations, graphs, geometric constructions, and 2D scientific animation;
- **Taichi:** particle/field simulation and GPU-oriented numerical visualization;
- **Blender:** 3D scientific scenes, camera work, and physically richer geometry.

These roles are architectural targets. The presence of an interface or worker does not establish end-to-end renderer readiness.

### Quality analysis

Target checks may include image similarity, motion stability, text legibility, clipping, artifact detection, timing consistency, and other inspectable measurements.

A quality threshold is useful only when it is computed from a real produced artifact. Deterministic synthetic QA remains appropriate for UI development but must be labeled as demo data.

### Audio and timing

The product vision includes narration ingestion, transcription/alignment, beat timing, and eventual timeline assembly. Those paths remain experimental until a reproducible real artifact demonstrates them.

## Reliability model

Terminal states should preserve meaning:

- `complete`: real supported operation completed;
- `fixture_complete`: deterministic orchestration fixture completed;
- `unsupported`: required real capability unavailable or unwired;
- `error`: supported operation attempted and failed.

Retries should be bounded and observable. Fallbacks may change implementation strategy, but they must not lower the evidence standard for success.

## Security model

Generated renderer code is considered untrusted. The target runtime should minimize inherited environment access, filesystem visibility, network access, capabilities, and child-process escape surface.

The current project does **not** claim hardened hostile multi-tenant isolation. Runtime sandbox verification is tracked separately.

## Portfolio acceptance criterion

The first reference production path is deliberately narrow:

1. accept one bounded physics prompt;
2. produce a schema-valid scene plan;
3. persist generated Manim source;
4. execute through the supported isolation path;
5. produce a non-empty MP4;
6. compute at least one real QA measurement from that MP4;
7. persist enough source, configuration, logs, and metadata to reproduce the run.

Only after that path is retained and repeatable should the portfolio expand its public claims to broader renderer autonomy.

## Non-goals for current public claims

Physics Foundry is not presently advertised as:

- a commercial-ready autonomous video studio;
- a verified production renderer farm;
- a hardened multi-tenant code-execution service;
- a guarantee of physics correctness;
- a guarantee of pedagogical or visual quality;
- proof that every optional renderer/model dependency works on every machine.

Those may be future ambitions. They are not current evidence.
