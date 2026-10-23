---
title: 'CI builds the wheel, smoke-installs it, and audits dependencies'
type: 'feature'
ticket: '6'
created: '2026-10-23'
status: done
baseline_revision: '037860bff77ad0fedf08d0a08b3707002d3cafdb'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CI proves the gate but not the install path users will take: nothing builds the wheel on a runner, installs it into a clean environment, audits the locked dependencies, or produces a release artifact (story 1.6, epic 1 R1 and R5).

**Approach:** Extend `.github/workflows/ci.yml` with a `wheel` job that builds and uploads the wheel, a `smoke` job on Linux and Windows that installs that wheel into a fresh venv and runs `agentproof version`, and an `audit` job that runs `pip-audit` against the exported lock; add `.github/workflows/release-draft.yml` that, on a `v*` tag, builds the wheel and attaches it to a draft GitHub release without publishing anywhere; extend the pin test to every workflow file and to the release job's permissions.

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** the draft release uses the runner's preinstalled `gh` CLI with the job's `GITHUB_TOKEN` rather than a third-party release action, so the only pinned actions remain checkout, setup-uv, upload-artifact, and download-artifact; the required status checks on `main` stay the eight `check` contexts, the new jobs are informative on pull requests and not required.

## Boundaries & Constraints

**Always:** Every `uses:` in every workflow is pinned to a 40-character SHA with a version comment; `ci.yml` keeps top-level `permissions: contents: read` and the `check` job unchanged; the smoke job installs the wheel by file path, never by name from an index; `pip-audit` runs against `uv export --locked` output covering the runtime and dev dependencies and fails the job on a known vulnerability; the release workflow has `permissions: contents: write` and nothing else, triggers only on `v*` tags, creates the release with `--draft`, and contains no publish step; the `agentproof` wheel contents stay identical to story 1.1.

**Never:** No PyPI publish, no `uv publish`, no `twine`, no trusted-publishing configuration (epic 9 story 5); no change to the `check` job, the check entry point, `pyproject.toml`, `uv.lock`, or `src/`; no example workflow (epic 8); no secrets beyond the automatic `GITHUB_TOKEN`; no edits to `AGENTS.md` or `PROJECT_SPEC.md`; the orchestrator pushes and opens the pull request, the implementer does not.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pull request | the story branch | `wheel` uploads `agentproof-0.1.0.dev0-py3-none-any.whl` as artifact `wheel`; `smoke (ubuntu-latest)` and `smoke (windows-latest)` install it into a fresh venv and print `0.1.0.dev0` with exit 0; `audit` passes | No error expected |
| Known vulnerability | a dependency with an advisory in the lock (simulated locally by auditing a requirements file that pins a known-vulnerable version) | `pip-audit` exits non-zero | job fails |
| Tag push | `v0.0.0-test` pushed by the orchestrator | a draft release exists with the wheel attached; `gh release view` shows `isDraft: true`; nothing on PyPI | No error expected |
| Pin test | every `.github/workflows/*.yml` | every `uses:` SHA-pinned with a version comment; release workflow permissions exactly `contents: write`; no `publish`, `twine`, or `pypi` token in any workflow | test failure otherwise |

</frozen-after-approval>

## Code Map

