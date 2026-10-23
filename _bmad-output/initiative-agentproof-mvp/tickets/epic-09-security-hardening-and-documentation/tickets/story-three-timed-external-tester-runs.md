---
id: 6
type: story
title: "Three timed external tester runs"
parent: epic-09-security-hardening-and-documentation
covers: [R6]
after: [5]
hitl: true
risk: medium
refined: true
---

# Three timed external tester runs

## Description

The PRD's first success metric measured, not assumed: three developers who have never seen the repository follow the README from install to a passing and a failing run while someone times them and notes every point of friction.

## Requirements

1. **Protocol** (R6; PRD SM-1, OQ-14)
   **Given** `docs/decisions/tester-protocol.md`
   **When** read
   **Then** it fixes the start (a fresh machine or container with Python only), the end (the failing run's exit code observed), what counts as help (none), and how time is recorded.
2. **Three runs** (R6; PRD AC-33.2)
   **Given** three external testers
   **When** each follows the README
   **Then** `docs/decisions/tester-runs.md` records each run's date, environment, time to the passing run, time to the failing run, and friction notes.
3. **Outcome** (R6)
   **Given** the three times
   **When** any exceeds five minutes
   **Then** the friction becomes a bug or story ticket in the backlog with the tester's note as its description, and the record says which.

## Boundaries

- No product changes in this story; findings become tickets.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, SM-1, AC-33.2, OQ-14
- spec — PROJECT_SPEC.md, section 14.1

## Notes

- Files: `docs/decisions/tester-protocol.md`, `docs/decisions/tester-runs.md`, backlog tickets as found.
- Tests: none; the record is the verification.
- Depends on: story 5 (the published package). Risk: medium.
- Hitl step: recruiting and timing the testers.
- Done when: criteria 1 to 3 are met.
