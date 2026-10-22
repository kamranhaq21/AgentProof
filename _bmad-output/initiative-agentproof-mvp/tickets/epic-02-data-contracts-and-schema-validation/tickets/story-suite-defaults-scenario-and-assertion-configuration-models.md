---
id: 2
type: story
title: "Suite, defaults, scenario, and assertion configuration models"
parent: epic-02-data-contracts-and-schema-validation
covers: [R2, R5]
after: [1]
hitl: false
risk: high
refined: true
---

# Suite, defaults, scenario, and assertion configuration models

## Description

The shape of what a user writes. Every validation rule the PRD places at load time lives here as a model rule so the loader (epic 3) and the public API agree. High risk because every later epic reads these models.

## Requirements

1. **Assertion configuration union** (R2; spine AD-8; PRD FR-10, AC-13.2)
   **Given** `agentproof.models.assertions`
   **When** it is imported
   **Then** six frozen config models exist with `type` literals `tool_called`, `tool_not_called`, `tool_call_count`, `tool_arguments_match`, `tool_order`, `final_output_contains`, their fields per PRD FR-11 to FR-16 (`tool`, `equals|greater_than|less_than`, `arguments` as a path-to-value mapping, `tools` list, `value`, `case_sensitive` default true), an optional `id`, and `AssertionConfig` is the discriminated union; `tool_call_count` with zero or two operators raises a validation error naming the field.
2. **Suite and defaults** (R2; spine Schemas seed; PRD Glossary Suite defaults)
   **Given** `agentproof.models.suite`
   **When** the spine's Suite YAML seed, loaded to a dict, is validated
   **Then** it yields a Suite with `version == 1`, `suite`, optional `description`, `SuiteDefaults(adapter, fail_on_missing_trace=True, fixture.deterministic, compare.include_arguments, redact.keys/paths/env)`, and Scenarios with `id`, optional `description`, optional `skip`, `input`, optional `trace`, and `assertions` with at least one item.
3. **Ids** (R2; PRD AC-2.5, AC-3.1, AC-17.4; spine AD-8, AD-14)
   **Given** a Suite dict
   **When** it is validated
   **Then** each Assertion without `id` gets `<type>-<0-based index>`; two Scenarios with ids equal case-insensitively, a Scenario id outside `SCENARIO_ID_RE`, a Windows device name, or two Assertions with the same id in one Scenario raise a validation error naming the id and path.
4. **Frozen and forbid-unknown** (R5; spine AD-3)
   **Given** any model in this story
   **When** an unknown field is supplied or an attribute is assigned after construction
   **Then** validation fails naming the field path, or assignment raises.

## Boundaries

- No YAML parsing; this story validates dicts only.
- Must not change: `constants` names from story 1.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-3, AD-8, AD-14, Schemas (seed)
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-2, FR-3, FR-10 to FR-16, AC-2.5, AC-3.1

## Notes

- Files: `src/agentproof/models/assertions.py`, `src/agentproof/models/suite.py`.
- Tests: `tests/unit/models/test_assertions_config.py`, `tests/unit/models/test_suite.py` with one passing and one failing case per rule in criteria 1 to 4.
- Depends on: story 1. Risk: high; OQ-5 (integer version) and OQ-7 (path syntax) are built as the spine's defaults and a reversal is a schema bump.
- Done when: criteria 1 to 4 pass and the spine's Suite seed validates.
