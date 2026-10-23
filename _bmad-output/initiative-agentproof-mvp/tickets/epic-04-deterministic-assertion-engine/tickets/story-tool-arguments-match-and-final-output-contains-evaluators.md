---
id: 5
type: story
title: "tool_arguments_match and final_output_contains evaluators"
parent: epic-04-deterministic-assertion-engine
covers: [R3]
after: [3, 4]
hitl: false
risk: medium
refined: true
---

# tool_arguments_match and final_output_contains evaluators

## Description

The last two built-ins: argument matching by dotted path and JSON value, and the only output Assertion in v0.1, matching structured output against the compact Canonical form so users can copy a snippet from the Report.

## Requirements

1. **Dotted paths and value matching** (R3; PRD AC-14.1, AC-14.2; spine Conventions Argument paths)
   **Given** a `tool_call` to `approve_expense` with arguments `{"items": [{"amount": 5000}], "currency": "USD"}`
   **When** `tool_arguments_match` with `arguments: {items.0.amount: 5000, currency: USD}` is evaluated
   **Then** it passes with that seq as Evidence; `items.0.amount: 5000.0` passes (numeric equality); `items.0.amount: "5000"` fails (number never matches string); nested objects match by deep equality.
2. **Absent path and never called** (R3; PRD AC-14.3, AC-14.4)
   **Given** the same Trace
   **When** evaluated with `items.3.amount: 1`
   **Then** it fails naming the absent path; and with `tool: never_called` it errors with a message distinguishing "tool never called" from "called with different arguments".
3. **final_output_contains** (R3; PRD AC-16.1 to AC-16.3; spine AD-11)
   **Given** an `agent_finished` event with `output: "Expense rejected: over limit"`
   **When** evaluated with `value: rejected`
   **Then** it passes; `value: REJECTED` fails unless `case_sensitive: false`; with structured output `{"status": "rejected", "amount": 5000}` and `value: '"status":"rejected"'` it passes against the compact form and `value: '"status": "rejected"'` fails; with no `agent_finished` event it errors.
4. **Registry complete** (R3; spine AD-8)
   **Given** `EVALUATORS`
   **When** the key-set test runs
   **Then** all six types are present and equal the union's literals.

## Boundaries

- No wildcards or JSONPath (OQ-7).
- No regex or JSON Schema Assertions (v0.2).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-14, FR-16, AC-14.x, AC-16.x
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-8, AD-11, Conventions

## Notes

- Files: `src/agentproof/assertions/builtin/tool_arguments_match.py`, `src/agentproof/assertions/builtin/final_output_contains.py`, registry update.
- Tests: `tests/unit/assertions/test_tool_arguments_match.py`, `tests/unit/assertions/test_final_output_contains.py`.
- Depends on: stories 3 and 4 (both edit `assertions/registry.py`, so they are serialized). Risk: medium; the compact-form decision (OQ-9) differs from the PRD's wording and is recorded as an upstream conflict in the ADR log.
- Done when: criteria 1 to 4 pass.
