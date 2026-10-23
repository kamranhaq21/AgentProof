---
id: 4
type: story
title: "CI runs the check entry point on Linux and Windows across Python 3.12 to 3.15"
parent: epic-01-repository-foundation-and-ci
covers: [R3, R5]
after: [2, 5]
hitl: true
risk: medium
refined: true
---

# CI runs the check entry point on Linux and Windows across Python 3.12 to 3.15

## Description

Every later story's claims about determinism and portability are only true if both platforms run the same check. A person enables branch protection on `main` so the check is required (hitl).

## Requirements

1. **Matrix** (R3; spine AD-17)
   **Given** `.github/workflows/ci.yml`
   **When** a pull request opens
   **Then** jobs run on `ubuntu-latest` and `windows-latest` for Python 3.12, 3.13, 3.14, and 3.15, each installing uv, syncing, and running `uv run check` as the only check step.
2. **Pinned and least privilege** (R5; spine AD-17)
   **Given** the workflow file
   **When** it is read
   **Then** every `uses:` is pinned to a full commit SHA with a version comment, and `permissions` is `contents: read` at the top level.
3. **Red on failure** (R3)
   **Given** a branch with a failing test
   **When** CI runs
   **Then** every matrix job fails and the PR cannot merge once branch protection is on.
4. **Branch protection** (initiative C10)
   **Given** the repository settings
   **When** the maintainer completes the hitl step
   **Then** `main` requires the CI check and a pull request; the setting is recorded in CONTRIBUTING.

## Boundaries

- No wheel build or publish jobs (story 6, epic 9).
- Must not change: the check entry point.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, Stack
- spec — PROJECT_SPEC.md, section 9 CI

## Notes

- Files: `.github/workflows/ci.yml`, `CONTRIBUTING.md` (branch rule line, written here if story 5 has not landed).
- Tests: the workflow itself on a test PR; `tests/unit/test_workflow_pins.py` asserting every `uses:` is a 40-character SHA.
- Depends on: story 2 and story 5 (`.gitattributes` and CONTRIBUTING must exist before the Windows leg checks out and before the branch rule is documented); the GitHub remote must exist (the maintainer creates it as part of the hitl step).
- Risk: Python 3.15 wheels for a dependency may lag; if a job fails only on 3.15 for that reason, mark it `continue-on-error` with a dated note and an issue.
- Done when: a test PR shows eight green jobs and the merge button requires them.
