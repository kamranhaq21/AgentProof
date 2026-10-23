---
id: 5
type: story
title: "Repository hygiene files and decision records"
parent: epic-01-repository-foundation-and-ci
covers: [R5, R6]
after: [1]
hitl: false
risk: low
refined: true
---

# Repository hygiene files and decision records

## Description

The files that keep a Windows-developed, Linux-tested repository honest: line-ending protection for golden files, ignores for local traces and environments, editor defaults, pre-commit, contributor rules, the security policy stub, and the ADRs moved to where the spec says decisions live.

## Requirements

1. **Golden files stay LF** (R5; spine AD-17)
   **Given** `.gitattributes` with `tests/golden/** text eol=lf` and `*.json text eol=lf` under `schemas/`
   **When** a fresh clone is made on Windows with `core.autocrlf=true`
   **Then** files under `tests/golden/` have LF endings.
2. **Ignores** (R5; initiative C10)
   **Given** `.gitignore`
   **When** it is read
   **Then** it ignores `.venv/`, `dist/`, `build/`, `*.egg-info/`, `agentproof-output/`, `_bmad/custom/*.user.toml`, and `.agentproof-*` temp files, and does not ignore `examples/**/traces/`.
3. **Contributor documents** (R5, R2)
   **Given** CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, `.editorconfig`, `.pre-commit-config.yaml`
   **When** they are read
   **Then** CONTRIBUTING states `uv run check`, the branch and PR rule, the 0.x pre-1.0 API policy, and the rule that a new runtime dependency needs an ADR; SECURITY names a reporting channel placeholder the maintainer fills; pre-commit runs ruff.
4. **Decision records** (R6)
   **Given** `docs/decisions/`
   **When** it is listed
   **Then** it holds ADR-001 to ADR-020 copied from the architecture run's `adr-log.md`, one file each, named `NNNN-<slug>.md`, plus the OQ-1 and OQ-2 stubs, and the architecture spine is linked from `docs/architecture.md`.

## Boundaries

- No LICENSE file until OQ-2 is decided (epic 9).
- Must not change: `AGENTS.md`; a pointer to CONTRIBUTING is added only through a `bmad-project-context` refresh, not here.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-001 to ADR-020
- spec — PROJECT_SPEC.md, sections 8, 13.2, 17.1

## Notes

- Files: `.gitignore`, `.gitattributes`, `.editorconfig`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `docs/architecture.md`, `docs/decisions/*.md`.
- Tests: `tests/unit/test_gitattributes.py` (golden paths covered); a CI step on Windows that asserts LF on a golden file.
- Depends on: story 1. Risk: low.
- Done when: criteria 1 to 4 pass and a Windows clone shows LF goldens.
