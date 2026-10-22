---
id: 6
type: story
title: "CI builds the wheel, smoke-installs it, and audits dependencies"
parent: epic-01-repository-foundation-and-ci
covers: [R1, R5]
after: [4]
hitl: false
risk: low
refined: true
---

# CI builds the wheel, smoke-installs it, and audits dependencies

## Description

The install path users will take is exercised on every pull request, and a tag produces a draft release with the wheel attached without publishing anywhere. Epic 8's example workflow and epic 9's docs test both install from this job's artifact.

## Requirements

1. **Build and smoke** (R1; spine AD-17)
   **Given** the CI workflow
   **When** it runs
   **Then** a job builds the wheel with `uv build`, uploads it as an artifact named `wheel`, installs it into a fresh venv on Linux and on Windows, and runs `agentproof version` with exit 0.
2. **Dependency audit** (R5)
   **Given** the same workflow
   **When** it runs
   **Then** `pip-audit` runs against the locked dependencies and fails the job on a known vulnerability.
3. **Draft release on tag** (R1; initiative C9)
   **Given** a tag matching `v*`
   **When** the workflow runs
   **Then** a draft GitHub release is created with the wheel attached, and nothing is published to PyPI.
4. **Pinned actions** (R5)
   **Given** the new jobs
   **When** they are read
   **Then** every action is SHA-pinned and the release job has `contents: write` only.

## Boundaries

- No PyPI publish (epic 9 story 5).
- Must not change: the check stage from story 4.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, Deployment and environments
- spec — PROJECT_SPEC.md, section 13.1

## Notes

- Files: `.github/workflows/ci.yml` (build, smoke, audit jobs), `.github/workflows/release-draft.yml`.
- Tests: the workflow on a PR and on a test tag; `tests/unit/test_workflow_pins.py` extended.
- Depends on: story 4. Risk: low. The draft-release workflow here is replaced by epic 9 story 5's `release.yml`; that story deletes `release-draft.yml`.
- Done when: a PR shows the smoke jobs green on both platforms and a test tag yields a draft release with the wheel.
