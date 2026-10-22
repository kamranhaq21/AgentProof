---
type: epic
title: "GitHub Actions example: a copy-paste workflow blocks a pull request on a failing Scenario and keeps the Reports as artifacts"
parent: initiative-agentproof-mvp
covers: ["R20", "R29"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: medium
---

# GitHub Actions example

## Description

The workflow a user copies: it checks out, installs a supported Python and AgentProof, runs the Suite with the Fixture Agent and no secrets, renders the HTML Report, uploads the Output Directory on success and failure, and fails the job on a non-zero exit. The same workflow runs in this repository's own CI against the example, and the end-to-end acceptance script from spec §12.4 runs beside it.

## Outcome

For an engineering lead, the demo pull request turns red on a declared Assertion failure and the uploaded HTML Report explains it (PRD UJ-1 first half, SM-2).

## Requirements

- R1 (parent R20): `.github/workflows/agentproof-example.yml` performs the six steps with SHA-pinned actions and `permissions: contents: read`, uploads the Output Directory including `report.html` with `if: always()`, and fails the job when `agentproof run` exits non-zero.
- R2 (parent R20): `docs/integrations.md` explains running with saved Traces and the Fixture Agent so CI needs no model credentials and states that uploaded artifacts are visible to anyone with read access to the repository's Actions.
- R3 (parent R29): `tests/e2e/test_acceptance.py` runs the spec §12.4 chain against the built wheel in a clean venv: install, `init`, passing run, failing run with non-zero exit, Report generation, Replay without credentials, Comparison of a changed run against its Baseline, and a grep of every artifact for the planted secret.

## Constraints

- Spine AD-17: pinned SHAs, least privilege; the workflow reuses the built wheel from the same CI run.
- Spine AD-18: no secrets, no services.

## Done when

- A pull request in this repository that changes the example Suite to make a Scenario fail shows the example workflow red with the artifact attached (R1).
- The acceptance test passes on Linux and Windows CI (R3).
- The integrations page's commands are executed by the docs test from epic 9 once it exists (R2).
- Production delivery: the workflow file is the one the README links to (R1).

## Boundaries

- No release workflow (epic 9); no project-CI changes beyond adding the two jobs.
- Must not change: the project's own `ci.yml` check stage from epic 1.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, AD-18, Deployment and environments
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-32, UJ-1, SM-2
- spec — PROJECT_SPEC.md, sections 6.8, 12.4

## Notes

- Decision (2026-10-22): tracer bullet is story 1, the example workflow running against the scaffolded Suite in this repository's CI.
- Decision (2026-10-22): three stories, so no refactor sweep.
