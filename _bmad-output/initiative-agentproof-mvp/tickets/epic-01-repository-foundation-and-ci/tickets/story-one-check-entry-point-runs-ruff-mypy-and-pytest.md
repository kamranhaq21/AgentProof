---
id: 2
type: story
title: "One check entry point runs ruff, mypy, and pytest"
parent: epic-01-repository-foundation-and-ci
covers: [R3]
after: [1]
hitl: false
risk: low
refined: true
---

# One check entry point runs ruff, mypy, and pytest

## Description

One command decides whether a change is acceptable, locally and in CI, so no story after this debates tooling. The order and the stop-on-first-failure behavior are the contract CI mirrors (spine AD-17).

## Requirements

1. **Ordered steps** (R3; spine AD-17)
   **Given** `uv run check`
   **When** it runs on the scaffold
   **Then** it executes `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, `pytest` in that order, prints each step's name, and exits 0.
2. **Stops at the first failure** (R3)
   **Given** an unused import, a type error, or a failing test introduced on a branch
   **When** `uv run check` runs
   **Then** it exits non-zero at the step that found it and does not run later steps.
3. **mypy configuration** (R3; initiative ARCH-1)
   **Given** `pyproject.toml`
   **When** the mypy section is read
   **Then** `strict = true` and the pydantic plugin are enabled and the package's `src` is the only target.
4. **Lint-imports step is a placeholder until story 3** (R3)
   **Given** no `.importlinter` file yet
   **When** `uv run check` reaches `lint-imports`
   **Then** it reports the step as skipped with a reason rather than failing.

## Boundaries

- Must not change: the package layout from story 1.
- The task runner choice (ARCH-4) is open; a `scripts/check.py` entry registered under `[project.scripts]` is the assumed form.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, Conventions (Typing)

## Notes

- Files: `packages/python/pyproject.toml` (ruff, mypy, pytest sections, `[project.scripts] check`), `packages/python/scripts/check.py`.
- Tests: `tests/unit/test_check_entry_point.py` running the script with injected failing steps.
- Depends on: story 1. Risk: low.
- Done when: criteria 1 to 4 pass and the command is documented in CONTRIBUTING by story 5.
