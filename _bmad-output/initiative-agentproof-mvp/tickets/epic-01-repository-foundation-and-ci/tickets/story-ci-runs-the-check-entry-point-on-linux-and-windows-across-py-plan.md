---
title: 'CI runs the check entry point on Linux and Windows across Python 3.12 to 3.15'
type: 'feature'
ticket: '4'
created: '2026-10-23'
status: done
baseline_revision: 'bd292752290c78f4baa01bac40127d01027dac65'
route: 'full'
route_source: 'pinned'
risk: 'medium'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The gate exists only on the maintainer's Windows machine; nothing proves a change on Linux or on the other supported Python versions, and nothing stops an unchecked change from reaching `main` (story 1.4, epic 1 R3 and R5).

**Approach:** Add `.github/workflows/ci.yml` that runs `uv run check` on `ubuntu-latest` and `windows-latest` across Python 3.12, 3.13, 3.14, and 3.15 with SHA-pinned actions and least-privilege permissions, add a test that every workflow action is pinned, record the branch rule in CONTRIBUTING, and have the orchestrator (acting for the maintainer) push the branch, open the pull request that proves eight green jobs and one red run, and protect `main`.

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** the remote is `https://github.com/kamranhaq21/AgentProof` (existing, public, default branch `main`); work lands on `main` through pull requests from `backlog`; branch protection on `main` requires the CI check and a pull request with zero required approvals and does not enforce on administrators, so the solo maintainer is never locked out; the orchestrator performs the push, pull-request, and protection steps, not the implementation subagent.

## Boundaries & Constraints

**Always:** The check stage is exactly one step per job, `uv run check` in `packages/python`; every `uses:` is pinned to a full 40-character commit SHA with a `# vX.Y.Z` comment; top-level `permissions: contents: read`; the matrix is the product of two runners and four Python versions; uv is installed by the official setup action and Python by uv; devtools stays an editable install (default `uv sync`); `.github/workflows/ci.yml` is the only workflow file this story adds.

**Never:** No wheel build, smoke-install, audit, or release jobs (story 1.6); no example workflow (epic 8); no changes to the check entry point, `pyproject.toml`, or source under `src/`; no secrets; no `pip install agentproof` by name anywhere; no edits to `AGENTS.md` or `PROJECT_SPEC.md`; no `continue-on-error` unless a 3.15 dependency wheel is missing, and then only on the 3.15 cell with a dated comment and a follow-up entry in deferred work.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pull request opened | the story branch targets `backlog` | eight `check` jobs run and pass; the job names are `check (ubuntu-latest, 3.12)` and so on | No error expected |
| Deliberate failure | a commit adding `assert False` in a test | every job fails at the `pytest` step; the PR shows red | job failure is the expected signal |
| Pinned actions | `ci.yml` read by the test | every `uses:` matches `owner/repo@<40 hex>` followed by a version comment | test failure otherwise |
| Permissions | `ci.yml` read by the test | top-level `permissions` is exactly `contents: read` | test failure otherwise |
| Branch protection | `gh api .../branches/main/protection` after the step | required status checks list the eight job contexts, pull requests required, admins not enforced | No error expected |

</frozen-after-approval>

## Code Map

