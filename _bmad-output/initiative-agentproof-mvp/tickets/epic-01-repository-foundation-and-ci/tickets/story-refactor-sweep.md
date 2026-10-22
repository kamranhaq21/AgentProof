---
id: 7
type: story
title: "Refactor sweep"
parent: epic-01-repository-foundation-and-ci
covers: [R3]
after: [1, 2, 3, 4, 5, 6]
hitl: false
risk: low
refined: true
---

# Refactor sweep

## Description

Cleanup only, scoped at start from the plans and review findings stories 1 to 6 deferred. No new behavior; scope pushed out of another story is a new story.

## Requirements

1. **Scope is written before work starts** (R3)
   **Given** the plans and review findings of stories 1 to 6
   **When** this story starts
   **Then** its plan lists each cleanup item with its source finding, and nothing else is touched.
2. **Checks stay green** (R3)
   **Given** the sweep's diff
   **When** `uv run check` and CI run
   **Then** both pass and the diff touches only the listed items.

## Boundaries

- Must not change: any behavior a test from stories 1 to 6 asserts.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements

## Notes

- Files: whatever the scope lists; none known in advance.
- Tests: the existing suite.
- Depends on: stories 1 to 6. Risk: low.
- Done when: criteria 1 and 2 pass.
