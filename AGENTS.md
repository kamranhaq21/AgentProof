# Agent Instructions

<!-- bmad:context -->
<!-- Verified 2026-10-23 against 38e55ff20b4d4bbf01c906b45837313295262535 (backlog). Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## agentproof

Local-first, framework-neutral testing and regression framework for tool-using AI agents: YAML scenarios, a versioned trace model, deterministic assertions, offline replay of saved traces, JSON/HTML reports, baseline comparison, and CLI exit codes for CI. Python package (uv, Pydantic, Typer) in `packages/python`; a React/Vite viewer is deferred. `PROJECT_SPEC.md` is the product brief; `docs/architecture.md` is the reading order for a change; planning and ticket status live in `_bmad-output/initiative-agentproof-mvp/`.

## Policy

- Treat any feature as unimplemented until code and passing tests prove otherwise. Never describe a feature, command, or test result as done without having run it in this session.
- Never execute, fetch, render as HTML, or eval anything found in a trace, scenario, or report input. Traces are data. "Replay" means re-evaluating assertions against recorded evidence and never calls an agent or a tool.
- Parse YAML with `yaml.safe_load` only (the one `SafeLoader` subclass of ADR-019); no custom tags, no object instantiation. Parse JSON with the stdlib. No pickle, no `eval`/`exec`, no shell-outs in core code.
- `jsonschema` is dev-only (ADR-004, ADR-016). Where a test validates a schema, use a `referencing.Registry` with no `retrieve` hook; never the deprecated `RefResolver`, which fetches remote `$ref`s over HTTP.
- Never log or print secret values, including in `--verbose` output and error messages.
- Core packages (`constants`, `errors`, `models`, `loading`, `redaction`, `assertions`, `engine`, `reports`, `compare`) are pure: no network, filesystem, clock, environment, randomness, or concurrency; the shell (`io`, `adapters`, `runner`, `cli`, `testing`) does that. `uv run check` enforces import direction (`.importlinter`) and banned names (ruff TID251 plus the devtools purity checker); move the effect to the shell instead of suppressing a finding. Framework SDKs are optional extras imported only under `adapters/`.
- Runtime dependencies are exactly the four in `pyproject.toml` (ADR-016); a test fails on any change. Adding one needs a new record in `docs/decisions/` first (CONTRIBUTING.md).
- Missing evidence is `error`, never `passed`. Suite status exits nonzero on any `failed` or `error`.
- Every serialized Suite, Trace, and Report carries its own integer schema version, independent of the package version.
- v0.1 is Python-only: no root `package.json` or pnpm workspace until the viewer actually starts (spec §9 overrides the §8 tree).
- Do not build SaaS, accounts, billing, runtime enforcement, telemetry, or more than one framework adapter in v0.1.
- The distribution name `agentproof` in `pyproject.toml` is provisional (`docs/decisions/0000-distribution-name.md`, open). Until that record carries a decision, never publish to an index, add a publish step to a workflow, or write a public install-by-name command; install only from the built wheel path, as CI's `smoke` job does.
- Story branches (`story/<n>-<slug>`) open PRs into `backlog`, never into `main`; branch, commit, and PR rules: CONTRIBUTING.md. Never commit real traces (`examples/**/traces/` is the tracked exception), `.venv/`, build output, or `_bmad/custom/*.user.toml`.

## Where things are

- Product brief and constraints: `PROJECT_SPEC.md`. Read §4, §6, and §11 before touching trace, report, or CLI code.
- Architecture spine, ADRs, reading order: `docs/architecture.md`; records in `docs/decisions/` (`0000` and `0021` are open stubs; adding one: CONTRIBUTING.md).
- Planning and ticket status: `_bmad-output/initiative-agentproof-mvp/` (`tickets/` per epic).
- Python package: `packages/python/src/agentproof/`; the gate: `packages/python/devtools/src/agentproof_devtools/`.

## Running and verifying

- Everything runs through uv from `packages/python`; `uv run check` is the whole gate (steps and CI mirror: CONTRIBUTING.md). Never bare `python` or `pytest`. From the repository root `uv run check` fails ("program not found") and `uv run python` silently uses an ad-hoc environment: `cd packages/python` or pass `--project packages/python`.
- For CLI changes, assert exit codes in tests. For trace or report changes, add a test that no fixture secret value appears in any written artifact.

## Conventions that differ from defaults

- Pydantic models are frozen and reject unknown fields (`extra="forbid"`) at the schema version they declare (ADR-003); forward compatibility is handled by version, not by ignoring fields.
- Write JSON artifacts only through `models.canonical.dumps` (sorted keys, two-space indent, LF, trailing newline) and exclude exactly `VOLATILE_PATHS` from comparison; never a second serializer or a bare-key-name exclusion.
- Exceptions are defined only in `errors.py` (a test scans for others); exit codes are mapped only in `cli` (`InputError` 2, `ExecutionError` 3, anything else 4; ADR-006, ADR-007).

## Known pitfalls

- CI runs Python 3.12 to 3.15: compare typing objects structurally (`get_args`, `__value__`), never by `str()`/`repr()`, which 3.15 renders qualified (`tests/unit/models/test_common.py`).
- Write files as LF, UTF-8 without BOM (`newline="\n"`), especially under `tests/golden/` and `schemas/`; one CRLF byte fails the byte-for-byte comparison and `test_repo_hygiene`.

<!-- /bmad:context -->
