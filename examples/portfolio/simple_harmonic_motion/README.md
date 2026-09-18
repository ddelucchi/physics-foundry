# Simple Harmonic Motion reference fixture

This directory is the bounded reference request used to exercise Physics Foundry's **deterministic orchestration semantics** while the real retained renderer proof is still being built.

It is intentionally small:

```text
20-second lesson
one dimension
one mass-spring oscillator
one coordinate axis
no damping
no driving
```

## Input

[`prompt.txt`](prompt.txt) asks for a 20-second introduction to one-dimensional simple harmonic motion showing equilibrium, displacement `x(t)`, and

\[
a = -\omega^2 x.
\]

The bounded prompt is deliberately narrow enough that a future real render can be reviewed for both software behavior and physics correctness without ambiguity.

## Deterministic fixture output

[`expected_fixture_plan.json`](expected_fixture_plan.json) records the expected orchestration fixture:

| Scene | Engine | Duration | Purpose |
| --- | --- | ---: | --- |
| `shm-01` | Manim | 8 s | mass-spring geometry, equilibrium, displacement |
| `shm-02` | Manim | 12 s | restoring acceleration and `a = -ω²x` |

The fixture also records two learning objectives:

1. identify equilibrium and displacement;
2. connect acceleration to displacement through `a = -ω²x`.

## What this proves

This example is evidence that Physics Foundry can maintain a bounded request and a deterministic expected planning fixture for orchestration tests.

It supports testing of concepts such as:

```text
request parsing
    ↓
fixture planning
    ↓
typed status transitions
    ↓
fixture_complete
```

## What this does not prove

This directory is **not** evidence that a real LLM generated Manim source, that Firejail executed generated code, that Manim produced an MP4, or that a QA engine measured that video.

`fixture_complete` is deliberately not equivalent to `complete`.

## Target evidence bundle

Issue #17 promotes this reference from fixture to verified vertical slice only when the retained directory can include a real chain equivalent to:

```text
prompt.txt
scene_plan.json
generated_scene.py
execution.json
renderer.log
output.mp4
qa.json
README.md
```

The evidence should include the exact command, dependency/runtime notes, exit status, generated source before execution, artifact metadata, and at least one real measurement made from the produced media.

That future bundle is the point of this example: not a decorative demo, but a falsifiable reference artifact.
