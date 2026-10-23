---
title: 'Refactor sweep'
type: 'feature'
ticket: '7'
created: '2026-10-23'
status: done
baseline_revision: '05ed167eb483c088cb22a7f48c4bf75e750d4d57'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'none'
review_source: 'orchestrator'
---

# Refactor sweep

## Intent

Cleanup only, scoped from what the plans and reviews of stories 1.1 to 1.6 deferred. No behavior a test asserts changes. The scope below was written before any edit (criterion 1); anything not listed is out.

## Scope (each item with its source)

1. **Stale comment in the check entry point.** Source: 1.2 plan, review fixes ("comment added for story 1.4"); `check.py` still says "story 1.4's CI must keep it editable or set the root explicitly" although CI is built and installs devtools editable through `uv sync --locked`. Change: the comment states the present fact. Touches `packages/python/devtools/src/agentproof_devtools/check.py` (comment only).
2. **The sdist ships `devtools/` and `tests/`.** Source: 1.2 Implementation Notes ("the sdist ... includes `devtools/` and `tests/` ... an sdist `include`/`exclude` list ... can tighten this"). Since 1.6 the sdist is a release asset. Change: a `[tool.hatch.build.targets.sdist]` exclude for the two trees, and one test that builds the sdist and asserts neither tree is inside while `pyproject.toml` and the package are. Touches `packages/python/pyproject.toml`, `packages/python/tests/integration/test_install_smoke.py`.
3. **1.6 plan bookkeeping.** Source: the 1.6 plan's unticked orchestrator task, its `v0.0.0-test` matrix row (the tag became `v0.1.0.dev0` after review finding 3), and no record of the orchestrator's evidence. Change: tick the task, fix the row, append the evidence block. Touches the 1.6 plan only.

## Considered and left out (with reason)

- Replacing the `--help` panel parser in the install smoke test with a `CliRunner` check (1.1 risks: "if that happens"). It has not happened; the parser and the `COLUMNS=400` workaround are stable across the CI matrix. Untouched.
- The 1.1 plan's "both tests pass" wording: the 1.1 review declined that edit; not reopened.
- The AGENTS.md provisional-name policy line and the four `TODO (EPIC A)` lines: agent-context edits, done by the project-context refresh in the epic-1 close-out, not here.
- Import-contract tensions noted in 1.3 (`adapters -> io -> redaction`, `cli` cannot import `errors`): architecture decisions, renegotiated by the story that first hits one.
- The purity checker's documented `str.replace` false positive (1.3): a test pins it; changing it is behavior.
- `pip-audit` pin (1.6): already done by review finding 6.

## Boundaries & Constraints

- Must not change: any behavior a test from stories 1.1 to 1.6 asserts; the wheel contents; the `check` job; the gate command list.
- No new runtime dependency, no source change under `src/agentproof/`.

## I/O & Edge-Case Matrix

| Case | Input | Expected | Error |
|---|---|---|---|
| sdist contents | `uv build --sdist` | one `agentproof-<version>.tar.gz`; members include `pyproject.toml` and `src/agentproof/__init__.py`; none under `devtools/` or `tests/` | build failure fails the test |
| wheel unchanged | `uv build --wheel` | existing wheel-contents test still passes (only `agentproof/` and dist-info) | n/a |
| gate | `uv run check` | all five steps pass | n/a |

## Code Map

- `packages/python/devtools/src/agentproof_devtools/check.py` (comment)
- `packages/python/pyproject.toml` (`[tool.hatch.build.targets.sdist]`)
- `packages/python/tests/integration/test_install_smoke.py` (new sdist test)
- `_bmad-output/.../story-ci-builds-the-wheel-smoke-installs-it-and-audits-dependencie-plan.md` (bookkeeping)
- this plan

## Tasks & Acceptance

- [x] scope written from the 1.1 to 1.6 plans before any edit (criterion 1)
- [x] items 1 to 3 applied; diff touches only the Code Map
- [x] `uv run check` green locally; CI green on the pull request (criterion 2)

## Implementation Notes

2026-10-23. Items 1 to 3 applied as scoped. `uv run check`: ruff clean, 36 files formatted, mypy clean (18 files), Contracts: 7 kept, 0 broken, `250 passed` (was 249), exit 0. Red check: with the sdist exclude stashed, the new test fails on `devtools` and `tests` members; with it restored, passes. Diff touches only the Code Map.

## Plan Change Log

- 2026-10-23: `review` corrected from `quick` to `none`. No review lens ran on this sweep;
  the orchestrator read the diff and the CI results (retrospective epic 1, finding 10).

## Review Triage Log

## Verification

- `uv run check` from `packages/python` -- expected: all steps pass, pytest count = previous + 1
- `git diff --stat backlog` -- expected: only the Code Map paths
- `gh pr checks <pr>` -- expected: eight `check`, `wheel`, two `smoke`, `audit` green
