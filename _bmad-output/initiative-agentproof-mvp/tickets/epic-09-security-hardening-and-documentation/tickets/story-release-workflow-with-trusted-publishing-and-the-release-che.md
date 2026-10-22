---
id: 5
type: story
title: "Release workflow with trusted publishing and the release checklist"
parent: epic-09-security-hardening-and-documentation
covers: [R5]
after: [1, 2, 4]
hitl: true
risk: high
refined: true
---

# Release workflow with trusted publishing and the release checklist

## Description

Publishing 0.1.0. Gated on the name decision: the PyPI name `agentproof` is taken by another agent-testing package, so this story cannot start until OQ-1 is recorded. A person configures the PyPI trusted publisher and cuts the tag (hitl).

## Requirements

1. **Name recorded** (R5; initiative C9; OQ-1)
   **Given** `docs/decisions/0000-distribution-name.md`
   **When** this story starts
   **Then** it names the decided distribution name, `pyproject.toml` uses it, the README install line uses it, and the import name stays `agentproof`.
2. **Release workflow** (R5; spine AD-17, Deployment)
   **Given** `.github/workflows/release.yml`
   **When** a `v*` tag is pushed
   **Then** it builds the wheel and sdist, runs the check entry point and the acceptance test against them, and publishes through PyPI trusted publishing with `id-token: write` and no stored secret; actions are SHA-pinned.
3. **Checklist** (R5; spec §13.3)
   **Given** `.github/RELEASE_CHECKLIST.md`
   **When** 0.1.0 is cut
   **Then** every item of spec §13.3 is checked with evidence, including the clean-install quick start on a machine that never had the repository.
4. **Published** (R5)
   **Given** the `v0.1.0` tag
   **When** the workflow completes
   **Then** `pip install <decided name>` on a fresh machine runs the README quick start green, and the GitHub release holds the notes and the wheel.

## Boundaries

- Must not change: Schema Versions or the public API; a last-minute change is a new patch release.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-17, Deployment and environments
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, OQ-1, H7
- spec — PROJECT_SPEC.md, sections 13.1, 13.3

## Notes

- Files: `.github/workflows/release.yml` (replaces epic 1 story 6's `release-draft.yml`, which this story deletes so only one tag-triggered workflow exists), `.github/RELEASE_CHECKLIST.md`, `docs/decisions/0000-distribution-name.md`, `pyproject.toml`, `README.md`.
- Tests: the release workflow on a release-candidate tag to Test PyPI first; the acceptance test against the published package.
- Depends on: stories 1, 2, 4. Risk: high; a published name cannot be changed.
- Hitl steps: decide OQ-1, configure the trusted publisher, push the tag.
- Done when: criteria 1 to 4 pass.
