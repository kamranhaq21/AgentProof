---
id: 1
type: story
title: "Example workflow runs the Suite and uploads Reports on success and failure"
parent: epic-08-github-actions-example
covers: [R1]
after: ["1.6", "6.3"]
hitl: false
risk: medium
refined: true
---

# Example workflow runs the Suite and uploads Reports on success and failure

## Description

The tracer bullet of the epic and the launch demo's backbone: the workflow a user copies, proven in this repository's own CI against the scaffolded example.

## Requirements

1. **Six steps** (R1; PRD FR-32; spec §6.8)
   **Given** `.github/workflows/agentproof-example.yml`
   **When** read
   **Then** it checks out, sets up a supported Python, installs AgentProof from the wheel artifact built in the same run (in this repository) with a commented line showing the `pip install <name>` form for users, runs `agentproof run examples/expense-agent/agentproof.yaml --output agentproof-output`, runs `agentproof report agentproof-output/report.json --format html`, uploads `agentproof-output/` with `if: always()`, and fails the job on a non-zero `run` exit.
2. **Pinned and least privilege** (R1; spine AD-17; PRD AC-32.2)
   **Given** the workflow
   **When** read
   **Then** every action is SHA-pinned and `permissions` is `contents: read`.
3. **Red on regression** (R1; PRD AC-32.1, UJ-1)
   **Given** a test branch that edits the example Suite so `approve-under-limit` fails
   **When** CI runs
   **Then** the example job is red and its artifact contains `report.json`, `report.html`, and both Trace files.
4. **No secrets** (R1; PRD AC-32.3)
   **Given** the workflow
   **When** read
   **Then** it references no secret and sets no provider environment variable.

## Boundaries

- No release logic; no changes to the project's check stage.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-08-github-actions-example/epic-08-github-actions-example.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, Deployment and environments
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-32, AC-32.1 to AC-32.3, UJ-1, SM-2
- spec — PROJECT_SPEC.md, section 6.8

## Notes

- Files: `.github/workflows/agentproof-example.yml`, `tests/unit/test_workflow_pins.py` (extended to cover it).
- Tests: the workflow on a PR and on the deliberately failing test branch; the pin test.
- Depends on: 1.6 (wheel artifact) and 6.3 (report command). Risk: medium.
- Done when: criteria 1 to 4 pass and the failing-branch run is linked from the epic's Notes.
