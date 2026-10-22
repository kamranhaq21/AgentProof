---
id: 4
type: story
title: "Result, outcome, Report, and Comparison models"
parent: epic-02-data-contracts-and-schema-validation
covers: [R3, R5]
after: [2, 3]
hitl: false
risk: medium
refined: true
---

# Result, outcome, Report, and Comparison models

## Description

What the engine returns and what reviewers read. Fixing the Report shape now lets the viewer, the GitHub Actions artifact, and `compare` all target one contract.

## Requirements

1. **Results and outcome** (R3; spine AD-6, Schemas seed; PRD FR-17, AC-17.1, AC-17.4)
   **Given** `agentproof.models.result`
   **When** it is imported
   **Then** `AssertionResult(assertion_id, type, status, message, evidence: list[int], detail)`, `ScenarioResult(scenario_id, status, skip_reason, execution_error, counts, assertions, trace, cost)`, and `SuiteOutcome(scenarios, suite_status, execution_failed, evaluated_assertions)` exist; `status` accepts only the four values.
2. **Report** (R3; spine AD-13, Schemas seed; PRD FR-22, AC-22.1, AC-22.3, AC-22.4)
   **Given** the spine's Report JSON seed
   **When** it is validated
   **Then** it yields a Report with `version == 1`, `suite_id`, `run_id`, `created_at`, `package_version`, `schema_versions`, `defaults` as a `SuiteDefaults`, `suite_status`, `execution_failed`, `counts`, and `scenarios` whose embedded `trace` is a Trace or null; a validator rejects a Report whose top-level `counts` differ from the sum over Assertion Results.
3. **Comparison** (R3; PRD FR-26)
   **Given** `agentproof.models.report`
   **When** it is imported
   **Then** `Comparison` carries per-scenario status changes, assertion-id set differences, tool-sequence differences, selected-argument differences, added and removed scenarios, duration and cost differences when present on both sides, `regressed: bool`, and the saved-data statement.
4. **Serialization** (R5; spine AD-11)
   **Given** a Report
   **When** `canonical.dumps` serializes it
   **Then** `defaults`, `scenarios`, and `trace` keys appear in sorted order and every optional field is written as `null`.

## Boundaries

- No building of Reports (epic 6) or Comparisons (epic 7); models only.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-13, Schemas (seed)
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-17, FR-22, FR-26

## Notes

- Files: `src/agentproof/models/result.py`, `src/agentproof/models/report.py`.
- Tests: `tests/unit/models/test_result.py`, `tests/unit/models/test_report.py` including the counts validator and the seed round trip.
- Depends on: stories 2 and 3. Risk: medium.
- Done when: criteria 1 to 4 pass.
