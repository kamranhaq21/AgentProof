---
id: 5
type: story
title: "Generated JSON Schemas, drift test, and schema v1 fixtures"
parent: epic-02-data-contracts-and-schema-validation
covers: [R5, R1, R2, R3]
after: [4]
hitl: false
risk: medium
refined: true
---

# Generated JSON Schemas, drift test, and schema v1 fixtures

## Description

Other stacks validate against published schemas; those schemas must be the models, not a copy. The fixture archive starts here so every later schema version can be tested against the old readers.

## Requirements

1. **Export** (R5; spine AD-4)
   **Given** `python -m agentproof.models.export_schemas`
   **When** it runs
   **Then** it writes `schemas/suite-v1.schema.json`, `schemas/trace-v1.schema.json`, `schemas/report-v1.schema.json` from `model_json_schema()` in Canonical form, with field descriptions present for every serialized field.
2. **Drift test** (R5; spine AD-4)
   **Given** the committed schema files
   **When** the test regenerates them in memory and diffs
   **Then** it passes; and when a committed file is edited by hand, it fails naming the file.
3. **Fixtures** (R1, R2, R3; PRD NFR-8, NFR-5)
   **Given** `tests/fixtures/schema/v1/valid/` and `invalid/`
   **When** the fixture test runs
   **Then** every valid fixture validates both with the model and with `jsonschema` against the committed schema, and every invalid fixture (unknown field, missing version, unsupported version, duplicate id, seq gap, naive timestamp, unknown event type, NaN, disallowed environment key, zero assertions) fails with the error class and field path its name states.
4. **jsonschema is dev-only** (R5; spine AD-16)
   **Given** the installed wheel
   **When** `agentproof` is imported
   **Then** `jsonschema` is not imported, verified by a test that checks `sys.modules`.

## Boundaries

- Must not change: the models; a schema that looks wrong is fixed in the model, never in the file.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-4, AD-16
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, NFR-5, NFR-8

## Notes

- Files: `src/agentproof/models/export_schemas.py`, `schemas/*.schema.json`, `tests/fixtures/schema/v1/**`, `tests/unit/test_schema_drift.py`, `tests/unit/test_fixtures_v1.py`.
- Tests: as listed; `jsonschema` added to the dev dependency group only.
- Depends on: story 4. Risk: medium; Pydantic's schema output can change between minor versions, which the drift test will surface on dependency bumps by design.
- Done when: criteria 1 to 4 pass.
