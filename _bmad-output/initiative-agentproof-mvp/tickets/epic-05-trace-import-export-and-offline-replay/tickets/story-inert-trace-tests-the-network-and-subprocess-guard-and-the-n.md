---
id: 5
type: story
title: "Inert-Trace tests, the network and subprocess guard, and the networkless CI step"
parent: epic-05-trace-import-export-and-offline-replay
covers: [R5]
after: [4, "1.6"]
hitl: false
risk: medium
refined: true
---

# Inert-Trace tests, the network and subprocess guard, and the networkless CI step

## Description

The "traces are data" and "no network" claims become tests that run everywhere: an in-process guard for the whole suite, an equivalence test for hostile Trace content, and a CI step that runs the example inside a container with no network at all.

## Requirements

1. **Guard** (R5; spine AD-17; PRD AC-9.2)
   **Given** `tests/conftest.py`
   **When** any test runs without `@pytest.mark.allow_subprocess`
   **Then** `socket.socket` and `subprocess.Popen` raise; a sample core test that opens a socket fails; the CLI subprocess tests carry the marker and still pass.
2. **Inert Trace** (R5; PRD AC-9.1; spine AD-12 for later rendering)
   **Given** a Trace whose arguments, results, metadata, and output contain `rm -rf /`, `https://evil.example`, `<script>alert(1)</script>`, and `__import__('os')`
   **When** evaluated and replayed
   **Then** the results equal those of a twin Trace with plain strings of the same length, and no subprocess or socket was created.
3. **Networkless container step** (R5; spine AD-17)
   **Given** the CI workflow
   **When** it runs on `ubuntu-latest`
   **Then** a `run:` step executes `docker run --network none` with the built wheel installed, runs `agentproof init`, `run`, and `trace replay` inside, and the job fails if any command exits unexpectedly.
4. **Replay makes no calls** (R5; PRD AC-19.1)
   **Given** the guard active and the environment cleared
   **When** `trace replay` runs in-process
   **Then** it completes.

## Boundaries

- Must not change: the pipeline.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-05-trace-import-export-and-offline-replay/epic-05-trace-import-export-and-offline-replay.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, AD-18
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-9, AC-9.1, AC-9.2, NFR-3

## Notes

- Files: `tests/conftest.py`, `tests/integration/test_inert_trace.py`, `tests/fixtures/traces/hostile.trace.json`, `.github/workflows/ci.yml` (networkless step).
- Tests: as listed.
- Depends on: story 4 and 1.6 (the wheel artifact the container step installs; both edit `ci.yml`, so they are serialized). Risk: medium; the container step is Linux-only by nature.
- Done when: criteria 1 to 4 pass.
