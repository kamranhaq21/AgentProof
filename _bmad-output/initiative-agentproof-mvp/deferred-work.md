- source_plan: `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/tickets/story-package-scaffold-installs-and-prints-its-version-plan.md`
  summary: AGENTS.md says no distribution name may be written before the OQ-1 decision, but the maintainer approved a provisional `name = "agentproof"` in pyproject.toml; reword the AGENTS.md policy line to allow the provisional name and forbid only install commands and publishing.
  evidence: Quick lens finding on 2026-10-22; the frozen plan Intent records the maintainer decision; a fix edits an agent-context file, so it goes through a bmad-project-context refresh rather than this build.
  status: closed 2026-10-23 by the bmad-project-context refresh after epic 1; the AGENTS.md
    policy line now allows the provisional name and forbids publishing and public
    install-by-name commands, and docs/decisions/0000-distribution-name.md quotes the new
    wording.

- source: `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci-retrospective.md` (2026-10-23, verdict accepted-with-open-items)
  summary: `.importlinter` forbids `cli -> errors` although AD-2/AD-15 make `errors` public API, and no `runner` forbidden contract exists (AD-2 lets runner import adapters and io only); reconcile when story 3.1 first hits it.
  owner: story 3.1 (CLI skeleton); architect decides the contract wording.
- source: epic-01 retrospective, finding 4
  summary: AD-19 says pickle/marshal/eval/exec/yaml.load are banned by the AD-1 ruff list, but pyproject's TID251 list does not name them and shell packages are exempt; add the bans with a rule set that reaches shell packages, and amend AD-19's wording.
  owner: story 3.2 (safe YAML loader) for the bans; architecture update for AD-19.
- source: epic-01 retrospective, finding 7 and item 8
  summary: release-draft builds on any tag without gating on the check gate or `main` ancestry, would clobber assets of a published release, and the sdist cannot drive `uv lock --check` because pyproject names the excluded devtools member; decide uv.lock-in-sdist and add an in-suite bare `uv build` test.
  owner: epic 9 story 5 (publishing pipeline).
- source: epic-01 retrospective, items 9 and 10
  summary: the dependency audit runs only on PR/push, Linux-marker-only, with no schedule or dependabot; smoke installs the wheel at Python 3.12 only while epic R1 says 3.12 to 3.15.
  owner: epic 9 (schedule, per-platform audit, dependabot); PO decides the R1 smoke matrix scope.
- source: epic-01 retrospective, items 12 and 13
  summary: the AD-1 ban list is as narrow as AD-1's literal list (os module, shutil, tempfile, Path.resolve/cwd pass); the next sweep should add conftest fixtures for PACKAGE_ROOT/REPOSITORY_ROOT (duplicated in seven test files and check.py), a shared subprocess helper, and the shared version step.
  owner: architect (AD-1 list, spine and pyproject together); the epic-2 refactor sweep.
- source: epic-01 retrospective, finding 6
  summary: `backlog` is not protected; decide whether to protect it now that `backlog -> main` pull requests are opened at each epic close.
  owner: maintainer.
- source: story 2.4 quick-lens review, 2026-10-23, finding 7
  summary: `SuiteDefaults`, `FixtureDefaults`, `CompareDefaults`, and `RedactDefaults` (story 2.2) carry no `Field(description=...)`, so the generated Report and Suite schemas have $defs without descriptions; and `Timestamp` exports bare `type: string` with no `pattern`, so an external validator accepts naive timestamps the models reject. Both must be fixed before the schemas are published.
  owner: story 2.5 (generated JSON Schemas): add the descriptions to the 2.2 models and an ECMA-anchored RFC 3339 pattern via json_schema_extra on the Timestamp alias.
- source: story 3.2 quick-lens review, 2026-10-23, finding 7
  summary: the YAML loader fills `Violation.field` with `<line>:<column>` while `errors.py` documents it as the dotted model path; story 3.3 (parse_suite) mixes both in one list, so it must fix the convention (for example a separate `line` on Violation, or a documented rule that a field matching `\d+:\d+` is a position) and update the errors.py docstring.
  owner: story 3.3.
