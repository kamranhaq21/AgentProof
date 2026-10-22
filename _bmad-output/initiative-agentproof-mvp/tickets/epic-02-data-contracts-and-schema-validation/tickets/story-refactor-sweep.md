---
id: 7
type: story
title: "Refactor sweep"
parent: epic-02-data-contracts-and-schema-validation
covers: [R5]
after: [1, 2, 3, 4, 5, 6]
hitl: false
risk: low
refined: true
---

# Refactor sweep

## Description

Cleanup only, scoped at start from the plans and review findings stories 1 to 6 deferred. No new behavior; scope pushed out of another story is a new story.

## Requirements

1. **Scope is written before work starts** (R5)
   **Given** the plans and review findings of stories 1 to 6
   **When** this story starts
   **Then** its plan lists each cleanup item with its source finding, and nothing else is touched.
2. **Checks and schemas stay green** (R5)
   **Given** the sweep's diff
   **When** `uv run check` runs
   **Then** it passes, the drift test passes, and the diff touches only the listed items.

## Boundaries

- Must not change: any serialized model field; that is a schema bump, not a sweep.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements

## Notes

- Files: whatever the scope lists.
- Tests: the existing suite.
- Depends on: stories 1 to 6. Risk: low.
- Done when: criteria 1 and 2 pass.
