---
epic: epic-01-repository-foundation-and-ci
date: 2026-10-23
verdict: accepted-with-open-items
criteria: declared
headless: true
---

# Retrospective: epic-01-repository-foundation-and-ci

Headless run (`-H epic-01-repository-foundation-and-ci`). Every finding below carries a source reference; a claim that could not be tied to a file, line, commit, run id, or command output was dropped. Fixes and spec reconciliations are proposed, not applied. Nothing in the ticket tree was changed by this run other than the creation of this file.

## Epic summary

**Epic:** `epic-01-repository-foundation-and-ci` — "Repository foundation and CI: the package installs from a built wheel and one check entry point runs locally and in CI on Linux and Windows". Epic file: `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md`. Covers initiative R27, R28, R29, C1, C7, C9, C10; epic-local requirements R1 to R6; Done when declared (five bullets).

**Tickets** (`tickets.py status <folder>`, build order; `counts: total 7, done 7`):

| Ref | Title | status | state | covers | plan `baseline_revision` |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Package scaffold installs and prints its version | done | done | R1, R2 | `5a4dc1b` |
| 1.2 | One check entry point runs ruff, mypy, and pytest | done | done | R3 | `f12115c` |
| 1.3 | Import contracts encode the dependency direction | done | done | R4 | `8afabe2` |
| 1.4 | CI runs the check entry point on Linux and Windows across Python 3.12 to 3.15 | done | done | R3, R5 | `bd29275` |
| 1.5 | Repository hygiene files and decision records | done | done | R5, R6 | `5705d83` |
| 1.6 | CI builds the wheel, smoke-installs it, and audits dependencies | done | done | R1, R5 | `037860b` |
| 1.7 | Refactor sweep | done | done | R3 | `05ed167` |

- Tickets still at `built`: none.
- `pending_tickets`: empty. No unfinished ticket; nothing was retro'd over.
- Every entry's `description` and `verify` are empty in `find` output (pulled); the seven story files under `tickets/` hold them. All seven plans are `status: done`.

**Plan ranges** (ordered by baseline position in history, oldest first; `git_evidence.py` run once per distinct range):

The history was rewritten between story 1.5 and story 1.4 (see finding B1). Four baselines (`5a4dc1b`, `f12115c`, `8afabe2`, `5705d83`) are commits on a lineage that is **not an ancestor of HEAD**; the live lineage (`401fef0` → … → `bd29275`) was recreated with identical trees plus a one-line `README.md` (`git diff 5a4dc1b 401fef0` and `git diff 22c8f48 bd29275` each show only `README.md`, 1 insertion). Both lineages were measured; the numbers are identical, so each range below is given on the recorded (orphan) baseline with its live-lineage equivalent.