- `.github/workflows/ci.yml` -- new; `name: CI`; `on: pull_request` (all branches) and `push` to `main` and `backlog`; `permissions: contents: read`; `concurrency` keyed on the ref with cancel-in-progress; one job `check` with `strategy.fail-fast: false`, `matrix.os: [ubuntu-latest, windows-latest]`, `matrix.python: ["3.12", "3.13", "3.14", "3.15"]`; steps: `actions/checkout@<sha> # v5.x`, `astral-sh/setup-uv@<sha> # v7.x` with `python-version: ${{ matrix.python }}` and `enable-cache: true`, then `run: uv sync --locked` and `run: uv run check`, both with `working-directory: packages/python`, `shell: bash`. Resolve the SHAs with `gh api repos/actions/checkout/git/ref/tags/<tag>` and `gh api repos/astral-sh/setup-uv/git/ref/tags/<tag>` (dereference annotated tags to the commit) and record the tag and SHA in Implementation Notes.
- `packages/python/tests/unit/test_workflow_pins.py` -- new; parses `.github/workflows/ci.yml` with `yaml.safe_load`; asserts every `uses:` value matches `^[\w.-]+/[\w.-]+@[0-9a-f]{40}$` and that the same line in the raw text carries a `# v` comment; asserts `permissions == {"contents": "read"}`; asserts the matrix os and python lists; asserts the check step command is `uv run check` with `working-directory: packages/python`; asserts no step references `secrets.`.
- `CONTRIBUTING.md` -- edit the "Branches and pull requests" section: `main` is protected, requires the CI check and a pull request; `backlog` is the integration branch stories merge into; the sentence written in story 1.5 about CI ("story 1.4, not yet in place") becomes present tense.
- Existing: `uv run check` (story 1.2), `uv.lock` with devtools editable (`uv sync --locked` must succeed from a clean checkout; if the lock is stale the step fails and the lock must be refreshed in this story).
- Orchestrator steps (not the subagent): push `story/1-4-ci-workflow`, open the PR against `backlog`, push a one-commit failure and its revert to prove the red run, apply branch protection on `main` with the eight job contexts through `gh api`, record evidence in Implementation Notes.

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/ci.yml` -- write the workflow with resolved SHAs -- criteria 1 and 2
- [x] `packages/python/tests/unit/test_workflow_pins.py` -- pin, permission, matrix, and no-secrets assertions -- criterion 2
- [x] `CONTRIBUTING.md` -- branch rule and present-tense CI sentence -- criterion 4
- [x] local verification -- `uv run check` green (the new test included); `uv sync --locked` succeeds from a fresh venv to prove the lock is current
- [x] orchestrator -- push, pull request, red-then-green proof, branch protection, evidence recorded -- criteria 1, 3, 4

**Acceptance Criteria:**
- Given the pull request, when CI runs, then eight `check` jobs appear and pass.
- Given a commit with a failing test on the PR, when CI runs, then every job is red at `pytest`, and after the revert they are green again.
- Given `ci.yml`, when the pin test runs, then every action is SHA-pinned with a version comment and permissions are `contents: read`.
- Given `main`, when its protection is read, then the CI contexts are required and pull requests are required, and CONTRIBUTING says so.

## Implementation Notes

- 2026-10-23, orchestrator (GitHub steps): pushed `story/1-4-ci-workflow` and opened pull request #1 against `backlog` (https://github.com/kamranhaq21/AgentProof/pull/1). Run 39896988588 on commit 606c0c2: all eight `check` jobs passed, including both 3.15 cells (pyyaml built from sdist on the runners). Run 39897319496 on 1c5aaa3 (`assert False`): all eight failed at `ruff check` (B011), proving the gate order. Run 39897818215 on c029ce8 (`assert 1 == 2`): all eight failed at `pytest`, proving the criterion's stage. Run 39897969954 on c0c7b63 (test removed): all eight passed. Branch protection applied to `main` through `gh api`: eight required contexts `check (<os>, <python>)`, strict status checks, pull request required with zero approvals, administrators not enforced; read back from the API as applied. Every push waited for the previous run to finish so `cancel-in-progress` never cancelled a proof run.

**2026-10-23, implementation subagent (files, local verification; no git writes).**

- **Action pins (verified against GitHub today).** Both tags are lightweight and point straight at a commit (`gh api repos/<owner>/<repo>/git/ref/tags/<tag>` returned `object.type == "commit"`, so no annotated-tag dereference was needed):
  - `actions/checkout` tag `v7.0.1` = `3d3c42e5aac5ba805825da76410c181273ba90b1`
  - `astral-sh/setup-uv` tag `v10.3.2` = `07a047e608db84b3d8c06cd9a7c7dcc9c355c18e`
  - The Code Map's `# v5.x` / `# v7.x` comments were written when those were current; the orchestrator supplied the resolved current majors above and those are what `ci.yml` pins. The pin test checks the SHA shape and the presence of a `# vX.Y.Z` comment, not a specific major.
  - `setup-uv` v10.3.2 `action.yml` (fetched with `gh api repos/astral-sh/setup-uv/contents/action.yml?ref=v10.3.2`) spells the inputs `python-version` (sets `UV_PYTHON`) and `enable-cache` (default `auto`); `ci.yml` passes `enable-cache: true` explicitly as the plan says. The default `cache-dependency-glob` includes `**/uv.lock`, which reaches `packages/python/uv.lock` from the workspace root, so no override is needed.
