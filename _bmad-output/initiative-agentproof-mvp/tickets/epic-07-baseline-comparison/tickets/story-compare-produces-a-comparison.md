---
id: 2
type: story
title: "compare produces a Comparison"
parent: epic-07-baseline-comparison
covers: [R2]
after: [1]
hitl: false
risk: medium
refined: true
---

# compare produces a Comparison

## Description

The pure function that answers "did the latest change make it worse" over two saved Reports, with the volatile paths excluded and the argument selection taken from the current Report.

## Requirements

1. **Differences** (R2; PRD FR-26, AC-26.1, AC-26.3)
   **Given** `compare(baseline, current)`
   **When** the current Report has one Scenario changed from `passed` to `failed`, one with a different tool-call sequence, one added, and one removed
   **Then** the Comparison lists the status change, the sequence difference, the added and removed ids, and the Assertion-id set differences, and ignores every `VOLATILE_PATHS` field.
2. **Arguments** (R2; PRD AC-26.5)
   **Given** the current Report's `defaults.compare.include_arguments` listing `approve_expense.amount`
   **When** compared
   **Then** only that argument path is compared; with an empty list no arguments are compared.
3. **Regression flag** (R2; PRD AC-26.4)
   **Given** the Comparison
   **When** inspected
   **Then** `regressed` is true only when some Scenario went from `passed` to `failed` or `error`; a sequence-only change or an improvement leaves it false; comparing a Report with itself yields no differences.
4. **Duration, cost, statement** (R2; PRD AC-26.6)
   **Given** two Reports
   **When** compared
   **Then** duration and cost differences appear only when both sides carry them, and the Comparison carries `STATEMENTS.compare_is_saved_data`; `dumps_comparison` emits it in Canonical form.

## Boundaries

- No CLI (story 3). No statistics across runs (v0.3).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-07-baseline-comparison/epic-07-baseline-comparison.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-11, AD-15
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-26, AC-26.1 to AC-26.6, UJ-3

## Notes

- Files: `src/agentproof/compare/compare.py`, `src/agentproof/__init__.py` (`compare`, `dumps_comparison`).
- Tests: `tests/unit/compare/test_compare.py` with fixtures for each difference kind and the self-comparison.
- Depends on: story 1. Risk: medium; OQ-10 defaults are built as the spine states.
- Done when: criteria 1 to 4 pass.
