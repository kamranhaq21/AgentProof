---
id: 4
type: story
title: "Security policy, review record, and license file"
parent: epic-09-security-hardening-and-documentation
covers: [R4, R5]
after: [3]
hitl: true
risk: medium
refined: true
---

# Security policy, review record, and license file

## Description

The process documents a public project needs before launch, and the license file that has waited for the maintainer's decision. A person completes the review checklist and records the license (hitl).

## Requirements

1. **SECURITY.md** (R4; spec §11.1)
   **Given** `SECURITY.md`
   **When** read
   **Then** it names a private reporting channel, a response window, supported versions, and links `docs/security.md` for limits.
2. **Review record** (R4; spec §11.1)
   **Given** `docs/decisions/security-review.md`
   **When** read
   **Then** every item of spec §11.1 is listed with its evidence (a test name, a file, or a dated note) and any unmet item has an issue link and an owner.
3. **License** (R5; initiative C9; OQ-2)
   **Given** the maintainer's recorded decision in `docs/decisions/0021-license.md`
   **When** this story completes
   **Then** `LICENSE` holds that license's text, `pyproject.toml` carries the matching classifier and `license` field, and CONTRIBUTING states the contribution terms.
4. **Dependency licenses** (R4; spec §13.3)
   **Given** the four runtime dependencies
   **When** their licenses are listed in the review record
   **Then** each is compatible with the chosen license.

## Boundaries

- No publishing (story 5).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements
- spec — PROJECT_SPEC.md, sections 11.1, 13.3, 16
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, OQ-2

## Notes

- Files: `SECURITY.md`, `LICENSE`, `docs/decisions/security-review.md`, `docs/decisions/0021-license.md`, `pyproject.toml`, `CONTRIBUTING.md`.
- Tests: `tests/unit/test_license_metadata.py` (classifier matches LICENSE).
- Depends on: story 3. Risk: medium.
- Hitl step: the maintainer decides the license (OQ-2) and signs off the review record.
- Done when: criteria 1 to 4 pass.
