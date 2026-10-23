---
type: epic
title: "Data contracts and schema validation: every artifact has a frozen versioned model, a Canonical serializer, a generated JSON Schema, and fixtures"
parent: initiative-agentproof-mvp
covers: ["R3", "R7", "R14", "R24", "R28", "C2", "C4", "C6"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: high
---

# Data contracts and schema validation

## Description

The shared dependency every later epic consumes: `constants`, `errors`, the common types, the Canonical serializer with its compact form and volatile-path list, and the Suite, assertion-config, Trace, result, Report, and Comparison models with integer versions, unknown fields rejected, and no strict mode. JSON Schemas are generated from the models and committed with a drift test, and valid and invalid fixtures for schema v1 are archived. Nothing here reads a file or the clock.

## Outcome

For every builder after this epic, the shape of a Suite, Trace, Assertion Result, and Report is a model they import, not a decision they make (initiative Done when: byte-identical artifacts on Linux and Windows).

## Requirements

- R1 (parent R3, C2): `models.trace` defines Trace, TraceEvent, Capture (required, default `unknown`), RedactionState, and Environment with the fields in the spine's Trace seed, RFC 3339 string timestamps validated by `constants.RFC3339_WITH_OFFSET`, contiguous 0-based `seq` validated on the model, and Final Output as `output` on `agent_finished`.
- R2 (parent R7, C4): `models.assertions` defines the six frozen config models and the static discriminated union; `models.suite` defines Suite, SuiteDefaults (`adapter`, `fail_on_missing_trace`, `fixture.deterministic`, `compare.include_arguments`, `redact.keys/paths/env`), and Scenario with `id`, `description`, `skip`, `input`, `trace`, and at least one Assertion, assigns default Assertion ids `<type>-<index>`, and rejects duplicate ids, ids outside the charset, case-insensitive duplicates, and Windows device names.
- R3 (parent R14): `models.result` defines AssertionResult, ScenarioResult, SuiteOutcome, and `models.report` defines Report with the Suite defaults snapshot and embedded Traces, and Comparison, matching the spine's Report seed.
- R4 (parent R24, C6): `models.canonical` provides `dumps` (sorted keys, two-space indent, non-ASCII preserved, trailing newline), `dumps_compact`, and `VOLATILE_PATHS` as the spine lists them; NaN and infinity are rejected by the models.
- R5 (parent R28, C2): Every serialized model carries `version: int`; `constants.SUPPORTED_VERSIONS` lists suite, trace, and report version 1; `python -m agentproof.models.export_schemas` writes `schemas/*.schema.json` and a test fails on drift.
- R6 (parent C2): `constants` holds SUPPORTED_VERSIONS, SCENARIO_ID_RE, WINDOWS_DEVICE_NAMES, RFC3339_WITH_OFFSET, REDACTED, MAX_*_BYTES, and STATEMENTS; `errors` holds the full taxonomy with `Violation`; `models.common` holds JsonValue and Status.

## Constraints

- Covered parent constraints: C2 (frozen forbid-unknown models, integer versions, generated schemas, contiguous seq), C4 (assertion config models and union in `models.assertions`), C6 (Canonical form and the one volatile list); the lines below say how.
- Spine AD-3: `ConfigDict(frozen=True, extra="forbid")`, no `strict`; models are validated only through `model_validate(dict)`.
- Spine AD-1, AD-2: these packages sit at the bottom of the core and import nothing above `constants`.
- Spine AD-4: JSON Schemas are never hand-edited.
- Open decisions OQ-5 (integer version, string timestamps, Final Output location) and ARCH-3 (contiguous seq) are built as the spine's defaults.

## Done when

- `python -m agentproof.models.export_schemas` produces three schema files that validate the fixtures with `jsonschema` in tests, and the drift test passes (R5).
- Every invalid fixture in `tests/fixtures/schema/v1/invalid/` raises the taxonomy error the fixture's name states, with a field path (R1, R2, R6).
- A hypothesis round-trip test proves `parse → dumps → parse` is identity for Suite, Trace, and Report, and `dumps` output is byte-identical on Linux and Windows CI for the golden fixtures (R4).
- The Assertion-id default, charset, uniqueness, and device-name rules each have a passing and a failing test (R2).
- Production delivery: the models ship in the wheel and `agentproof version` prints the supported Schema Versions (R5).

## Boundaries

- No parsing of files or YAML text (epic 3), no evaluation (epic 4), no I/O (epic 5), no rendering (epic 6).
- Must not change: the package layout and contracts from epic 1.
- Touch point: `schemas/` at the repository root; owner: this epic.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-3, AD-4, AD-5, AD-8, AD-11, AD-14, Schemas (seed)
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, section 3 Glossary, FR-5, FR-17, FR-22, NFR-8
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-003, ADR-004, ADR-005, ADR-011

## Notes

- Decision (2026-10-22): tracer bullet is story 1, constants plus errors plus the Canonical serializer with its first golden file; it proves the byte-identity claim before any model exists.
- Decision (2026-10-22): `seq` contiguity is validated on the Trace model (not only in `parse_trace`) so every path into a Trace object enforces it.
- Assumption: epic refined from the initiative, PRD, and spine alone; nothing more was needed.
- Open question: OQ-5 should be confirmed before story 2 starts; building the defaults and changing later costs a schema version bump.
