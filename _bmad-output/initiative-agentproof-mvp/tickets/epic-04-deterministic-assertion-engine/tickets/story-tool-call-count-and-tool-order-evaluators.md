---
id: 4
type: story
title: "tool_call_count and tool_order evaluators"
parent: epic-04-deterministic-assertion-engine
covers: [R3]
after: [3]
hitl: false
risk: medium
refined: true
---

# tool_call_count and tool_order evaluators

## Description

Two Assertions with defined edge semantics the reviews fought over: the count operators and first-occurrence ordering. The PRD's documented counter-example is the fixture.

## Requirements

1. **tool_call_count** (R3; PRD AC-13.1 to AC-13.3)
   **Given** a Trace with two `tool_call` events for `reject_expense`
   **When** evaluated with `equals: 2`, `greater_than: 1`, `less_than: 3`
   **Then** each passes, and `equals: 1`, `greater_than: 2`, `less_than: 2` each fail with Evidence of the matching seqs; an empty Trace errors; a `less_than` message states the Capture declaration.
2. **tool_order first occurrences** (R3; PRD AC-15.1, AC-15.4)
   **Given** the Trace `[delete_file, confirm_with_user, delete_file]`
   **When** `tool_order` with `tools: [confirm_with_user, delete_file]` is evaluated
   **Then** it fails naming `delete_file` as out of order with Evidence for both first occurrences; and `[confirm_with_user, delete_file, confirm_with_user, delete_file]` passes.
3. **Intervening events and absence** (R3; PRD AC-15.2, AC-15.3)
   **Given** `[a, x, b, y, c]`
   **When** `tool_order` with `tools: [a, b, c]` is evaluated
   **Then** it passes; and when `c` is never called it errors naming `c`.
4. **Purity and ids** (R3; PRD AC-17.2, AC-17.4)
   **Given** any result
   **When** evaluated twice
   **Then** results are equal and carry the config's id.

## Boundaries

- No `strict` adjacency option (OQ-8 deferred).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-13, FR-15, AC-13.x, AC-15.x
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-8

## Notes

- Files: `src/agentproof/assertions/builtin/tool_call_count.py`, `src/agentproof/assertions/builtin/tool_order.py`, registry update.
- Tests: `tests/unit/assertions/test_tool_call_count.py`, `tests/unit/assertions/test_tool_order.py` with the PRD counter-example as a named fixture.
- Depends on: story 3. Risk: medium.
- Done when: criteria 1 to 4 pass.
