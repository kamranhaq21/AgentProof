# Agent Instructions

<!-- bmad:context -->
<!-- Verified 2026-10-22 against an unborn `main` (no commits yet; only PROJECT_SPEC.md is staged). Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## agentproof

Local-first, framework-neutral testing and regression framework for tool-using AI agents: YAML scenarios, a versioned trace model, deterministic assertions, offline replay of saved traces, JSON/HTML reports, baseline comparison, and CLI exit codes for CI. Python package first (uv, Pydantic, Typer); a React/Vite viewer is optional and deferred. Nothing is implemented yet. `PROJECT_SPEC.md` is the product brief and constraints; BMAD planning artifacts live in `_bmad-output/initiative-agentproof-mvp/`.

## Policy

- Treat the product as unimplemented until code and passing tests prove otherwise. Never describe a feature, command, or test result as done without having run it in this session.
- Never execute, fetch, render as HTML, or eval anything found in a trace, scenario, or report input. Traces are data. "Replay" means re-evaluating assertions against recorded evidence and never calls an agent or a tool.
- Parse YAML with `yaml.safe_load` only; no custom tags, no object instantiation. Parse JSON with the stdlib. No pickle, no `eval`/`exec`, no shell-outs in core code.
- Validate user-supplied JSON Schemas with a `referencing.Registry` that has no `retrieve` hook; never use the deprecated `RefResolver`, which fetches remote `$ref`s over HTTP.
- Never log or print secret values, including in `--verbose` output and error messages.
- Core evaluation makes no network calls. Framework SDKs are optional extras under `adapters/`; `models`, `assertions`, `traces`, `reports`, and `compare` never import one.
- Keep runtime dependencies to what `PROJECT_SPEC.md` §9 names; adding one needs a stated reason in the PR.
- Missing evidence is `error`, never `passed`. Suite status exits nonzero on any `failed` or `error`.
- Every serialized scenario, trace, and report carries its own schema version, independent of the package version.
- v0.1 is Python-only: no root `package.json` or pnpm workspace until the viewer actually starts (spec §9 overrides the §8 tree).
- Do not build SaaS, accounts, billing, runtime enforcement, telemetry, or more than one framework adapter in v0.1.
- The PyPI name `agentproof` is taken by another agent-testing package; do not write install commands or a distribution name until the name decision is recorded in `docs/decisions/`.
- Work on short-lived branches and open a PR even when solo; `main` stays releasable. Never commit real traces, `.venv/`, build output, or `_bmad/custom/*.user.toml`.

## Where things are

- Product brief and constraints: `PROJECT_SPEC.md`. Read §4, §6, and §11 before touching trace, report, or CLI code.
- Planning artifacts (initiative, architecture, epics, stories, assessments): `_bmad-output/initiative-agentproof-mvp/`.
- Decision records: `docs/decisions/`. TODO: create with the first recorded decision.
- Python package: `packages/python/src/agentproof/`. TODO: created by EPIC A.

## Running and verifying

- TODO (EPIC A): once `pyproject.toml` exists, run everything through uv: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and the chosen type checker. Never bare `pytest` or `python`; `uv run` selects the interpreter from `requires-python`, and the `python` on PATH may be a different version.
- TODO (EPIC A): CI runs the same commands as local; define them once and have CI call that.
- For CLI changes, assert exit codes in tests. For trace or report changes, add a test that no fixture secret value appears in any written artifact.

## Conventions that differ from defaults

- Pydantic models reject unknown fields (`extra="forbid"`) at the schema version they declare; forward compatibility is handled by version, not by ignoring fields.
- Assertion evaluation is pure: trace and config in, result out. No I/O, no clock, no randomness inside an assertion.
- JSON artifacts are written with sorted keys and a fixed indent so baselines diff cleanly; volatile fields (run id, timestamps, durations) are excluded from comparison by default.

<!-- /bmad:context -->
