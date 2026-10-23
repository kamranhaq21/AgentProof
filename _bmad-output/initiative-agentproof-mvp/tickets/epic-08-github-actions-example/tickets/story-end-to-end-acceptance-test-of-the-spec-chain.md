---
id: 3
type: story
title: "End-to-end acceptance test of the spec chain"
parent: epic-08-github-actions-example
covers: [R3]
after: [1, "7.3"]
hitl: false
risk: medium
refined: true
---

# End-to-end acceptance test of the spec chain

## Description

One test that walks the whole product the way a new user would, from a clean install to a comparison, and checks every artifact for a planted secret.

## Requirements

1. **Chain** (R3; spec §12.4; PRD NFR-9)
   **Given** `tests/e2e/test_acceptance.py` and the wheel built in the same CI run
   **When** it runs
   **Then** it creates a clean venv, installs the wheel, runs `agentproof init` in a temp directory, runs the Suite and asserts exit 1 with one failed Scenario, edits the Suite to make both pass and asserts exit 0, generates the HTML Report, replays the exported failing Trace with the environment cleared and asserts the same result, compares the passing run against the failing Baseline and asserts `regressed` false and exit 0, then the reverse and asserts exit 1, and greps every file in both Output Directories for the planted secret value.
2. **Platforms** (R3; PRD NFR-6)
   **Given** the CI matrix
   **When** the test runs
   **Then** it passes on Linux and Windows.
3. **Breaks when broken** (R3)
   **Given** any one step disabled in a temporary copy
   **When** the test runs
   **Then** it fails naming the step.

## Boundaries

- Must not change: product behavior; a failure is a bug ticket against the owning story.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-08-github-actions-example/epic-08-github-actions-example.md, section Requirements
- spec — PROJECT_SPEC.md, section 12.4
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, NFR-9

## Notes

- Files: `tests/e2e/test_acceptance.py`, `.github/workflows/ci.yml` (e2e job after the wheel job).
- Tests: as listed, marked `allow_subprocess` and `e2e`.
- Depends on: story 1 and 7.3. Risk: medium; slow, so it runs once per platform, not per Python version.
- Done when: criteria 1 to 3 pass.
