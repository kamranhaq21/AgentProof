---
id: 3
type: story
title: "Import contracts encode the dependency direction"
parent: epic-01-repository-foundation-and-ci
covers: [R4]
after: [2]
hitl: false
risk: medium
refined: true
---

# Import contracts encode the dependency direction

## Description

The spine's dependency direction and pure-core rule become tool-checked before any real module exists, so later stories cannot drift. This is the single most important guard for the determinism promise (spine AD-1, AD-2).

## Requirements

1. **Layer contract** (R4; spine AD-2)
   **Given** `.importlinter` at the repository root
   **When** `lint-imports` runs
   **Then** a `layers` contract lists, top to bottom, `cli`, `runner`, `reports | compare`, `engine`, `loading | redaction | assertions`, `models`, `constants`, `errors`, and passes on the empty packages.
2. **Forbidden contracts** (R4; spine AD-2)
   **Given** the same file
   **When** it is read
   **Then** `forbidden` contracts allow `io` to import only `errors`, `constants`, `redaction`; `adapters` only `errors`, `constants`, `models`, `loading`, `io`; `testing` only `models`, `loading`, `adapters`, `errors`; `cli` only `runner`, `io`, and the package's top level; and nothing imports `cli`.
3. **Banned stdlib names in the core** (R4; spine AD-1)
   **Given** ruff's `flake8-tidy-imports` banned-API configuration scoped to the core packages
   **When** a core module uses `open`, `os.environ`, `time`, `datetime.now`, `uuid`, `random`, `socket`, `subprocess`, `threading`, `asyncio`, or a `pathlib.Path` I/O method
   **Then** `ruff check` reports it.
4. **Contracts bite** (R4)
   **Given** a test that writes `import agentproof.cli` into `agentproof/models/__init__.py` and `open("x")` into `agentproof/engine/__init__.py` in a temporary copy
   **When** `lint-imports` and `ruff check` run on the copy
   **Then** both fail naming the offending module.

## Boundaries

- Must not change: the check entry point's order from story 2; this story only removes the placeholder for `lint-imports`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-1, AD-2
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-001, ADR-002

## Notes

- Files: `.importlinter`, `packages/python/pyproject.toml` (ruff `banned-api` and per-file scoping), `packages/python/scripts/check.py`.
- Tests: `tests/unit/test_import_contracts.py` (negative tests on a temporary copy).
- Depends on: story 2. Risk: a banned-API rule that is too broad blocks legitimate shell code; scope it to core packages only.
- Done when: criteria 1 to 4 pass and `uv run check` runs `lint-imports` for real.
