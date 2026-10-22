---
type: epic
title: "Baseline comparison: any JSON Report is a Baseline and compare reports regressions excluding volatile paths"
parent: initiative-agentproof-mvp
covers: ["R16", "C3", "C6"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: medium
---

# Baseline comparison

## Description

The third question the product answers: did the latest change make it worse. `parse_report` and `load_report` with version dispatch, `compare(baseline, current)` producing a `Comparison`, `dumps_comparison`, and the `compare` command with its own exit function and the fixed statement that it compares saved data.

## Outcome

For an automation engineer upgrading a model, `compare` shows which Scenario regressed and which tool sequences changed, labeled as possible sampling variation (PRD UJ-3).

## Requirements

- R1 (parent R16): `parse_report(data, source=)` and `load_report(path)`, created in epic 6, gain dispatch on the integer version through an `upgrade_to_latest` stub, rejecting unsupported versions with exit 2 at the CLI.
- R2 (parent R16, C6): `compare` reports per-Scenario status changes, Assertion id set differences, tool-sequence differences, selected-argument differences limited to the current Report's `defaults.compare.include_arguments`, added and removed Scenarios, excludes `VOLATILE_PATHS`, reports duration and cost only when both sides have them, and sets `regressed` only on `passed` to `failed` or `error`.
- R3 (parent R16, C3): `agentproof compare BASELINE_REPORT CURRENT_REPORT [--output FILE]` prints the summary with `STATEMENTS.compare_is_saved_data`, writes the Comparison JSON when asked, and exits through `from_comparison`: 1 on regression, 0 otherwise, 2 on an invalid Report.

## Constraints

- Covered parent constraints: C3 (one exit mapping) and C6 (one volatile list); the lines below say how.
- Spine AD-6: `from_comparison` is the only exit mapping; invalid input is handled before it.
- Spine AD-11: the volatile list is shared with golden tests, never duplicated.
- PRD OQ-10 built as the spine's defaults: sequence-only changes do not fail; no arguments compared unless listed.

## Done when

- `compare report.json report.json` prints no differences and exits 0; a current Report with one Scenario regressed exits 1 naming it; one with a changed sequence but unchanged statuses exits 0 and lists the sequence change (R2, R3).
- A file that is not a Report exits 2 with one line (R1, R3).
- The summary and the Comparison JSON carry the fixed statement about saved data (R3).
- Production delivery: the CI matrix runs the compare integration tests on both platforms (R3).

## Boundaries

- No statistical comparison, no multi-run aggregation (v0.3).
- Must not change: Report schema v1.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-11, AD-15, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-25, FR-26, UJ-3

## Notes

- Decision (2026-10-22): tracer bullet is story 1, `load_report` round-tripping the run's own `report.json`.
- Decision (2026-10-22): three stories, so no refactor sweep; cleanup rides with story 3.
- Decision (2026-10-22): `parse_report` and `load_report` are owned by epic 6 story 3; story 1 here adds only version dispatch and waits on 6.3.
