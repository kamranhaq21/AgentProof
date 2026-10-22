---
id: 5
type: story
title: "Refactor sweep"
parent: epic-06-json-and-html-reports
covers: [R1]
after: [1, 2, 3, 4]
hitl: false
risk: low
refined: true
---

# Refactor sweep

## Description

Cleanup only, scoped at start from the plans and review findings stories 1 to 4 deferred. No new behavior; scope pushed out of another story is a new story.

## Requirements

1. **Scope is written before work starts** (R1)
   **Given** the plans and review findings of stories 1 to 4
   **When** this story starts
   **Then** its plan lists each cleanup item with its source finding, and nothing else is touched.
2. **Checks stay green** (R1)
   **Given** the sweep's diff
   **When** `uv run check` runs
   **Then** it passes, the goldens pass, and the diff touches only the listed items.

## Boundaries

- Must not change: Report schema, Canonical form, or the HTML escaping rules.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-06-json-and-html-reports/epic-06-json-and-html-reports.md, section Requirements

## Notes

- Files: whatever the scope lists.
- Tests: the existing suite.
- Depends on: stories 1 to 4. Risk: low.
- Done when: criteria 1 and 2 pass.