- **Workflow shape.** `.github/workflows/ci.yml`: `name: CI`; `on: pull_request` (unfiltered) and `push` to `main` and `backlog`; top-level `permissions: contents: read` and no job-level permissions; `concurrency.group: ci-${{ github.ref }}` with `cancel-in-progress: true`; one job `check` with `fail-fast: false`, `os: [ubuntu-latest, windows-latest]`, `python: ["3.12", "3.13", "3.14", "3.15"]`. The job `name` is set explicitly to `check (${{ matrix.os }}, ${{ matrix.python }})`, which renders identically to GitHub's default matrix naming and yields the eight contexts `check (ubuntu-latest, 3.12)` ... `check (windows-latest, 3.15)` for the protection rule. `working-directory: packages/python` and `shell: bash` are on each `run` step (not `defaults.run`) so the test can assert them per step. Steps: checkout, setup-uv, `uv sync --locked`, `uv run check`. No `continue-on-error` anywhere (see the 3.15 note below).
- **Pin test.** `packages/python/tests/unit/test_workflow_pins.py`, 11 tests: `ci.yml` is the only file in `.github/workflows/`; triggers; every `uses:` matches `^[\w.-]+/[\w.-]+@[0-9a-f]{40}$`; every raw `uses:` key line ends in `# vX.Y.Z` and the commented refs equal the parsed ones; the actions are exactly checkout and setup-uv; permissions `== {"contents": "read"}` with none on the job; `fail-fast` false and the matrix lists exactly as above with no include/exclude; the job name template; setup-uv `with` is exactly `python-version` + `enable-cache: true`; the run steps are exactly `uv sync --locked` then `uv run check`, each with `working-directory: packages/python` and `shell: bash`, and `uv run check` is the last step; neither `secrets.` nor `continue-on-error` appears in the file. PyYAML reads the bare `on` key as boolean `True`; the test handles both spellings. One self-inflicted failure during development: the raw-line scan first used `re.search(r"\buses:")`, which also matched the header comment that mentions `` `uses:` ``; it now matches key lines only (`^\s*-?\s*uses:`).
- **CONTRIBUTING.** "The one check": the story-1.5 sentence `CI (story 1.4, not yet in place) will call ...` is now present tense and names `.github/workflows/ci.yml`, Linux and Windows, and Python 3.12 to 3.15. "Branches and pull requests": `main` is protected (pull request required, the eight `check` jobs required, zero approvals, not enforced on administrators) and `backlog` is the integration branch that story branches (`story/<n>-<slug>`) target and that lands on `main` through a pull request. `test_contributing_states_the_check_command_and_policies` still passes.
- **Python 3.15 and the lock (the one risk for the PR run).** `uv.lock` (revision 5, `requires-python = ">=3.12, <4"`) has cp315 wheels for every compiled dependency except `pyyaml`: `pydantic-core` 2.50.1, `mypy` 2.4.0, `grimp` 3.17, `librt` 0.16.0, and `ast-serialize` 0.13.1 all ship cp315 wheels; `pyyaml` 6.0.3 ships cp312/cp313/cp314 wheels and an sdist only. PyPI was checked today: 6.0.3 is still the latest pyyaml release and no release has a cp315 wheel, so no in-range lock refresh can fix this; the 3.15 cells build pyyaml from the sdist. Local proof on this machine: `UV_PROJECT_ENVIRONMENT=<scratch> uv sync --locked --python 3.15` downloaded CPython 3.15.1, resolved the lock, and failed only at `Building pyyaml==6.0.3` with `error: Microsoft Visual C++ 14.0 or greater is required` (no compiler on this machine). Both GitHub runner images carry one: `windows-latest` (image 20261021.299.1) has Visual Studio Enterprise 2022 17.14 with the `NativeDesktop` workload, and `ubuntu-latest` (image 20261012.334.1) has GCC 12/13/14 and `libyaml-dev` 0.2.5. pyyaml's build falls back to the pure-Python package when libyaml is absent, so the 3.15 cells are expected to pass on both runners; nothing is proven until the PR runs. Decision: no `continue-on-error`. If the PR's `check (*, 3.15)` jobs fail at `uv sync --locked` on the pyyaml build, the plan's escape hatch applies: `continue-on-error: ${{ matrix.python == '3.15' }}` on the job with a dated comment, plus a deferred-work entry to drop it when pyyaml ships cp315 wheels (and in that case `test_no_step_references_secrets_or_tolerates_failure` must be relaxed to allow exactly that expression). The scratch venv and the downloaded CPython 3.15.1 were removed afterwards (`uv python uninstall 3.15.1`); the managed interpreters are back to 3.12.15 and 3.13.16 as found.
- **Local verification (all with uv 0.13.5 from `~/.local/bin`, in `packages/python`).**
  - Baseline before changes: `uv run check` -> 83 passed.
  - `uv run ruff check tests/unit/test_workflow_pins.py` -> `All checks passed!`; `uv run ruff format --check tests/unit/test_workflow_pins.py` -> `1 file already formatted`.
  - `uv run pytest tests/unit/test_workflow_pins.py tests/unit/test_repo_hygiene.py -q` -> 22 passed.
  - `uv run check` (existing venv, CPython 3.12.15) -> all five steps, `94 passed in 142.60s`, exit 0.
  - `rm -rf .venv && uv sync --locked` -> `Resolved 29 packages`, `Installed 29 packages in 8.68s`, exit 0; `agentproof-devtools` editable from `packages/python/devtools`; the recreated venv chose CPython 3.13.16 (highest installed interpreter satisfying `requires-python`; nothing pins 3.12 locally), and `uv run check` on it -> `94 passed in 177.42s`, exit 0. The working venv is left in place.
