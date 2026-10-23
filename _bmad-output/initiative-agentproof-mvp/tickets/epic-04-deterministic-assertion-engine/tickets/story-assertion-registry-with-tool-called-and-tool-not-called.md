---
id: 3
type: story
title: "Assertion registry with tool_called and tool_not_called"
parent: epic-04-deterministic-assertion-engine
covers: [R3]
after: [1]
hitl: false
risk: medium
refined: true
---

# Assertion registry with tool_called and tool_not_called

## Description

The first two real Assertions and the registry that binds a config type to its evaluator. `tool_not_called` is the product's compliance promise, so its message must say what the Adapter could observe.

## Requirements

1. **Registry** (R3; spine AD-8)
   **Given** `assertions.registry.EVALUATORS`
   **When** `agentproof.assertions.builtin` is imported
   **Then** it maps each type name to a pure evaluator `(config, trace) -> AssertionResult`, and a test asserts its key set equals the `type` literals of the `models.assertions` union (two in this story, six by story 5, with the test updated per story).
2. **tool_called** (R3; PRD AC-11.1 to AC-11.3)
   **Given** a Trace with `tool_call` events for `reject_expense` at seq 1 and 3
   **When** `tool_called` with `tool: reject_expense` is evaluated
   **Then** it passes with Evidence `[1, 3]`; with no matching call it fails with a message naming the tool and the distinct tools called; on an empty Trace it errors.
3. **tool_not_called** (R3; PRD AC-12.1 to AC-12.4)
   **Given** the same Trace
   **When** `tool_not_called` with `tool: reject_expense` is evaluated
   **Then** it fails with Evidence `[1, 3]`; with no matching call it passes; on an empty Trace it errors; and every message ends with the Capture declaration, for example `(capture: complete)` or `(capture: unknown; absence is limited to what the Adapter observed)`.
4. **Assertion id and purity** (R3; spine AD-1; PRD AC-17.2, AC-17.4)
   **Given** any result from this story
   **When** inspected
   **Then** `assertion_id` equals the config's id and evaluating twice yields equal results.

## Boundaries

- Must not change: the config models.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-1, AD-8
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-10 to FR-12, AC-11.x, AC-12.x

## Notes

- Files: `src/agentproof/assertions/builtin/__init__.py`, `src/agentproof/assertions/builtin/tool_called.py`, `src/agentproof/assertions/builtin/tool_not_called.py`, `src/agentproof/assertions/registry.py`.
- Tests: `tests/unit/assertions/test_registry.py`, `tests/unit/assertions/test_tool_called.py`, `tests/unit/assertions/test_tool_not_called.py` (pass, fail, invalid configuration, missing evidence each).
- Depends on: story 1. Risk: medium.
- Done when: criteria 1 to 4 pass.
