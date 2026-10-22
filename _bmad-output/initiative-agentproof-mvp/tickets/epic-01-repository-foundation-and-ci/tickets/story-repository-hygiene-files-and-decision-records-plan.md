---
title: 'Repository hygiene files and decision records'
type: 'chore'
ticket: '5'
created: '2026-10-23'
status: 'built'
baseline_revision: '5705d837a7ec210d65632779cc4dacef0b28d324'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repository is developed on Windows and will be tested on Linux, yet nothing protects line endings, nothing ignores caches and local artifacts, there are no contributor or security documents, and the twenty architecture decisions live only inside a planning document instead of `docs/decisions/` where the spec says decisions go (story 1.5, epic 1 R5 and R6).

**Approach:** Add `.gitattributes` (LF for golden files and schemas), a complete `.gitignore`, `.editorconfig`, a pre-commit config running ruff, CONTRIBUTING with the check command and policies, SECURITY with a reporting-channel placeholder, the Contributor Covenant code of conduct, `docs/architecture.md` linking the spine, and one file per ADR under `docs/decisions/` copied from `adr-log.md`, with tests that the attributes, ignores, and decision records are present.

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** ADR files are numbered `0001` to `0020` to match ADR-001 to ADR-020; the OQ-2 license stub is therefore `docs/decisions/0021-license.md` (epic 9 story 4 names it `0001-license.md` and must be repointed by the Product Owner); the generated `_bmad/render/` directory is left as it is in this story.

## Boundaries & Constraints

**Always:** `.gitattributes` keeps `**/tests/golden/**` and `schemas/*.json` at LF; `.gitignore` keeps `examples/**/traces/` trackable; CONTRIBUTING states `uv run check`, the short-lived-branch and pull-request rule, the 0.x pre-1.0 API policy from spine AD-15, and that a new runtime dependency needs an ADR; SECURITY names a reporting channel placeholder the maintainer fills; pre-commit runs `ruff check` and `ruff format` only, pinned to a tag that matches the ruff version in `uv.lock`; each ADR file carries its ADR id, AD id, status, and the full text from `adr-log.md` unchanged; the `agentproof` wheel is unaffected.