- **Not done here, by design:** push, pull request, red-then-green proof, branch protection (orchestrator steps). Observed but not touched: two `epic-09` ticket files were already modified in the working tree before this story started (an `0001-license.md` -> `0021-license.md` reference fix); they are unrelated to this story.

## Plan Change Log

## Review Triage Log

### Review pass 1 (quick lens), 2026-10-23

Verdicts: high 0, medium 3, low 1, false 0, maybe-false 0, plus one "evidence pending" item.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| `assert False` is stopped by ruff B011, so the red run fails at `ruff check`, not `pytest` | medium | patch (orchestrator) | True: run 39896988588's second attempt failed at `ruff check` with B011; a ruff-clean `assert 1 == 2` was pushed as commit c029ce8 to prove the `pytest` stage. The first red run still stands as proof the gate order holds. |
| `cancel-in-progress` can cancel the red run if the revert is pushed early | low | process | True; every push waited for the previous run to finish. |
| CONTRIBUTING overstated the protection ("never skipped") and misattributed bullets to spec §13.2 | medium | patch | True; reworded: administrators can bypass, everyone else cannot; attribution to the maintainer's 2026-10-22 decisions added. |
| The pin test froze this story's job and action set as a repository invariant (only workflow, only job, last step) | medium | patch | True; story 1.6 adds jobs. Assertions relaxed to: workflow exists, `check` job has the required shape, every action in every job is pinned, no secrets anywhere. |
| Orchestrator criteria unevidenced at review time | pending | evidence below | Recorded in Implementation Notes once the green rerun and the protection read-back are in hand. |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: 84 or more tests pass, exit 0
- `cd packages/python && rm -rf .venv && uv sync --locked && uv run check` -- expected: lock current, gate green (restore the venv afterwards by the same command)
- `gh pr checks <pr>` -- expected: eight passing checks
- `gh api repos/kamranhaq21/AgentProof/branches/main/protection` -- expected: eight required contexts, pull request required

**Manual checks (if no CLI):**
- The PR page shows the matrix; the red run and the green rerun are both visible in the checks history.