| Plan | Range (recorded baseline → next baseline) | Live-lineage equivalent | Commits | Code files / net lines |
| --- | --- | --- | --- | --- |
| 1.1 | `5a4dc1b..f12115c` | `401fef0..4a48899` | 2 | 22 / +661 (uv.lock +355) |
| 1.2 | `f12115c..8afabe2` | `4a48899..8f6df80` | 2 | 8 / +652 (uv.lock +391) |
| 1.3 | `8afabe2..5705d83` | `8f6df80..bb89d24` | 2 | 7 / +876 |
| 1.5 | `5705d83..22c8f48` (lineage end; cut recorded) | `bb89d24..bd29275` | 2 | 32 / +705 |
| 1.4 | `bd29275..037860b` | same | 8 (1 merge, PR #1) | 4 / +204 |
| 1.6 | `037860b..05ed167` | same | 7 (2 merges, PR #2 and #3) | 13 / +1235, of which story **2.1** (epic 2) contributes `d7f765d`, `376fbb7`, merge `39ab5e1`, `17c885a` and 9 files (+1043) — excluded from epic-1 attribution |
| 1.7 | `05ed167..38e55ff` (HEAD; **inferred**, not recorded) | same | 3 (1 merge, PR #4) | 3 / +25 |

`merges_measured == merge_count` for every range (no unmeasured merges); `binary_revisions` is 0 for every path. `merge_files` restates the merged churn in each case and added no conflict-resolution-only paths. Row order (1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7) differs from build order: 1.5 was built before 1.4, as the `after: [2, 5]` dependency on 1.4 requires.

**Evidence inventory**

| Evidence | Available | Notes |
| --- | --- | --- |
| Epic file with Done when | yes | Five declared criteria; Phase 4 judged against them (criteria: declared). |
| Initiative Requirements (R1..R31) and Constraints (C1..C10) | yes | `initiative-agentproof-mvp.md`. |
| Architecture spine, adr-log, PRD | yes | `architecture-agentproof/architecture-agentproof.md` (AD-1, AD-2, AD-15..AD-19 read), `prd-agentproof/`. |
| Entries, story files, plans | yes | 7 + 7 + 7; plans 1.4 and 1.6 have `review: ''` and `lenses_ran: []` although their triage logs record a review (finding A4). |
| Diff ranges and commits | yes, with the lineage caveat above | `git_evidence.py` on 11 ranges (both lineages). |
| GitHub evidence | yes (read-only `gh`) | PRs #1 to #4 all merged into `backlog`; CI runs listed; branch protection on `main` read back; release-draft run 39902388238 success; releases and tags now empty (the test draft and tag were deleted as the 1.6 plan records). |
| Previous retrospective | **none** | First epic; nothing to follow through. |
| Session logs | **absent** | Not available for any of the seven builds. Process-lesson analysis is limited to what the plans' Implementation Notes and Review Triage Logs record; the "why" behind abandoned attempts is unrecoverable except where a plan wrote it down. |
| Behavior check | yes | `uv run check`, `agentproof version`, `uv build`, fresh-venv wheel install, sdist unpack (see Behavior verification). |

## Findings

Dispositions: **fix now** (becomes an action item), **defer** (tracked with enough context to act later), **accept** (recorded so later retros stop re-flagging). Findings from the `bmad-review` lenses were re-checked against the primary source before being kept; the ones that did not hold up, or that duplicated another finding, are folded or dropped and said so.

### Aggregate views

**A1. Architecture delta — clean, derived inline (narrowed scope).** No dependency tool (pydeps) is installed; the import graph was read from the files. Epic-1 code in `src/agentproof` imports only the stdlib and `typer`: `cli/app.py:21-23` imports `typer` and `from agentproof import __version__`; `__init__.py:9` imports `importlib.metadata`. `lint-imports` on HEAD reports `Analyzed 18 files, 2 dependencies`, `Contracts: 7 kept, 0 broken` (`uv run check` output). The devtools graph is `check.py:20` → `purity.py`. No cross-cutting dependency, layering violation, or cycle was introduced. The two source-level dependencies at HEAD belong to story 2.1 (`models/canonical.py`, `models/common.py`), outside this epic. Disposition: none needed.

**A2. Duplication map — the root-locating constants and the version-extraction snippet.** `PACKAGE_ROOT = Path(__file__).resolve().parents[2]` appears in seven test modules (`tests/integration/test_install_smoke.py:20`, `tests/unit/test_import_contracts.py:21`, `test_repo_hygiene.py:13`, `test_tooling_config.py:6`, `test_version.py:9`, `test_workflow_pins.py:17`, and epic-2's `test_errors_taxonomy.py:34`), `REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]` in three of them plus `devtools/src/agentproof_devtools/check.py:25-27` (`parents[3]`). Each session re-derived it; no `conftest.py` exists yet (the spine's Structural Seed names one). The subprocess helper `_run` is written twice with different environment handling (`test_install_smoke.py:32-56`, `test_import_contracts.py:37-56`). The shell snippet `tr -d '\r' < packages/python/pyproject.toml | sed -nE 's/^version = "([^"]*)"$/\1/p'` is duplicated between `.github/workflows/ci.yml:129` and `release-draft.yml:37`. Disposition: **defer** to the next sweep (a `conftest.py` with `package_root`/`repository_root` fixtures is the obvious home; the spine already plans `tests/conftest.py`).

**A3. Size growth — inspected, no god-class.** Top code churn by `files.net`: `uv.lock` +746 (generated), `tests/unit/test_workflow_pins.py` +145/-10 in 1.4 then +196/-28 in 1.6 (303 lines, 25 tests at HEAD), `test_import_contracts.py` 232, `purity.py` 194, `check.py` 110. `test_workflow_pins.py` was opened: it is the one file two tickets grew, it stays single-purpose (every assertion is about the two workflow files), and the 1.4 review already relaxed its "only workflow, only job" invariants so 1.6 could add jobs (plan 1.4 triage row 4). Not a god-class. Disposition: none.

**A4. Pattern divergence — plan bookkeeping.** Plans 1.1, 1.2, 1.3, 1.5 record `review: 'quick'`, `lenses_ran: ['quick']` and a tabular Review Triage Log. Plan 1.4 (`story-ci-runs-...-plan.md:11-13`) and plan 1.6 (`story-ci-builds-...-plan.md:11-13`) have `review: ''`, `review_source: ''`, `lenses_ran: []` although both carry a dated quick-lens triage (1.4 as a table, 1.6 as a prose numbered list at lines 100-113). Plan 1.7 (`story-refactor-sweep-plan.md`) has `review: 'quick'` but **no** `lenses_ran` key, no `<frozen-after-approval>` block, and an empty Review Triage Log (line 69-70): either the sweep was not reviewed or the review was not recorded. The 1.6 implementer wrote "`lint-imports` 3 contracts KEPT" (plan 1.6 line 84) when the file had seven; the 1.7 orchestrator corrected it (line 94). Disposition: **fix now** for the record (bookkeeping only, three plan frontmatters), **process lesson** for the build loop: a plan whose triage log is empty while `review` is non-empty should not reach `done` unnoticed.

**A5. Spec-to-implementation reconciliation.**

- **A5.1 AD-19 claims bans the ruff list does not carry.** Spine AD-19 (`architecture-agentproof.md:225`): "`pickle`, `marshal`, `eval`, `exec`, and `yaml.load` without the safe loader are banned by the ruff list in AD-1." The implemented list (`packages/python/pyproject.toml:61-74`) bans exactly the AD-1 names (`os.environ`, `os.getenv`, `os.getcwd`, `os.stat`, `time`, `datetime.datetime.now/today`, `uuid`, `random`, `socket`, `subprocess`, `threading`, `asyncio`) and none of AD-19's. Story 1.3's R4 asked only for the AD-1 names, so the build matched its ticket; the spine overstates what exists. Also, `per-file-ignores` (`pyproject.toml:76-80`) exempts the shell packages from *all* of `TID251`, so a `yaml.load` ban placed there would not reach `io`/`loading`-adjacent shell code. Disposition: **spec reconciliation, proposed** (AD-19 wording) plus **defer** the bans to the epic that builds `loading.yaml_safe` (epic 2/3), with a separate rule-set so safety bans stay package-wide. Lenses adversarial and edge-case-hunter raised the same gap; verified against the pyproject text.
- **A5.2 `cli` contract forbids `agentproof.errors` while AD-2 and AD-15 make `errors` public API.** `.importlinter:82-101` forbids `agentproof.errors` from `agentproof.cli`; AD-2 says `cli` may import "`runner`, `io`, and the public API (AD-15)", and AD-15 lists "the `errors` module" in the public API. Plan 1.3 recorded the tension ("`cli` cannot import `agentproof.errors` directly; the error handler (AD-20) must take exceptions through the top-level public API", line 93) and deferred it to "the story that first hits one". Epic 3 story 3.1 (error handler, exit codes) will hit it. Disposition: **spec reconciliation, proposed**, owner Product Owner/architect, before 3.1 starts.
- **A5.3 No forbidden contract for `runner`.** AD-2: "`runner` may import `adapters` and `io`" outside the stack. `.importlinter` has forbidden contracts for `io`, `adapters`, `testing`, `cli`, `nothing-imports-cli`, and `core-imports-no-shell`, none with `agentproof.runner` as a source. `runner → testing` would pass `lint-imports` today (the layers contract does not list `testing`). Edge-case lens claim, verified against `.importlinter` and AD-2. Disposition: **defer** (one contract; add when `runner` gains code in epic 5).
- **A5.4 Wheel install proven on both runners at Python 3.12 only.** Epic R1: "installs into a clean virtual environment on Linux and Windows for Python 3.12, 3.13, 3.14, and 3.15". `ci.yml:92-135` `smoke` runs on both runners with `python-version: "3.12"` only; the eight `check` cells run `uv sync --locked` (editable install of the source tree), not the wheel. Disposition: **accept as-is or extend** — a decision for the Product Owner; recorded so the deviation is explicit.
- **A5.5 `main` has not received the epic.** `origin/main` = `2fad72b` ("Initial commit"); all four pull requests merged into `backlog` (`gh pr list`: base `backlog` for #1..#4). The protection rule on `main` (eight required `check` contexts, PR required, 0 approvals, admins not enforced; read back from `gh api .../branches/main/protection`) has never gated a merge; `CONTRIBUTING.md:46-48` describes a `backlog` → `main` pull request that has not happened; the `v0.1.0.dev0` draft (run 39902388238) was cut from `backlog` at `05ed167`. "`main` stays releasable" (C10) holds vacuously. Disposition: **fix now** (open the `backlog` → `main` pull request as part of closing the epic; decide whether `backlog` gets the same required contexts), owner maintainer.
- **A5.6 `AGENTS.md` lines overtaken by the epic.** `AGENTS.md:35-36` still read "TODO (EPIC A): once `pyproject.toml` exists…" and `:23` forbids writing a distribution name, while `pyproject.toml:9` carries the maintainer-approved provisional name. Already recorded in `deferred-work.md` (plan 1.1 quick-lens finding) and in plan 1.7's "left out" list as a `bmad-project-context` refresh. Disposition: **accept** here; the refresh is tracked.
- **A5.7 `.importlinter` is AD-2 "plus".** Epic R4 says the file carries the contracts "exactly as spine AD-2 lists them"; the file carries them plus a seventh contract `core-imports-no-shell` (`.importlinter:123-143`, added by the 1.3 review) and sets `allow_indirect_imports = True` on every forbidden contract, with the reasoning in plan 1.3 Design Notes (lines 125-127). Disposition: **accept** (recorded accepted deviation; the seventh contract strengthens AD-1 enforcement).

### Provenance and process (Phase 1 evidence)

**B1. History rewrite invalidated four plan baselines.** Plans 1.1, 1.2, 1.3, 1.5 record baselines `5a4dc1b`, `f12115c`, `8afabe2`, `5705d83`; `git merge-base --is-ancestor <sha> HEAD` is false for all four. Local branches `story/1-1-package-scaffold` (`f12115c`), `story/1-2-check-entry-point` (`8afabe2`), `story/1-3-import-contracts` (`5705d83`), `story/1-5-hygiene-files` (`22c8f48`) still point at the orphan lineage; `story/1-4-ci-workflow` (`457566e`) is fully merged. The live lineage from `401fef0` carries the same subjects, author dates, and trees (plus `README.md`), so the rewrite happened when the remote was created before story 1.4 (plan 1.4: "the GitHub remote must exist (the maintainer creates it as part of the hitl step)"). No plan records the rewrite. Disposition: **fix now** for the record (this document carries the mapping); **process lesson**: create the remote before the first baseline is recorded, or re-record `baseline_revision` when history is rewritten. Propose pruning the five stale local branches (git operation, maintainer).

**B2. Epic boundary blurred by story 2.1.** Story 2.1 (epic 2) was built, reviewed, and merged (PR #2, `39ab5e1`) between 1.4 done (`037860b`) and 1.6's commit (`c20b425`), inside this epic's 1.6 range; the 1.6 branch was rebased onto it (plan 1.6 line 94). Worktrees `D:/AgentProof-wt-2-2` and `D:/AgentProof-wt-2-3` (stories 2.2, 2.3) already exist at `05ed167`. The epic was therefore not closed before the next one started. Disposition: **process lesson** (no code effect; attribution was separated in Phase 1).

**B3. Two merge commits on `backlog` have no completed CI result.** `gh run list`: run 39901557156 on `39ab5e1` (merge of PR #2) and run 39902361915 on `cbecff1` (merge of PR #3) were **cancelled** because the ticket-mark commit pushed seconds later (`17c885a`, `05ed167`) superseded them under `concurrency.cancel-in-progress: true` (`ci.yml:33-35`). The superseding commits passed and differ only in `_bmad-output` files, so no code went unchecked, but the merge commits themselves carry no green run. Adversarial lens; verified against the run list. Disposition: **fix now** (cheap: `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`).

**B4. Session logs absent.** Recorded above; process-lesson analysis is narrowed to plan notes. The plans are unusually complete (each records tooling versions, deviations, and verification output), which is why B1 and A4 could still be derived.

### Diff-scope review (`bmad-review`: adversarial, edge-case-hunter, verification-gap)

`bmad-review` was invoked on the epic diff (`git diff 401fef0..38e55ff` over the epic-1 files, story 2.1's modules excluded), code lenses only, with the ticket boundaries weighted. The three lenses ran as independent subagents and returned 20, 20, and 4 findings. They are triaged here; the lens code is the provenance. Findings about story 2.1 files, and findings whose claim did not survive re-reading the source, were dropped.

**C1. [verified; fix now] `PYPI_*` secret names slip past the no-publish scan.** `tests/unit/test_workflow_pins.py:37-43`: the comment says "a `PYPI_*` secret … is not [fine]", but the whole-word pattern `\bPYPI\b` does not match `PYPI_TOKEN` or `PYPI_API_TOKEN` (`_` is a word character). Verified with `re`: `'PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}'` and `'PYPI_API_TOKEN'` match nothing. The 1.6 plan's mutation check (line 85) that proved this test bit was run **before** review finding 8 (line 111) switched to whole-word patterns, and was not re-run after. The `secrets.` scan (`:150-153`) still catches `${{ secrets.X }}`, so a secret reference is caught by the other test; a bare `PYPI_API_TOKEN` env name is not. Lens: edge-case-hunter. Guard: `(?<![A-Za-z0-9])PYPI(?![a-z])` or an explicit `PYPI_` pattern, and re-run the mutation.

**C2. [verified; fix now] `core-imports-no-shell` promises more than it checks.** `.importlinter:123` comment: "the pure core never reaches the effectful shell, directly or otherwise"; `:143` sets `allow_indirect_imports = True`, which makes it a direct-import check. Plan 1.3 Design Notes justify indirect allowance for the allow-list contracts, not for this one, and the layers contract does not list `io`/`adapters`/`testing`, so once `agentproof/__init__.py` re-exports a shell function (AD-15 `load_*`, `run_suite`) a core module doing `from agentproof import …` reaches the shell unreported. Lenses: adversarial, verification-gap (both). Guard: drop `allow_indirect_imports` on this one contract (the top-level back-edge `agentproof.* -> agentproof` can be `ignore_imports`) or reword the comment, and add the indirect negative test.

**C3. [verified; defer] The release build path is exercised only on a tag, and the sdist cannot drive uv.** `release-draft.yml:43` runs bare `uv build` (sdist, then wheel **from the sdist**); the suite builds `--wheel` and `--sdist` separately (`test_install_smoke.py:103,137`). Behavior check: bare `uv build` succeeded here ("Building wheel from source distribution…") and the wheel's member list equals the tree-built wheel's, so the path works today. Inside the unpacked sdist, `uv build --wheel` succeeds but `uv lock --check` fails: "`agentproof-devtools` references a workspace in `tool.uv.sources` … but is not a workspace member", because `pyproject.toml:34-38` still names the member that `:43-47` excludes from the sdist. Lenses: all three. Guard: an in-suite bare `uv build` test comparing wheel RECORDs; decide whether the sdist should carry `uv.lock` and the `[tool.uv]` tables at all. Owner: epic 9 story 5 (which replaces `release-draft.yml`).

**C4. [verified; defer to epic 9 story 5] Tag-triggered drafting is ungated.** `release-draft.yml` runs on any `v*` tag push with no `uv run check`, no main-ancestry check (and `main` is at the initial commit, A5.5), and its `gh release view` branch (`:55-56`) also uploads `--clobber` into an already **published** release. Lenses: adversarial, edge-case-hunter. The maintainer's decision (plan 1.6 Intent) scoped this workflow as a stand-in until epic 9; record the three gaps as requirements on `release.yml`.

**C5. [verified; fix now] `actions/checkout` keeps the job token in `.git/config`.** No `persist-credentials: false` on any checkout (`ci.yml:51,76,107,144`; `release-draft.yml:28`); in the release job the token has `contents: write`. Lens: adversarial. Guard: `with: persist-credentials: false` everywhere plus one assertion in `test_workflow_pins.py`.

**C6. [verified; fix now] Workflow-test scope.** `test_workflow_pins.py:22` globs `*.yml` only (a `*.yaml` workflow is unscanned); `_all_steps` (`:87-89`) sees step-level `uses:` only, never a job-level reusable-workflow `uses:`; no assertion forbids `pull_request_target`, `workflow_run`, or `issue_comment` triggers. Lens: adversarial. Small test additions.

**C7. [verified; defer] Audit coverage.** `audit` (`ci.yml:137-160`) runs only on PR/push and is not required; a new advisory against an unchanged lock triggers nothing; `pip-audit` on `ubuntu-latest` skips requirements whose markers do not match (e.g. `colorama ; sys_platform == 'win32'` in the export). Lenses: adversarial, edge-case-hunter. Guard: `schedule` + `workflow_dispatch`; audit per platform or in the OS matrix; a Dependabot config for `github-actions` and the lock (none exists under `.github/`).

**C8. [verified; spec reconciliation] The AD-1 ban is as narrow as AD-1's list.** `pyproject.toml:61-74` and `purity.py:45-65` implement the AD-1 names literally; `os` as a module (`os.listdir`, `os.remove`, `os.system`…), `shutil`, `tempfile`, `urllib`, `http`, `secrets`, `multiprocessing`, `datetime.date.today`, `datetime.datetime.utcnow`, and `Path.cwd/home/resolve/expanduser/rmdir/chmod/walk/...` pass. Lenses: adversarial, edge-case-hunter. The implementation matches the ticket (R4: "the stdlib names AD-1 forbids"); the gap is between AD-1's list and AD-1's intent ("never touches … the filesystem"). Propose widening the list in the spine and the pyproject together.

**C9. [verified; defer] `check.py` leftovers.** The `lint-imports` skip placeholder from 1.2 (`check.py:50-55`) survived 1.3 and the 1.7 sweep: a deleted `.importlinter` makes the step a skipped pass (AGENTS.md: missing evidence is `error`, never `passed`); it is mitigated because `test_repository_importlinter_exists_so_lint_imports_is_not_skipped` (`test_check_entry_point.py:145-151`) then fails in the `pytest` step. A missing tool binary raises an uncaught `FileNotFoundError` traceback at `:95` instead of a `failed: <step>` line. Lenses: adversarial, edge-case-hunter.

**C10. [verified by code reading; defer] `purity.py` edges.** `SUPPRESSION_MARKER in line` (`:122`) matches the marker inside a string literal on the same line; `read_text(encoding="utf-8")` (`:140`) is not guarded, so a BOM or non-UTF-8 core file ends in `SyntaxError`/`UnicodeDecodeError` outside the documented exit-2 path (`:181-183` catches `SyntaxError` only). Lenses: adversarial, edge-case-hunter.

**C11. [verified; fix now] The SECURITY placeholder is asserted literally.** `test_repo_hygiene.py:117-119` asserts `<security contact to be filled by the maintainer>` is present in `SECURITY.md:17`, so filling in the real channel breaks the gate; `CODE_OF_CONDUCT.md:63` carries the same placeholder. Lens: adversarial. Guard: accept either the placeholder or a real contact; the maintainer fills the channel before the first public tag.

**C12. [verified; defer] Hygiene assertions are textual.** `.pre-commit-config.yaml:18-23` scopes both hooks with `files: ^packages/python/` but `test_repo_hygiene.py:130-138` never reads `files`; `.gitignore`'s "examples stay tracked" is checked only as "no rule contains the substring `examples`" (`:58-60`); no `.env`/`*.pem`/`*.key` patterns; `**/tests/golden/** text eol=lf` (`.gitattributes:7`) would normalise a future binary golden. Lenses: adversarial, verification-gap, edge-case-hunter. The adversarial claim that the "never rewrites" comment is wrong is **not kept as written**: the comment (`:21`) sits under `ruff-check`, which it describes correctly; `ruff-format` rewriting is the hook's purpose.

**C13. [verified; defer] Workflow robustness.** No `timeout-minutes` on any job (the gate spawns `uv build`/`uv pip install` subprocesses with 600 s timeouts each, `test_install_smoke.py:21`); the version `sed` reads the whole `pyproject.toml` and would mis-extract on a second `version =` line or a `dynamic` version; `gh release view` failing for a non-404 reason falls into `create`. Lenses: edge-case-hunter, adversarial.

**C14. [accept] Decisions the lenses re-raised that the plans already own.** `mypy --strict` on `src` only (story 1.2 criterion 3; devtools and tests were type-checked by hand in plans 1.3 and 1.6); branch protection with administrators not enforced and zero approvals (maintainer decision, plan 1.4 Intent; CONTRIBUTING states it); the `agentproof` no-arguments exit code (story 3.1 owns exit codes; plan 1.1 noted it); `PackageNotFoundError` on an uninstalled import (uv always installs). Recorded so they are not re-flagged.

**C15. [defer] Low-frequency correctness.** Wheel filename assertion assumes a PEP 440-normalized `version` (`test_install_smoke.py:107`; `0.1.0-rc1` would be normalised to `0.1.0rc1`); `Step` with empty `commands` or a `skip_reason` returning `""` is reported oddly (`check.py:90-98`). Lens: edge-case-hunter.

### Wins the evidence confirms

- The gate is one definition, called the same way locally and in CI: `check.py` builds the step list; `ci.yml:62-69` runs `uv sync --locked` then `uv run check` and nothing else (asserted by `test_check_stage_is_exactly_one_uv_run_check_step_in_the_package`).
- Every contract bites: `test_import_contracts.py` injects a violation per contract and per banned name in a temporary copy, and the red-run proof on PR #1 showed the gate order on real runners (runs 39897319496 at `ruff check`, 39897818215 at `pytest`, then 39897969954 green).
- Review passes caught real defects before merge in every reviewed story (plan 1.3's seventh contract; plan 1.6's CRLF smoke fix, tag guard, `pip-audit` pin), and the plans record the evidence a later reader needs.

## Behavior verification

Exercised end to end on this Windows machine (uv 0.13.5, project venv CPython 3.12) and read from GitHub, read-only:

- `uv run check` in `packages/python` → `==> ruff check` All checks passed (purity silent); `==> ruff format --check` 36 files already formatted; `==> mypy --strict` Success: no issues found in 18 source files; `==> lint-imports` Analyzed 18 files, 2 dependencies, 7 contracts KEPT, 0 broken; `==> pytest` **250 passed**; exit 0. Caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`) deleted afterwards from the package tree; `git status` unchanged.
- `uv run agentproof version` → `0.1.0.dev0`, exit 0. `uv run agentproof --help` → Commands panel lists `version` only.
- `uv build --out-dir <scratchpad>/dist` → `agentproof-0.1.0.dev0.tar.gz` and `agentproof-0.1.0.dev0-py3-none-any.whl`, the wheel built from the sdist ("Building wheel from source distribution…"). Wheel members: 18 `agentproof/` sources (including story 2.1's `constants.py`, `errors.py`, `models/canonical.py`, `models/common.py`) plus four `dist-info` files; nothing from `devtools` or `tests`. Sdist members: `src/agentproof/**`, `pyproject.toml`, `uv.lock`, `.gitignore`, `PKG-INFO`; no `devtools/`, no `tests/`.
- Fresh venv (`uv venv --python 3.12`), `uv pip install <wheel path>`, `agentproof.exe version` → `0.1.0.dev0`, exit 0; installed set is `agentproof` plus the four runtime dependencies and their transitive closure (15 distributions).
- Unpacked sdist: `uv build --wheel` succeeds; `uv lock --check` fails on the missing `agentproof-devtools` workspace member (finding C3).
- GitHub: run 39903309802 on HEAD `38e55ff` (push to `backlog`) → all twelve jobs `success` (eight `check`, `wheel`, `smoke (ubuntu-latest)`, `smoke (windows-latest)`, `audit`). Branch protection on `main`: the eight `check (<os>, <python>)` contexts, strict, PR required with 0 approvals, `enforce_admins: false`. Release-draft run 39902388238 on tag `v0.1.0.dev0` at `05ed167` → `success`; `gh release list` and the tags API are now empty, consistent with the plan's recorded deletion of the test draft and tag.
- Not exercised in this run: a Linux checkout (relied on the CI runs above); the draft release's asset list (deleted before this run; plan 1.6 line 96 records `isDraft: true` with the `.whl` and `.tar.gz`); the pre-commit hooks; a red run.

## Previous-retro follow-through

No previous retrospective file exists: this is the first epic of the initiative, and there is no sibling epic folder before `epic-01` in the `epics` order. Nothing to follow through on. (This is "no previous file", not "no outstanding items".)

## Action items

All items are **proposed**; none was applied by this run. "Dev loop" means a story-shaped change through `bmad-build`; "PO" is the Product Owner (ticket edits); "maintainer" is the repository owner (`kamranhaq21`).

| # | Action | Kind | Owner | Source |
| --- | --- | --- | --- | --- |
| 1 | Fix the `PYPI` whole-word pattern so `PYPI_*` names match again, re-run the plan 1.6 mutation check, and widen `test_workflow_pins.py` to `*.yaml`, job-level `uses:`, and a forbidden-trigger assertion. | Remediation (dev loop, small) | dev loop | C1, C6 |
| 2 | Reconcile `.importlinter` with AD-2/AD-15: decide `allow_indirect_imports` on `core-imports-no-shell` (or reword its comment and add the indirect negative test); resolve the `cli` → `errors` tension before epic 3 story 3.1; add a `runner` forbidden contract when `runner` gains code. | Spec reconciliation + remediation | PO / architect, then dev loop | C2, A5.2, A5.3 |
| 3 | Amend AD-19 so it stops claiming `pickle`/`marshal`/`eval`/`exec`/`yaml.load` are banned today, and schedule the bans (as a rule-set that reaches the shell packages) in the loading story of epic 2/3. | Spec reconciliation + remediation | PO, then dev loop | A5.1, C8 |
| 4 | CI hardening: `persist-credentials: false` on every checkout, `cancel-in-progress` only for `pull_request`, `timeout-minutes` on every job; one assertion each. | Remediation (dev loop, small) | dev loop | C5, B3, C13 |
| 5 | Relax `test_security_policy_names_a_reporting_channel_placeholder` to accept a real contact, then fill the SECURITY and CODE_OF_CONDUCT contacts. | Remediation + maintainer input | dev loop; maintainer | C11 |
| 6 | Open the `backlog` → `main` pull request as the epic's closing step; decide whether `backlog` carries the same required contexts and record the decision in CONTRIBUTING. | Process / maintainer decision | maintainer | A5.5 |
| 7 | Prune the stale local branches `story/1-1-package-scaffold`, `story/1-2-check-entry-point`, `story/1-3-import-contracts`, `story/1-5-hygiene-files` (orphan lineage) and `story/1-4-ci-workflow` (merged); treat this document's baseline mapping as the record, or re-point the four `baseline_revision` values. | Process (git operation; not applied here) | maintainer | B1 |
| 8 | Carry into epic 9 story 5 (`release.yml`): gate the tag build on `uv run check` and main ancestry; never upload into a published release; add an in-suite bare `uv build` test; decide whether the sdist ships `uv.lock` and the `[tool.uv]` tables. | Requirements on a later story | PO | C3, C4 |
| 9 | Schedule the audit (`schedule` + `workflow_dispatch`), audit per platform, and add `.github/dependabot.yml` for actions and the lock. | Remediation (dev loop) | PO → dev loop (epic 9) | C7 |
| 10 | Decide whether R1's "installs … for Python 3.12 to 3.15" is met by the editable `check` cells or needs the `smoke` matrix extended to 3.13–3.15; record the decision in the epic file or a ticket. | Spec reconciliation | PO | A5.4 |
| 11 | Plan bookkeeping: set `review`/`lenses_ran` on plans 1.4 and 1.6; record or run the review of plan 1.7 (its triage log is empty). Process lesson for the build loop: `done` with `review` set and no triage entry should be flagged. | Process | PO / build loop | A4 |
| 12 | Widen the AD-1 list in the spine and `pyproject.toml` together (`os`, `shutil`, `tempfile`, `urllib`, `http`, `secrets`, `multiprocessing`, `datetime.date.today`, `datetime.datetime.utcnow`, the remaining `Path` effects) with a parametrized purity test per name. | Spec reconciliation + remediation | architect, then dev loop | C8 |
| 13 | Next refactor sweep: `tests/conftest.py` with `package_root`/`repository_root` fixtures and one subprocess helper; share the version-extraction step between the two workflows; remove the `lint-imports` skip placeholder; guard `purity.py` reads. | Remediation (sweep) | dev loop (epic 2 sweep) | A2, C9, C10 |
| 14 | `bmad-project-context` refresh of `AGENTS.md` (the two "TODO (EPIC A)" lines and the provisional-name line), already in `deferred-work.md`. | Process | maintainer via `bmad-project-context` | A5.6 |

Process lessons (upstream, not tied to one fix): create the remote before the first plan baseline is recorded (B1); close an epic before the next one starts work (B2); re-run a mutation proof after a review changes the guard it proved (C1); a review fix that narrows a contract must also narrow the comment that documents it (C2).

## Acceptance verdict

**Machine verdict: accepted-with-open-items.** Criteria: **declared** (the epic file's Done when).

Evidence per criterion:

1. "`uv run check` passes on a fresh clone on Windows and on Linux CI with an empty-but-structured package (R3, R4)" — met: local `uv run check` exit 0 with 250 passed; run 39903309802 green on all eight `check` cells; plan 1.4 line 89 records the fresh-venv `uv sync --locked` proof.
2. "CI is green on the full matrix and the wheel installed into a clean venv prints its version (R1, R2, R5)" — met: twelve jobs green on HEAD; local fresh-venv install printed `0.1.0.dev0`; plan 1.6 line 95 records the Windows smoke log. Open item A5.4 (smoke at 3.12 only) is a scope question, not a failure.
3. "`lint-imports` fails when a test commit adds `import agentproof.cli` inside `agentproof.models` (R4)" — met: `test_upward_import_from_models_to_cli_breaks_the_contracts` (`test_import_contracts.py:124-131`) is in the 250 passing tests; plan 1.3 line 97 records the end-to-end run through `run_steps`.
4. "The repository has every hygiene file in R5 and `docs/decisions/` holds ADR-001 to ADR-020 (R5, R6)" — met: `.gitattributes`, `.gitignore`, `.editorconfig`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` tracked; `docs/decisions/` holds 23 files (`0000`, `0001`–`0020`, `0021`, `README.md`); `test_repo_hygiene.py` asserts them.
5. "Production delivery: a tagged pre-release wheel builds in CI and is attached to the GitHub release draft without publishing to PyPI (R1, C9)" — met on the evidence available: release-draft run 39902388238 `success` on tag `v0.1.0.dev0`; plan 1.6 line 96 records `isDraft: true` with both assets; no publish step exists (`test_no_workflow_publishes_to_a_package_index`); the draft and tag were deleted afterwards, so the asset list is not re-verifiable now.

No ticket is unfinished (`pending_tickets` empty). No blocking finding stands: C1 weakens one of two overlapping guards, C2 and A5.1 are documentation-stronger-than-enforcement gaps that bite only when later epics add code, and A5.5 is a process gap in how the epic landed, not in what it built. The open items are the deferred findings routed above (action items 1 to 14). This verdict was rendered without a human decision; a human decision overrides it.

## Open questions

- Does the Product Owner read R1's "for Python 3.12, 3.13, 3.14, and 3.15" as satisfied by the editable `check` cells, or must the wheel smoke run on every version? (A5.4) A "must" turns action item 10 into a dev-loop story before epic 9.
- Should `backlog` be the protected integration branch, or should `backlog` → `main` merges happen at every epic close? (A5.5) The answer decides whether the protection rule on `main` is ever load-bearing before release.
- Is the `cli` → `errors` import to be allowed directly (amend `.importlinter`) or routed through `agentproof.__init__` as plan 1.3 assumed? (A5.2) Epic 3 story 3.1 cannot start cleanly without the answer.
- Should the sdist carry `uv.lock` and the `[tool.uv.workspace]`/`[tool.uv.sources]` tables when it no longer carries the member they name? (C3)
- Were the 1.7 sweep's changes reviewed? The plan says `review: 'quick'` and records no triage. (A4)

## Assumptions

Headless choices made without the user:

- **Epic resolution:** `-H epic-01-repository-foundation-and-ci` matched the `epics` entry by slug; `find 1.1` gave `epic_file` whose parent is `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/`; `status <folder>` returned seven rows, all `status: done`, `state: done`; `pending_tickets` empty, so no unfinished-ticket confirmation was needed or invented.
- **Going-in concerns:** none were invited (headless); the Phase 2 weighting of ticket boundaries came from the orchestrator's invocation, not from a user.
- **Range construction:** four plan baselines are unreachable from HEAD; I assumed the live-lineage commits with identical subjects, dates, and trees are the same builds (verified by `git diff` showing only `README.md`) and measured both lineages rather than declaring the ranges unestablishable. The 1.7 range end was inferred as HEAD `38e55ff` because no later epic-1 commit exists. Story 2.1's commits inside the 1.6 range were attributed to epic 2 by subject and plan.
- **Diff-scope review:** `bmad-review` was invoked with the three code lenses; its findings were treated as unverified reports and each kept finding was re-checked against the file, the run list, or a command (C1 by `re`, C3 by unpacking the sdist, B3 by `gh run list`). Two lens claims were dropped or narrowed (the pre-commit "never rewrites" comment reading; findings on story 2.1 files).
- **Behavior check scope:** `uv run check`, `agentproof version`, `uv build`, a fresh-venv wheel install, and an sdist unpack were run locally; Linux behavior was taken from the GitHub run records; the draft release could not be re-inspected because it was deleted as planned.
- **Machine verdict:** `accepted-with-open-items`, rendered on the evidence alone with no human decision; every open item is routed above. Each of the fourteen proposed action items and their owners is a proposal, not an assignment.
- **No team discussion** (Phase 3) ran, as the headless mode requires.
- **Writes:** this file only. No `tickets.py mark`, no edit to the epic file, any plan, or any story file; tool caches created by the behavior check were deleted from `packages/python` (not from `.venv`), and the built artifacts live in the session scratchpad.
