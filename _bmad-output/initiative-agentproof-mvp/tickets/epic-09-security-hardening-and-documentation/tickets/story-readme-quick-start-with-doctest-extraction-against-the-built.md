---
id: 1
type: story
title: "README quick start with doctest extraction against the built wheel"
parent: epic-09-security-hardening-and-documentation
covers: [R1, R2]
after: ["8.3"]
hitl: false
risk: medium
refined: true
---

# README quick start with doctest extraction against the built wheel

## Description

The tracer bullet of launch readiness: the README a stranger follows, and the mechanism that keeps every command in it executable in CI against the wheel built in the same run, never against PyPI by name.

## Requirements

1. **Quick start** (R1; PRD FR-33, AC-33.3)
   **Given** `README.md`
   **When** read
   **Then** it has the opening from spec §14.4 (adjusted for the decided name once OQ-1 is settled, provisional until then), an install step, `agentproof init`, `agentproof run` showing the failing Scenario, `agentproof report --format html`, `agentproof trace replay`, and `agentproof compare`, and a Limits section containing `STATEMENTS.limits_v01` verbatim (no reproducibility of stochastic runs, no runtime enforcement, key- and declared-value-based Redaction).
2. **Doctest extraction** (R2; spine AD-17; PRD AC-33.1)
   **Given** `tests/e2e/test_docs.py`
   **When** it runs in CI
   **Then** it extracts every fenced block tagged `agentproof-doctest` from `README.md` and `docs/**/*.md`, executes them in order in a temp directory against the wheel built in the same run, and fails naming the file and block on a non-zero exit.
3. **Never PyPI by name** (R2; PRD AC-33.1, H7)
   **Given** the docs test
   **When** inspected
   **Then** the install block it executes is rewritten to install the local wheel path, and a test asserts no `pip install agentproof` by name is executed in CI.
4. **Breaks when broken** (R2)
   **Given** a README command changed to a non-existent flag
   **When** the docs test runs
   **Then** it fails.

## Boundaries

- No reference pages (story 2).
- No install command naming a PyPI package until OQ-1 is recorded (initiative C9).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-33, AC-33.1, AC-33.3, SM-1, SM-C3
- spec — PROJECT_SPEC.md, section 14.4

## Notes

- Files: `README.md`, `tests/e2e/test_docs.py`, `tests/helpers/doctest_extract.py`, `.github/workflows/ci.yml` (docs job).
- Tests: as listed.
- Depends on: 8.3. Risk: medium.
- Done when: criteria 1 to 4 pass on both CI platforms.
