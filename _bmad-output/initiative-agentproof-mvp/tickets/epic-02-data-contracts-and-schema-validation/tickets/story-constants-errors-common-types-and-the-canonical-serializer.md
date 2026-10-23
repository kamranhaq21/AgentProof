---
id: 1
type: story
title: "Constants, errors, common types, and the Canonical serializer"
parent: epic-02-data-contracts-and-schema-validation
covers: [R4, R6]
after: ["1.3", "1.4"]
hitl: false
risk: medium
refined: true
---

# Constants, errors, common types, and the Canonical serializer

## Description

The bottom of the core: the constants every module shares, the error taxonomy, the JSON value and status types, and the one serializer whose output the byte-identity promise depends on. The first golden file is committed here, so the determinism claim is tested before any model exists.

## Requirements

1. **Constants** (R6; spine AD-3, AD-10, AD-14, AD-19, AD-20)
   **Given** `agentproof.constants`
   **When** it is imported
   **Then** it defines `SUPPORTED_VERSIONS = {"suite": (1,), "trace": (1,), "report": (1,)}`, `SCENARIO_ID_RE`, `WINDOWS_DEVICE_NAMES`, `RFC3339_WITH_OFFSET`, `REDACTED = "[REDACTED]"`, `MAX_SUITE_BYTES`, `MAX_TRACE_BYTES`, `MAX_REPORT_BYTES` (each 5 MB), and `STATEMENTS` with the saved-data, redaction-limits, capture, and §5-limits strings from the PRD.
2. **Error taxonomy** (R6; spine AD-7)
   **Given** `agentproof.errors`
   **When** it is imported
   **Then** `AgentProofError`, `InputError` with `violations: list[Violation]`, `SuiteError`, `TraceFormatError`, `PathError`, `UnsupportedVersionError`, `ExecutionError`, `AdapterLoadError`, `AdapterRunError`, `TraceMissingError`, `ArtifactWriteError` exist with that hierarchy, and a test asserts no other module defines an exception class.
3. **Common types** (R6)
   **Given** `agentproof.models.common`
   **When** it is imported
   **Then** `JsonValue` is the recursive union from the spine conventions and `Status` is `Literal["passed", "failed", "error", "skipped"]`.
4. **Canonical serializer** (R4; spine AD-11; PRD Glossary Canonical form)
   **Given** `agentproof.models.canonical`
   **When** `dumps` serializes the golden input
   **Then** the output has sorted keys, two-space indent, non-ASCII preserved, a trailing newline, and equals `tests/golden/canonical-1.json` byte for byte on Linux and Windows CI; `dumps_compact` of a nested object is one line with sorted keys and no spaces; `VOLATILE_PATHS` lists exactly the spine's patterns.

## Boundaries

- No models beyond `common`; no I/O.
- Must not change: the contracts from epic 1; this package must pass `lint-imports` importing only `errors` and `constants`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-7, AD-11, AD-19, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, section 3 Glossary (Canonical form), AC-26.6, AC-31.4, AC-33.3

## Notes

- Files: `src/agentproof/constants.py`, `src/agentproof/errors.py`, `src/agentproof/models/common.py`, `src/agentproof/models/canonical.py`, `tests/golden/canonical-1.json`.
- Tests: `tests/unit/test_constants.py`, `tests/unit/test_errors_taxonomy.py`, `tests/unit/test_canonical.py` (golden, compact, float repr, non-ASCII), run on both CI platforms.
- Depends on: 1.3 (contracts) and 1.4 (CI on both platforms). Risk: float formatting differences across Python minors; the golden input avoids floats that differ in repr.
- Done when: criteria 1 to 4 pass on both CI platforms.
