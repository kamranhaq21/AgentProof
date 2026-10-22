---
type: epic
title: "Security hardening and documentation: a stranger installs, runs, and understands the limits, and 0.1.0 is published under the decided name"
parent: initiative-agentproof-mvp
covers: ["R21", "R23", "R25", "R27", "C8", "C9", "C10"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: high
---

# Security hardening and documentation

## Description

Launch readiness: the reference docs for the Suite format, Assertions, Traces, CLI, and security limits built on the fixed statement constants; the README quick start whose commands are extracted and executed in CI against the built wheel; the remaining hardening tests for paths, symlinks, device names, and atomic-write failure; the security policy and review; the release workflow with trusted publishing gated on the name and license decisions; and three timed external tester runs.

## Outcome

For an external developer, the package installs and demonstrates a regression without live help, and the README never claims more than a test proves (PRD SM-1, SM-C3; spec Week 4 exit gate).

## Requirements

- R1 (parent R21): `docs/` holds getting-started, suite-format, assertions, traces, cli, and security pages; every claim about determinism, Replay, Redaction, and capture uses `constants.STATEMENTS`; the §5 limits appear in the README.
- R2 (parent R21): fenced blocks tagged `agentproof-doctest` in README and docs are extracted by `tests/e2e/test_docs.py` and executed against the wheel built in the same CI run, never against PyPI by name.
- R3 (parent R25, R27): tests cover a Scenario id with `..`, a symlink out of the Output Directory, Windows reserved names, a locked target on Windows, and an oversized Trace, each ending in the documented exit code; `pip-audit` runs in CI.
- R4 (parent C8, C10): SECURITY.md states the reporting process; a security review checklist covering spec §11.1 is completed and recorded in `docs/decisions/`.
- R5 (parent C9): the release workflow publishes with trusted publishing on a tag, only after the name (OQ-1) and license (OQ-2) decisions are recorded and the LICENSE file exists; the spec §13.3 checklist is completed.
- R6 (parent R21): three external testers each reach a passing and a failing run from the README in under five minutes, with times recorded.
- R7 (parent R23): `report --format junit` and the viewer remain absent and documented as deferred.

## Constraints

- Covered parent constraints: C8 (nothing hosted, no telemetry, no more than one Adapter is documented or published), C9 (no install command or LICENSE before the decisions), C10 (release from `main` through pull requests); the lines below say how.
- Spine AD-17: docs commands cannot drift from CI.
- Spine AD-20: statements are constants, reused.
- C9: no publish before the decisions.

## Done when

- The docs test executes every tagged block green on Linux and Windows CI (R2).
- The hardening tests pass on both platforms (R3).
- The release workflow publishes 0.1.0 to PyPI under the decided name from a tag, and a clean `pip install <name>` on a fresh machine runs the quick start (R5).
- Three tester records exist with times under five minutes (R6).
- SECURITY.md, the review record, and the LICENSE file are committed (R4, R5).

## Boundaries

- No new product behavior; a bug found by testers is a `bug` ticket in the backlog, not a story here.
- Must not change: public API names or Schema Versions.
- Touch point: PyPI project and trusted publisher configuration; owner: this epic, hitl.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-14, AD-17, AD-19, AD-20, Deployment and environments
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-33, NFR-2, NFR-5, NFR-6, SM-1
- spec — PROJECT_SPEC.md, sections 11, 13.3, 14.1

## Notes

- Decision (2026-10-22): tracer bullet is story 1, the README quick start with its doctest extraction running against the wheel; it proves the docs-to-CI mechanism before the reference pages exist.
- Open question: OQ-1 and OQ-2 gate story 5; the entry carries the unknown so it cannot start unsettled.
- Assumption: external testers are recruited by the maintainer (hitl in story 6).
