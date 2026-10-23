- source_plan: `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/tickets/story-package-scaffold-installs-and-prints-its-version-plan.md`
  summary: AGENTS.md says no distribution name may be written before the OQ-1 decision, but the maintainer approved a provisional `name = "agentproof"` in pyproject.toml; reword the AGENTS.md policy line to allow the provisional name and forbid only install commands and publishing.
  evidence: Quick lens finding on 2026-10-22; the frozen plan Intent records the maintainer decision; a fix edits an agent-context file, so it goes through a bmad-project-context refresh rather than this build.
  status: closed 2026-10-23 by the bmad-project-context refresh after epic 1; the AGENTS.md
    policy line now allows the provisional name and forbids publishing and public
    install-by-name commands, and docs/decisions/0000-distribution-name.md quotes the new
    wording.
