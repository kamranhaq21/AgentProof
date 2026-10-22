---
id: 1
type: story
title: "Package scaffold installs and prints its version"
parent: epic-01-repository-foundation-and-ci
covers: [R1, R2]
after: []
hitl: true
risk: medium
refined: true
---

# Package scaffold installs and prints its version

## Description

The tracer bullet for the whole initiative: a real wheel that installs and answers `agentproof version`. It gives every later story a package to put code in and proves the install path the README will promise. A person records the provisional distribution name and runs the first `uv sync` (hitl).

## Requirements

1. **Layout matches the spine** (R1)
   **Given** a fresh clone
   **When** the tree is listed
   **Then** `packages/python/pyproject.toml`, `packages/python/src/agentproof/__init__.py`, and empty `__init__.py` files for `models`, `loading`, `redaction`, `assertions`, `engine`, `reports`, `compare`, `adapters`, `runner`, `io`, `cli`, `testing` exist, plus `errors.py` and `constants.py` as empty modules (spine Structural Seed).
2. **Four runtime dependencies** (R1; spine AD-16)
   **Given** `pyproject.toml`
   **When** its `dependencies` are read
   **Then** they are exactly `pydantic`, `typer`, `rich`, `pyyaml` with lower bounds at the spine's Stack versions and upper bounds on the next major, and `requires-python` is `>=3.12,<4`.
3. **Installs and prints its version** (R2; spine AD-15)
   **Given** the wheel built with `uv build`
   **When** it is installed into a fresh venv and `agentproof version` runs
   **Then** it prints the version from `pyproject.toml` read through `importlib.metadata` and exits 0; and `agentproof.__all__` contains `__version__`.
4. **Provisional name is marked** (initiative C9)
   **Given** `pyproject.toml`
   **When** the `name` field is read
   **Then** a comment beside it says the name is provisional pending OQ-1 and `docs/decisions/0000-distribution-name.md` exists as a stub naming the open decision.

## Boundaries

- No commands other than `version`; no models; no CI (story 4).
- Must not change: `AGENTS.md`, `PROJECT_SPEC.md`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, Stack, Structural Seed, AD-15, AD-16
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, NFR-7

## Notes

- Files: `packages/python/pyproject.toml`, `packages/python/uv.lock`, `packages/python/src/agentproof/**/__init__.py`, `packages/python/src/agentproof/cli/app.py` (version only), `docs/decisions/0000-distribution-name.md`.
- Tests: `tests/unit/test_version.py` (version string equals metadata); `tests/integration/test_install_smoke.py` (subprocess `agentproof version` from the installed wheel).
- Depends on: nothing. Risk: the provisional name `agentproof` collides on PyPI; publishing is gated in epic 9, not here.
- Hitl step: the maintainer records the provisional name and runs `uv sync` once to produce `uv.lock`.
- Done when: criteria 1 to 4 pass on Windows locally; story 4 later proves them on Linux CI.
