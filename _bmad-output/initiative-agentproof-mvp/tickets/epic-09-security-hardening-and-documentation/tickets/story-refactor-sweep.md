---
id: 7
type: story
title: "Refactor sweep"
parent: epic-09-security-hardening-and-documentation
covers: [R1]
after: [1, 2, 3, 4, 5]
hitl: false
risk: low
refined: true
---

# Refactor sweep

## Description

Cleanup only, scoped at start from the plans and review findings stories 1 to 5 deferred. No new behavior; scope pushed out of another story is a new story. Runs before the tester story only if it finishes first; it never blocks the release.

## Requirements

1. **Scope is written before work starts** (R1)
   **Given** the plans and review findings of stories 1 to 5
   **When** this story starts
   **Then** its plan lists each cleanup item with its source finding, and nothing else is touched.
2. **Checks stay green** (R1)
   **Given** the sweep's diff
   **When** `uv run check` and the docs test run
   **Then** both pass and the diff touches only the listed items.

## Boundaries

- Must not change: published behavior; anything user-visible after 0.1.0 is a patch release with notes.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements

## Notes

- Files: whatever the scope lists.
- Tests: the existing suite.
- Depends on: stories 1 to 5. Risk: low.
- Done when: criteria 1 and 2 pass.