**Never:** No LICENSE file (OQ-2 open); no edits to `AGENTS.md` or `PROJECT_SPEC.md`; no CI (story 1.4); no change to `.importlinter`, the check entry point, or any Python source under `src/`; no new runtime or dev dependency; no untracking or ignoring of `_bmad/render/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Golden file on a Windows clone | a file under `packages/python/tests/golden/` with `core.autocrlf=true` | checked out with LF endings, verified by a test reading bytes | No error expected |
| Local artifacts | `.venv/`, `dist/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.import_linter_cache/`, `agentproof-output/`, `.agentproof-*`, `_bmad/custom/*.user.toml` present | `git status` shows none of them | No error expected |
| Example traces | a file under `examples/expense-agent/traces/` | not ignored | No error expected |
| Decision records | `docs/decisions/` listed | `0000-distribution-name.md`, `0001` to `0020` ADR files, `0021-license.md`, `README.md` index | No error expected |
| Pre-commit config | `uvx pre-commit validate-config` | valid; ruff hook revision equals the ruff version in `uv.lock` | No error expected |

</frozen-after-approval>

## Code Map

- `.gitattributes` -- new; `* text=auto`, `**/tests/golden/** text eol=lf`, `schemas/*.json text eol=lf`, `*.lock text eol=lf`, `*.sh text eol=lf`, `*.bat text eol=crlf`.
- `.gitignore` -- rewrite (currently three lines plus a comment); keep `.claude/skills/`; add `.venv/`, `dist/`, `build/`, `*.egg-info/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.import_linter_cache/`, `agentproof-output/`, `.agentproof-*`, `_bmad/custom/*.user.toml`, `.hypothesis/`; a comment that `examples/**/traces/` is intentionally tracked.
- `.editorconfig` -- new; `root = true`, UTF-8, LF, final newline, 4-space Python, 2-space YAML/TOML/JSON/Markdown with trailing whitespace kept for Markdown.
- `.pre-commit-config.yaml` -- new; `astral-sh/ruff-pre-commit` at the tag matching ruff in `packages/python/uv.lock` (verify the tag exists with `git ls-remote --tags`), hooks `ruff` (with `--fix` off) and `ruff-format`; `args` pointing at `packages/python/pyproject.toml` config.
- `CONTRIBUTING.md` -- new; sections: setup (`uv sync` in `packages/python`), the one check (`uv run check`), branches and pull requests (short-lived, PR even solo, `main` releasable, per spec §13.2), versioning policy (0.x semver; minor may change the public API with a changelog entry, patch may not; artifact schema versions are integers independent of the package version, spine AD-15 and AD-3), dependency policy (four runtime dependencies; adding one needs an ADR, spine AD-16), decision records (how to add an ADR), security (link SECURITY.md).
- `SECURITY.md` -- new; supported versions table (0.x, latest minor only), reporting channel placeholder `<security contact to be filled by the maintainer>`, response window placeholder, pointer to `docs/security.md` (epic 9) for limits.
- `CODE_OF_CONDUCT.md` -- new; Contributor Covenant 2.1 text with the enforcement contact as the same placeholder.
- `docs/architecture.md` -- new; one page linking `_bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md` and `docs/decisions/`.
- `docs/decisions/README.md` -- new; index table of 0000 to 0021 with status.
- `docs/decisions/0001-functional-core-imperative-shell.md` ... `0020-cli-contract-and-fixed-honesty-statements.md` -- new; each from the corresponding `## ADR-NNN` section of `adr-log.md`: title line `# ADR-NNN (AD-N): <title>`, then the section body verbatim.
- `docs/decisions/0021-license.md` -- new stub; status open, candidate Apache-2.0, what changes once decided (LICENSE file, pyproject `license`, classifiers, CONTRIBUTING terms).
- `packages/python/tests/golden/README.md` -- new; explains the LF rule and that goldens are compared byte for byte; it is the first LF-protected file the test reads.
- `packages/python/tests/unit/test_repo_hygiene.py` -- new; reads the repository root files: `.gitattributes` has the golden and schema patterns; `.gitignore` has every required entry and no `examples` entry; every file under `tests/golden/` contains no `\r`; `docs/decisions/` holds 0000, 0001 to 0020, 0021, README, and each ADR file's first line names its ADR id; CONTRIBUTING contains `uv run check`; `.pre-commit-config.yaml` ruff rev equals the ruff version in `uv.lock` (parse with `tomllib`).
- Reuse: `docs/decisions/0000-distribution-name.md` exists from story 1.1; keep it.

## Tasks & Acceptance

**Execution:**
- [x] `.gitattributes`, `.gitignore`, `.editorconfig` -- write per the Code Map -- criteria 1 and 2
- [x] `.pre-commit-config.yaml` -- ruff hooks pinned to the locked ruff version -- criterion 3
- [x] `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` -- write per the Code Map -- criterion 3
- [x] `docs/architecture.md`, `docs/decisions/README.md`, `docs/decisions/0001` to `0020`, `0021-license.md` -- generate the ADR files from `adr-log.md` with a short script run once (not committed), verify each body matches its source section -- criterion 4
- [x] `packages/python/tests/golden/README.md`, `packages/python/tests/unit/test_repo_hygiene.py` -- the LF, ignore, and decision-record tests -- all criteria

**Acceptance Criteria:**
- Given the repository root, when `.gitattributes` is read, then golden files and schema JSON are forced to LF, and the golden README contains no carriage return on this Windows checkout after `git add`/re-checkout.
- Given `.gitignore`, when the listed artifact paths exist, then `git status --ignored` lists them as ignored and `examples/**/traces/` is not ignored.
- Given CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, `.editorconfig`, `.pre-commit-config.yaml`, when read, then each states what the Always clause requires.
- Given `docs/decisions/`, when listed, then it holds the twenty ADR files, the two stubs, and the index, and `docs/architecture.md` links the spine.

## Implementation Notes

