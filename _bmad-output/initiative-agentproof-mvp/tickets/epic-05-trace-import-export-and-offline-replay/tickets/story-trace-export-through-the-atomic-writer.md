---
id: 3
type: story
title: "Trace export through the atomic writer"
parent: epic-05-trace-import-export-and-offline-replay
covers: [R3]
after: [2]
hitl: false
risk: medium
refined: true
---

# Trace export through the atomic writer

## Description

The first file the product writes, through the one writer every later artifact uses. A failing CI run leaves the evidence Replay needs.

## Requirements

1. **write_atomic** (R3; spine AD-14; PRD AC-29.3)
   **Given** `io.artifacts.write_atomic(path, data: bytes)`
   **When** called
   **Then** it writes to a `NamedTemporaryFile` in the target's directory with prefix `.agentproof-`, then `os.replace`; on rename failure it raises `ArtifactWriteError` naming the target and leaves the temp file; it is the only function in the package that writes a file, verified by the banned-API rule plus a grep test.
2. **Paths** (R3; spine AD-14; PRD AC-29.1, AC-29.2)
   **Given** `io.paths`
   **When** forming `scenario-<id>.trace.json`
   **Then** it asserts `SCENARIO_ID_RE`, and a symlink inside the Output Directory resolving outside it is refused with `ArtifactWriteError`.
3. **Export from run** (R3; PRD AC-6.1 to AC-6.4)
   **Given** `agentproof run` with the default or `--output DIR`
   **When** it completes
   **Then** each Scenario's redacted Trace is written in Canonical form as `scenario-<id>.trace.json`, validates against the schema, and two deterministic runs produce byte-identical files; a non-fixture adapter's Trace carries the runner's identity fields.
4. **Failure exit** (R3; PRD AC-27.3)
   **Given** a locked target file on Windows or an unwritable directory
   **When** `run` tries to write
   **Then** it exits 3 naming the file and the temp file remains for inspection.

## Boundaries

- No Report file (epic 6).
- Must not change: Canonical form.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-05-trace-import-export-and-offline-replay/epic-05-trace-import-export-and-offline-replay.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-11, AD-13, AD-14
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-6, FR-29, AC-6.x, AC-29.x

## Notes

- Files: `src/agentproof/io/artifacts.py` (`write_atomic`), `src/agentproof/io/paths.py`, `src/agentproof/runner/pipeline.py` (write step).
- Tests: `tests/unit/io/test_write_atomic.py` (including a Windows-only locked-file case), `tests/unit/io/test_paths.py`, `tests/integration/test_run_exports.py` (byte identity across two runs).
- Depends on: story 2. Risk: medium; Windows file locking semantics differ, tested on the Windows CI leg.
- Done when: criteria 1 to 4 pass on both CI platforms.
