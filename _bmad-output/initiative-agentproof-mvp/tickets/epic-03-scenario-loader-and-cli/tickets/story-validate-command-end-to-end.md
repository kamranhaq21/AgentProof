---
id: 4
type: story
title: "validate command end to end"
parent: epic-03-scenario-loader-and-cli
covers: [R4, R3]
after: [1, 3]
hitl: false
risk: low
refined: true
---

# validate command end to end

## Description

The first command a user runs on their own file. It proves the loader, the error handler, and the exit codes together.

## Requirements

1. **Valid Suite** (R4; spine AD-20)
   **Given** `agentproof validate agentproof.yaml` on the spine's Suite seed
   **When** it runs
   **Then** it prints the Suite id, the Scenario count, and the Assertion count, and exits 0.
2. **Invalid Suite** (R3, R4; PRD AC-2.4, AC-28.1)
   **Given** each malformed fixture from stories 2 and 3
   **When** `validate` runs
   **Then** it exits 2, prints one line per violation, and prints no traceback.
3. **Missing file** (R3; PRD AC-28.1)
   **Given** a path that does not exist
   **When** `validate` runs
   **Then** it exits 2 with one line naming the path.
4. **Help** (R4; PRD AC-28.3)
   **Given** `agentproof validate --help`
   **When** it runs
   **Then** it lists the argument and the exit codes 0, 2, and 4.

## Boundaries

- Must not change: the error shape from story 1.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-03-scenario-loader-and-cli/epic-03-scenario-loader-and-cli.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-2, AC-2.4, AC-28.1, AC-28.3

## Notes

- Files: `src/agentproof/cli/commands/validate.py`.
- Tests: `tests/integration/cli/test_validate.py` (subprocess, marked `allow_subprocess`) over the fixture set.
- Depends on: stories 1 and 3. Risk: low.
- Done when: criteria 1 to 4 pass on both CI platforms.