- 2026-10-23, implementation (Claude). All Code Map files written; `uv run check` passes (83 tests, 11 of them in the new `tests/unit/test_repo_hygiene.py`).
- **Pre-commit hook ids.** At `ruff-pre-commit` tag `v0.17.2` (verified with `git ls-remote --tags` and the tag's `.pre-commit-hooks.yaml`) the `ruff` id is a "legacy alias" of `ruff-check`; the config uses `ruff-check` and `ruff-format`. Same entry (`ruff check --force-exclude`, `--fix` not passed), current name, so a later tag bump cannot break on a removed alias.
- **Deviation from the Code Map: no `--config` args on the hooks.** Running ruff from the repository root with `--config packages/python/pyproject.toml` resolves `per-file-ignores` and `src` against the working directory, so `devtools/**` and `tests/**` no longer match and TID251 fires on `devtools/src/agentproof_devtools/check.py` (`import subprocess`), reproduced with `uv run --project packages/python ruff check --force-exclude --config packages/python/pyproject.toml ...` from the root (exit 1). Without `--config`, ruff discovers `packages/python/pyproject.toml` per file and resolves the patterns against it; the same invocation from the root exits 0 for check and format. The config comments explain this so nobody re-adds the argument. `pyproject.toml` was not touched.
- **Ignore check.** `git check-ignore -v --no-index` matches every pattern in the matrix; `examples/expense-agent/traces/run.json`, `_bmad/render/bmad-build/x`, and `_bmad/custom/team.toml` are not ignored. `_bmad/custom/.gitignore` already carried `*.user.toml`; the root rule is additive. The plan's probe (`packages/python/dist/x`, `packages/python/__pycache__/x`) showed both as `!!` in `git status --ignored --short`; probes removed.
- **Line endings.** The index was already LF-only (`git ls-files --eol` showed no `i/crlf`), so `* text=auto` flags no tracked file as modified. `git check-attr -a packages/python/tests/golden/README.md` gives `text: set`, `eol: lf`; `schemas/suite.json`, `*.lock`, `*.sh` resolve to `eol: lf`, `*.bat` to `eol: crlf`. Every new file was written with LF (CR count 0 per file). The acceptance wording "after `git add`/re-checkout" could not be exercised because the implementation was not allowed to touch git state; the attribute resolution and the byte test stand in for it until the branch is staged.
- **ADR files.** Generated once by a scratch script (not committed) that split `adr-log.md` on `## ADR-NNN (AD-N) — <title>`, wrote `# ADR-NNN (AD-N): <title>` plus the body verbatim, and slugified the full title (hence the long names for 0003, 0008, 0010). A second scratch script, parsing independently from each file's own title line, confirmed all 20 bodies identical to their source sections (`identical=20 mismatched=0`). The log's per-section `**Status:**` line is kept inside each body; the index table repeats it.
- **Hygiene test scope beyond the Code Map.** The test also asserts the decision index lists every record, `docs/architecture.md` links the spine, SECURITY carries the placeholder, and the hook ids/`--fix` absence, so the Always clause is machine-checked rather than only read.
- **0021-license.md** records the epic 9 story 4 repoint (`0001-license.md` to `0021-license.md`) for the Product Owner; nothing in the tickets was edited.
- **Not done here (out of scope by the Never clause):** no LICENSE, no CI, no `pyproject.toml` change, `_bmad/render/` left as is.

## Plan Change Log

## Review Triage Log

### Review pass 1 (quick lens), 2026-10-23

Verdicts: high 0, medium 4, low 2, false 0, maybe-false 0. Patches applied by the orchestrator (text-only edits).

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| CONTRIBUTING states CI runs the gate; no CI exists yet | medium | patch | True (AGENTS.md: never describe as done what is not built); reworded to story 1.4 future tense. |
| SECURITY asserts replay and redaction behavior as shipped | medium | patch | True; reworded as design commitments backed by tests as v0.1 lands. |
| Pre-commit hooks unscoped; would run ruff defaults on `.agents/` scripts and rewrite them | medium | patch | True; `files: ^packages/python/` on both hooks. |
| `test_decision_records_are_complete` uses set equality; the first new ADR breaks the gate | medium | patch | True; containment assertion instead. |
| CONTRIBUTING supersede rule contradicts the fill-in stubs | low | patch | True; carve-out for Proposed records and open stubs. |
| LF round trip unverified until the golden README is staged | low | verify at commit | True; `git ls-files --eol` is checked after `git add` below. |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: all five steps pass (the new test included)
- `git check-attr -a packages/python/tests/golden/README.md` -- expected: `text: set`, `eol: lf`
- `git status --ignored --short | grep '^!!'` after creating `packages/python/dist/x` and `packages/python/__pycache__/x` -- expected: both listed as ignored; remove them after
- `uvx pre-commit validate-config .pre-commit-config.yaml` -- expected: no output, exit 0
- `python -c` comparison of each `docs/decisions/00NN-*.md` body against its `adr-log.md` section -- expected: identical text

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths; `AGENTS.md`, `PROJECT_SPEC.md`, `.importlinter`, and `src/` untouched.
