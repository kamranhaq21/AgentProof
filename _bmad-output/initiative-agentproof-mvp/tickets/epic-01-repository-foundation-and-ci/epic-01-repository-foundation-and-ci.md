---
type: epic
title: "Repository foundation and CI: the package installs from a built wheel and one check entry point runs locally and in CI on Linux and Windows"
parent: initiative-agentproof-mvp
covers: ["R27", "R28", "R29", "C1", "C7", "C9", "C10"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: medium
---

# Repository foundation and CI

## Description

The platform baseline every other epic builds on: the `src` layout under `packages/python`, `pyproject.toml` as the single version source, the uv lockfile, ruff, mypy, import-linter contracts that encode the spine's dependency direction before any real module exists, one `check` entry point, a CI matrix on Linux and Windows across Python 3.12 to 3.15, wheel build with a clean-install smoke test, and the repository hygiene files. When done, a contributor clones, runs one command, and gets the same verdict CI gives.

## Outcome

For the maintainer and every build agent, a change is accepted or rejected by one command that CI mirrors, so no later epic debates tooling (initiative Done when: clean install on Linux and Windows CI).

## Requirements

- R1 (parent R27): The package builds as a wheel and installs into a clean virtual environment on Linux and Windows for Python 3.12, 3.13, 3.14, and 3.15, with exactly `pydantic`, `typer`, `rich`, and `pyyaml` as runtime dependencies.
- R2 (parent R28): `pyproject.toml` is the only place the package version is written; `agentproof version` prints it via `importlib.metadata`; the 0.x pre-1.0 policy is stated in CONTRIBUTING.
- R3 (parent R29, C7): One entry point runs, in order, `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, and `pytest`, and CI calls that entry point and nothing else for the check stage.
- R4 (parent C1): An `.importlinter` file carries the layer contract and the forbidden contracts exactly as spine AD-2 lists them, and ruff's banned-API list covers the stdlib names AD-1 forbids in the core; both pass on the scaffold's empty subpackages.
- R5 (parent C7, C10): CI pins every action by commit SHA, declares `permissions: contents: read` by default, builds the wheel, installs it into a fresh venv, runs `agentproof version`, and runs `pip-audit`; `.gitattributes` forces LF on `tests/golden/**`; `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml`, CONTRIBUTING, SECURITY, and CODE_OF_CONDUCT exist.
- R6 (parent C9): The ADRs move to `docs/decisions/` and the name (OQ-1) and license (OQ-2) decisions are recorded there when the maintainer makes them; until then the distribution name is marked provisional and no LICENSE file is committed.

## Constraints

- C1, C7, C9, C10 from the initiative bind here in full; this epic is where they become files.
- Spine AD-15: `agentproof.__all__` exists from the first story, even if it exports only `__version__`.
- Spine AD-17: the check entry point's tool is open (ARCH-4); any single entry point satisfies it.

## Done when

- `uv run check` passes on a fresh clone on Windows and on Linux CI with an empty-but-structured package (R3, R4).
- CI is green on the full matrix and the wheel installed into a clean venv prints its version (R1, R2, R5).
- `lint-imports` fails when a test commit adds `import agentproof.cli` inside `agentproof.models` (R4).
- The repository has every hygiene file in R5 and `docs/decisions/` holds ADR-001 to ADR-020 (R5, R6).
- Production delivery: a tagged pre-release wheel builds in CI and is attached to the GitHub release draft without publishing to PyPI (R1, C9).

## Boundaries

- No product behavior: `agentproof version` is the only runnable command; `validate` and the rest belong to epic 3.
- No release to PyPI; the release workflow with trusted publishing is epic 9.
- Must not change: `AGENTS.md` and `PROJECT_SPEC.md` are only pointed at, never rewritten.
- Touch point: GitHub repository settings (branch protection, Actions permissions); owner: this epic, as a hitl step in the CI story.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-1, AD-2, AD-15, AD-16, AD-17, Stack, Structural Seed
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-001, ADR-002, ADR-016, ADR-017
- spec — PROJECT_SPEC.md, sections 8, 9, 13

## Notes

- Decision (2026-10-22): tracer bullet is story 1, the scaffold with `agentproof version` installed from a locally built wheel; a person records the provisional name and runs the first `uv sync`.
- Decision (2026-10-22): the distribution name in `pyproject.toml` is provisional (`agentproof`, which is taken on PyPI) so epics 2 to 8 are not blocked; epic 9's release story carries the `unknown` that gates publishing on OQ-1.
- Assumption: mypy with the pydantic plugin (ARCH-1); switching to pyright changes story 2 only.
- Assumption: the check entry point is a `scripts/check.py` invoked as `uv run check` through a `[project.scripts]` entry (ARCH-4).
- Open question: OQ-2 license; story 5 commits every hygiene file except LICENSE until the maintainer decides.
