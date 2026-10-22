---
id: 2
type: story
title: "Integration docs: CI without credentials and artifact visibility"
parent: epic-08-github-actions-example
covers: [R2]
after: [1]
hitl: false
risk: low
refined: true
---

# Integration docs: CI without credentials and artifact visibility

## Description

The page that makes the workflow copyable and honest about where the artifacts go.

## Requirements

1. **Walkthrough** (R2; PRD AC-32.3)
   **Given** `docs/integrations.md`
   **When** read
   **Then** it shows the workflow file, explains each step, and explains how to run with saved Traces and the Fixture Agent so CI needs no model credentials.
2. **Visibility statement** (R2; PRD AC-32.3)
   **Given** the page
   **When** read
   **Then** it contains `STATEMENTS.artifacts_visible_to_readers` verbatim, stating that uploaded artifacts are visible to anyone with read access to the repository's Actions.
3. **Doctest blocks** (R2; spine AD-17)
   **Given** the page's fenced blocks tagged `agentproof-doctest`
   **When** epic 9's docs test runs
   **Then** they execute green; until then a unit test asserts the blocks match the workflow's `run` and `report` commands textually.

## Boundaries

- No README changes (epic 9).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-08-github-actions-example/epic-08-github-actions-example.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, AC-32.3

## Notes

- Files: `docs/integrations.md`, `src/agentproof/constants.py` (`STATEMENTS.artifacts_visible_to_readers` if not already present), `tests/unit/test_docs_match_workflow.py`.
- Tests: as listed.
- Depends on: story 1. Risk: low.
- Done when: criteria 1 to 3 pass.
