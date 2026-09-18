# Security

Physics Foundry is an active research/engineering prototype. It includes code paths intended to execute generated renderer source, which must be treated as untrusted input.

## Current security boundary

The generated-code path now separates three layers:

1. dependency-light static policy checks (`core/sandbox_policy.py`);
2. explicit capability detection (`core/capabilities.py`);
3. an isolation wrapper (`core/sandbox.py`) that refuses direct host execution when the supported backend is unavailable.

Static analysis is defense-in-depth only. It does **not** make arbitrary Python safe to execute. The repository is **not claimed to be hardened for hostile multi-tenant execution**.

## Current invariants

- fixture/test completion is distinct from real execution completion;
- missing generated-code isolation returns `unsupported` instead of running directly on the host;
- the current execution wrapper treats firejail as the supported backend contract;
- nsjail may be detected as installed but is not currently used as a verified execution path;
- Blender has no direct-execution fallback when sandbox support is unavailable;
- staged auxiliary files reject absolute paths and `..` traversal;
- generated Python receives conservative import/call policy checks before execution;
- child execution is launched with a stripped environment rather than inheriting arbitrary host secrets;
- the firejail profile disables network access and applies resource/process restrictions;
- arbitrary external Blender input/output host paths are not currently staged through the sandbox boundary.

## Remaining verification work

The implementation still requires real-host verification of firejail behavior, including:

- absence of the firejail binary;
- timeout/process-tree handling;
- filesystem visibility from inside the sandbox;
- environment-variable isolation;
- network isolation;
- artifact retention and cleanup;
- renderer-specific behavior under headless execution.

That work is tracked in issue #27. Until it is complete, describe the sandbox as a prototype isolation boundary, not a hardened security product.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting mechanism if it is enabled for this repository. If private reporting is unavailable, contact the repository owner privately rather than publishing exploit details in a public issue.

Include the affected file/path, environment assumptions, reproduction steps, and expected impact. Do not include real secrets, credentials, or third-party private data in reports.