- `.github/workflows/ci.yml` -- edit; add jobs after `check`: `wheel` (ubuntu-latest; checkout, setup-uv, `uv build --wheel --out-dir dist` in `packages/python`, `actions/upload-artifact` with `name: wheel`, `path: packages/python/dist/*.whl`, `if-no-files-found: error`); `smoke` (`needs: wheel`, matrix `os: [ubuntu-latest, windows-latest]`, Python 3.12 via setup-uv; `actions/download-artifact` `name: wheel` to `dist`; `uv venv .smoke`; `uv pip install --python <venv python> dist/*.whl`; run the venv's `agentproof version` and assert the output equals the version in `pyproject.toml` with a small `bash` check); `audit` (ubuntu-latest; `uv export --locked --all-groups --no-emit-project -o requirements.txt` in `packages/python`; `uvx pip-audit --strict -r requirements.txt`). Resolve `actions/upload-artifact` and `actions/download-artifact` latest release SHAs with `gh api repos/actions/<name>/releases/latest` then `git/ref/tags/<tag>`; record tag and SHA in Implementation Notes.
- `.github/workflows/release-draft.yml` -- new; `on: push: tags: ["v*"]`; `permissions: contents: write`; one job `draft-release`: checkout, setup-uv, `uv build` in `packages/python`, then `gh release create "$GITHUB_REF_NAME" --draft --title "$GITHUB_REF_NAME" --generate-notes packages/python/dist/*` with `GH_TOKEN: ${{ github.token }}`; a header comment that publishing to PyPI is epic 9 story 5 and that this workflow is replaced then.
- `packages/python/tests/unit/test_workflow_pins.py` -- edit; the pin and version-comment tests iterate every `*.yml` under `.github/workflows`; new tests: the release workflow triggers only on `v*` tags, has permissions exactly `{"contents": "write"}`, and no workflow text contains `uv publish`, `twine`, `pypi-token`, or `PYPI`; the `wheel` job uploads an artifact named `wheel`; the `smoke` job has `needs: wheel` and installs from `dist/*.whl`; `audit` runs `pip-audit`.
- Existing: `test_workflow_pins.py` already allows extra jobs and extra actions after story 1.4's review; `check` job untouched.
- Local proof for the audit matrix row: in a scratch directory, write `requirements.txt` with `requests==2.19.0` (known advisories) and run `uvx pip-audit --strict -r requirements.txt`; expect non-zero; record the output.

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/ci.yml` -- add `wheel`, `smoke`, and `audit` jobs with resolved SHAs -- criteria 1, 2, 4
- [x] `.github/workflows/release-draft.yml` -- draft release on tag with `gh` -- criterion 3
- [x] `packages/python/tests/unit/test_workflow_pins.py` -- extend to every workflow; release permissions; no-publish; job shapes -- criterion 4
- [x] local verification -- `uv run check` green; the known-vulnerability audit proof recorded
- [ ] orchestrator -- push, pull request, confirm `wheel`, `smoke`, `audit` green on the PR, push a `v0.0.0-test` tag, confirm the draft release, delete the test tag and draft release, record evidence

**Acceptance Criteria:**
- Given the pull request, when CI runs, then `wheel`, both `smoke` jobs, and `audit` pass alongside the eight `check` jobs, and the smoke output shows `0.1.0.dev0`.
- Given a requirements file pinning a known-vulnerable package, when `pip-audit --strict` runs, then it exits non-zero.
- Given a `v*` tag, when the release workflow runs, then a draft release with the wheel attached exists and no publish step ran.
- Given every workflow file, when the pin test runs, then every action is SHA-pinned with a version comment and the release workflow's permissions are exactly `contents: write`.

## Implementation Notes

**2026-10-23, implementation subagent (files and local verification in worktree `D:\AgentProof-wt-1-6`, branch `story/1-6-wheel-smoke-audit`; no git writes).**

- **Action pins (resolved against GitHub today with `gh api`).** `repos/actions/<name>/releases/latest` then `git/ref/tags/<tag>`; both tags are lightweight and point straight at a commit (`object.type == "commit"`, no annotated-tag dereference needed):
  - `actions/upload-artifact` tag `v7.0.2` = `cf430e030ddbb5b0abf93d22962f4752f3646cd9`
  - `actions/download-artifact` tag `v8.0.2` = `9000827ccba6bdab643e8b6fd33ac0654aef8333`
  - `actions/checkout` `v7.0.1` = `3d3c42e5aac5ba805825da76410c181273ba90b1` and `astral-sh/setup-uv` `v10.3.2` = `07a047e608db84b3d8c06cd9a7c7dcc9c355c18e` are reused unchanged from story 1.4.
  - `action.yml` at each tag (`gh api repos/actions/<name>/contents/action.yml?ref=<tag>`) confirms the inputs used: upload `name`, `path`, `if-no-files-found`; download `name`, `path`. Both run on `node24`, which the GitHub-hosted runners provide.
- **One deviation from the Code Map, in the `audit` job: `--no-emit-workspace` added to `uv export`.** `uv export --locked --all-groups --no-emit-project -o <file>` still emits the workspace member as `-e ./devtools`; `uvx pip-audit --strict -r` on that file fails before auditing anything (`internal pip failure: ERROR: ./devtools is not a valid editable requirement`, exit 1). `agentproof-devtools` is our own local code with `dependencies = []`, so `--no-emit-workspace` drops exactly that one line and no third-party package: the export is 27 pinned, hashed third-party requirements covering the runtime and dev groups (annotated-doc, annotated-types, ast-serialize, click, colorama, grimp, import-linter, iniconfig, librt, markdown-it-py, mdurl, mypy, mypy-extensions, packaging, pathspec, pluggy, pydantic, pydantic-core, pygments, pytest, pyyaml, rich, ruff, shellingham, typer, typing-extensions, typing-inspection). The "Always" constraint (audit covers runtime and dev dependencies) is met; the pin test asserts the exact export command.
- **Workflow shape, `ci.yml`.** `git diff` is 95 insertions and 0 deletions: the header gains one comment paragraph about the story 1.6 jobs, and the `check` job, triggers, top-level `permissions: contents: read`, and `concurrency` are byte-for-byte unchanged. New jobs declare no `permissions` (they inherit `contents: read`; the artifact upload and download in the same run use the runner's runtime token, not `GITHUB_TOKEN` scopes). `wheel`: ubuntu-latest; checkout, setup-uv (`python-version: "3.12"`), `uv build --wheel --out-dir dist` in `packages/python`, `actions/upload-artifact` with `name: wheel`, `path: packages/python/dist/*.whl`, `if-no-files-found: error`, as the last step. `smoke`: `name: smoke (${{ matrix.os }})` (same text GitHub's default naming would render, set explicitly for the matrix row), `needs: wheel`, `fail-fast: false`, `os: [ubuntu-latest, windows-latest]`; checkout (read only for the expected version in `pyproject.toml`), setup-uv 3.12, `actions/download-artifact` `name: wheel` `path: dist`, `uv venv .smoke`, `uv pip install --python .smoke dist/*.whl` (uv accepts the venv directory as `--python`; verified locally), then a bash step that reads `version = "..."` from `packages/python/pyproject.toml` with `sed`, picks `.smoke/bin` or `.smoke/Scripts`, runs `"$bin/agentproof" version`, echoes both values, and `test`s them equal. All `smoke` run steps are `shell: bash` at the checkout root; the Windows runner's `bash` is Git Bash, which resolves `agentproof` to `agentproof.exe` (verified on this machine's Git Bash). `audit`: ubuntu-latest; the export above into `packages/python/requirements.txt` (a runner-only file: it is written on the runner and never committed) and `uvx pip-audit --strict -r requirements.txt`. `enable-cache` is not set on the new jobs; setup-uv's default `auto` enables it on GitHub-hosted runners anyway.
- **Workflow shape, `release-draft.yml`.** `name: Release draft`; `on: push: tags: ["v*"]` only; top-level `permissions: contents: write`, no job-level permissions; one job `draft-release` on ubuntu-latest: checkout, setup-uv 3.12, `uv build` in `packages/python` (sdist and wheel, per the Code Map, so the draft carries one `.tar.gz` and one `.whl`; the Verification row's "one `.whl` asset" still holds), then `gh release create "$GITHUB_REF_NAME" --draft --title "$GITHUB_REF_NAME" --generate-notes packages/python/dist/*` with `env: GH_TOKEN: ${{ github.token }}` as the last step. `gh` is preinstalled on ubuntu-latest. The header comment says publishing to PyPI is epic 9 story 5 and that this workflow is replaced then; the word "PyPI" (prose) passes the case-sensitive forbidden-text test below, while a `PYPI_*` secret name would not.
- **Pin test, `tests/unit/test_workflow_pins.py` (25 tests, 11 before).** `WORKFLOW_FILES = sorted(WORKFLOWS_DIR.glob("*.yml"))` drives a `parametrize` over both files for: every `uses:` matches `^[\w.-]+/[\w.-]+@[0-9a-f]{40}$`; every raw `uses:` key line ends in `# vX.Y.Z` and the commented refs equal the parsed ones; the set of action owners is a subset of exactly {checkout, setup-uv, upload-artifact, download-artifact} (the maintainer's delegated decision); neither `secrets.` nor `continue-on-error` appears; none of `uv publish`, `twine`, `pypi-token`, `PYPI`, `gh-action-pypi-publish` appears. Story 1.4's `check` assertions are unchanged except `test_top_level_permissions_are_contents_read_only`, which now asserts no job in `ci.yml` declares permissions. New single tests: `wheel` (no `needs`, exact build command and directory, exact upload `with`, upload is last); `smoke` (`needs: wheel`, name template, exact strategy, exact download `with`, first two run steps exactly `uv venv .smoke` and `uv pip install --python .smoke dist/*.whl`, every `pip install` step is that one file-path install, no `--index`/`--extra-index`/`-i`, last step runs `"$bin/agentproof" version`, reads `packages/python/pyproject.toml`, and compares `$actual` with `$expected`); `audit` (exactly the two run commands, both in `packages/python` with `shell: bash`); release trigger `== {"push": {"tags": ["v*"]}}`; release permissions `== {"contents": "write"}` with exactly one job `draft-release` and no job-level grant; release steps are checkout + setup-uv only, run steps exactly `uv build` (in `packages/python`, no `env`) then the `gh release create ... --draft ...` command with `env == {"GH_TOKEN": "${{ github.token }}"}`, and that step is last.
- **Local verification (uv 0.13.5 from `~/.local/bin`; `uv sync` in `packages/python` created this worktree's venv: 29 packages, exit 0).**
  - `uv run ruff check tests/unit/test_workflow_pins.py` -> `All checks passed!`, exit 0. `uv run ruff format --check` first flagged one implicit string concatenation that fits on one line; joined it; -> `1 file already formatted`, exit 0.
  - `uv run pytest tests/unit/test_workflow_pins.py -q` -> `25 passed in 2.75s`, exit 0.
  - `uv run check` -> `ruff check` All checks passed; `ruff format --check` 29 files already formatted; `mypy --strict` Success: no issues found in 16 source files; `lint-imports` 3 contracts KEPT; `pytest` `108 passed in 171.79s`; exit 0.
  - Mutation check that the new tests bite (each on the real file, restored from a backup afterwards; sha256 of both workflows identical before and after; clean run `25 passed`): unpinning `actions/checkout` to `@v7.0.1` -> only `test_every_action_is_pinned_to_a_full_commit_sha[ci.yml]` fails; removing `--draft` -> only `test_release_workflow_drafts_a_release_with_gh_and_the_job_token` fails; adding `packages: write` to the release permissions -> only `test_release_workflow_permissions_are_exactly_contents_write` fails; appending `PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}` to the release workflow -> `test_no_step_references_secrets_or_tolerates_failure[release-draft.yml]`, `test_no_workflow_publishes_to_a_package_index[release-draft.yml]`, and the gh-release test fail.
- **Known-vulnerability audit proof (I/O matrix row 2; scratch directory, `req.txt` = `requests==2.19.0`).** `uvx pip-audit --strict -r req.txt` (pip-audit 2.10.1) -> `Found 37 known vulnerabilities in 3 packages` (`requests 2.19.0`: PYSEC-2018-28, PYSEC-2023-74, PYSEC-2026-1872, PYSEC-2026-1873, PYSEC-2026-2275; `idna 2.7`: PYSEC-2024-60, PYSEC-2026-215; `urllib3 1.23`: PYSEC-2019-132/133, PYSEC-2020-148, PYSEC-2023-192/207/212, PYSEC-2026-141/1994/1995/1996/1999/4177, each listed per advisory id, several twice), **exit 1**.
- **Lock audit (what the `audit` job will see today).** `uv export --locked --all-groups --no-emit-project --no-emit-workspace -o <scratch>/lock-requirements.txt` -> `Resolved 29 packages`, exit 0, 27 pinned requirements; `uvx pip-audit --strict -r lock-requirements.txt` -> `No known vulnerabilities found`, **exit 0**.
- **Smoke path dry-run (what the `smoke` job does, on this machine).** `uv build --wheel --out-dir <scratch>/dist` in `packages/python` -> `agentproof-0.1.0.dev0-py3-none-any.whl`; `unzip -l` shows 20 entries, 4701 bytes: `agentproof/__init__.py`, `constants.py`, `errors.py`, the 13 subpackage `__init__.py` files (`adapters`, `assertions`, `cli`, `compare`, `engine`, `io`, `loading`, `models`, `redaction`, `reports`, `runner`, `testing`) plus `cli/app.py`, and the four `dist-info` files; nothing from `devtools` or `tests`, so the wheel contents are the story 1.1 set. `uv venv .smoke --python 3.12`, `uv pip install --python .smoke dist/*.whl` -> exit 0; `.smoke/Scripts/agentproof version` -> `0.1.0.dev0`, exit 0, equal to `version = "0.1.0.dev0"` in `pyproject.toml` (`MATCH`). The exact CI step script was not run as a unit here, but each of its commands was.
- **Housekeeping.** Files were written with LF endings; git reports it will normalise to CRLF in the working copy (`core.autocrlf`), which does not affect the committed content. The scratch directories (`audit-proof`, `smoke`, `backup`) and the `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, and `__pycache__` directories my runs created in the worktree were removed, and `uv cache clean pip-audit` dropped the 37 cached pip-audit files; the worktree's `.venv` stays, as instructed. One slip: the first sweep also deleted the `__pycache__` bytecode directories inside `.venv/Lib/site-packages` (a mis-targeted `-prune`); that is regenerated on import and nothing else in the venv was touched. Verified afterwards: `uv run --no-sync python -c "import pytest, yaml, pydantic, mypy, ruff, agentproof, agentproof_devtools"` -> `venv ok 0.1.0.dev0`, and the pin tests -> `25 passed`.
- **Not done here, by design (orchestrator steps):** push, pull request, confirming `wheel`, `smoke (ubuntu-latest)`, `smoke (windows-latest)`, and `audit` green on the PR, the `v0.0.0-test` tag, confirming and then deleting the draft release and tag. **Risks until the PR runs:** nothing above is proven on a GitHub runner; `uvx pip-audit` installs the current pip-audit release unpinned (not in the plan's scope; a `pip-audit==<version>` pin is a possible follow-up if reproducibility of the audit tool matters); `gh release create` fails if a release for the tag already exists, so re-running a tag push after a draft exists needs the draft deleted first; `--generate-notes` on the first tag generates notes from the whole history, which is fine for a draft.

## Plan Change Log

## Review Triage Log

2026-10-23, quick lens (adversarial, edge cases, verification gaps) on the staged diff. Eight findings, all applied:

1. smoke on Windows: CRLF broke both sides of the version comparison (the checkout normalises pyproject.toml to CRLF; Python's piped stdout writes CRLF). Fix: `tr -d '\r'` on both sides, `[^"]*` in the sed group.
2. release-draft: `gh release create` fails when a release for the tag already exists (UI-made release, re-run). Fix: `gh release view` then `gh release upload --clobber`, else create; never `gh release edit`.
3. release-draft: tag and `pyproject.toml` version were never compared. Fix: a guard step fails unless `${GITHUB_REF_NAME#v}` equals the declared version, before `uv build`.
4. Over-claim: the test proves pin form and version comment, not that the SHA is the tag's commit. Fix: comments in both workflows say so; SHA-to-tag is checked by hand with `gh api` when a pin is added.
5. Weak smoke assertions: the `Scripts` fallback and the `test -n "$expected"` guard were not asserted. Fix: the test asserts the exact lines.
6. `uvx pip-audit` floated. Fix: `uvx pip-audit==2.10.1`, the version used for the local vulnerability proof; test asserts the exact command.
7. `"$bin/agentproof"` without `.exe` relied on MSYS resolution. Fix: explicit `exe=.smoke/bin/agentproof`, else `.smoke/Scripts/agentproof.exe`.
8. The no-publish scan was a plain substring match (`twine` in "intertwined"). Fix: whole-word patterns.

Not changed: the reviewer's note that AC2 "fails on a known vulnerability" is pip-audit behaviour; the local proof with `requests==2.19.0` (exit 1, 37 advisories) stands as the evidence. The Verification tag is now `v0.1.0.dev0` (the declared version) because of finding 3; it is deleted with its draft after the check.

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green with the extended pin tests
- scratch: `printf 'requests==2.19.0\n' > req.txt && uvx pip-audit --strict -r req.txt` -- expected: non-zero exit with advisories listed
- `gh pr checks <pr>` -- expected: eight `check` jobs, `wheel`, `smoke (ubuntu-latest)`, `smoke (windows-latest)`, `audit` all passing
- `gh release view v0.1.0.dev0 --json isDraft,assets` -- expected: `isDraft: true`, one `.whl` and one `.tar.gz` asset

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths; `check` job diff is empty.
