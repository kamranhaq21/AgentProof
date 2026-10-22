---
id: 3
type: story
title: "Path, symlink, device-name, locked-file, and oversized-input hardening tests"
parent: epic-09-security-hardening-and-documentation
covers: [R3]
after: ["5.3"]
hitl: false
risk: medium
refined: true
---

# Path, symlink, device-name, locked-file, and oversized-input hardening tests

## Description

The spec's security tests collected in one place and run on both platforms, each asserting the documented exit code and message rather than just "it did not crash".

## Requirements

1. **Scenario id as path** (R3; PRD AC-2.5, AC-29.1)
   **Given** Suites whose Scenario ids are `../escape`, `CON`, `nul.trace`, and a 65-character id
   **When** `validate` runs
   **Then** each exits 2 naming the id, and nothing is written outside the Output Directory in any later command.
2. **Symlinks** (R3; PRD AC-29.2; spine AD-14)
   **Given** an Output Directory containing a symlink to a directory outside it
   **When** `run` writes
   **Then** it exits 3 naming the refused path and the external directory is untouched; and a Suite directory symlink pointing outside it makes `load_suite` raise `PathError`.
3. **Locked file** (R3; PRD AC-29.3)
   **Given** `report.json` held open with a share-deny lock on Windows
   **When** `run` writes
   **Then** it exits 3 naming the file and the `.agentproof-` temp file remains; on Linux the equivalent read-only directory case exits 3.
4. **Oversized input and audit** (R3; PRD AC-1.2, AC-7.3; spine AD-17)
   **Given** a 6 MB Suite and a 6 MB Trace
   **When** `validate` and `trace validate` run
   **Then** each exits 2 naming the limit before parsing (measured by a patched parser that would raise); and `pip-audit` remains a required CI job.

## Boundaries

- Must not change: product behavior; a failing case is a bug ticket against the owning story.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-14, AD-17, AD-19
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, AC-1.2, AC-2.5, AC-7.3, AC-29.1 to AC-29.3, NFR-5
- spec — PROJECT_SPEC.md, section 11.1

## Notes

- Files: `tests/integration/security/test_paths.py`, `tests/integration/security/test_locked_file.py`, `tests/integration/security/test_limits.py`, `tests/fixtures/suites/hardening/`.
- Tests: as listed, platform-marked where behavior differs.
- Depends on: 5.3. Risk: medium.
- Done when: criteria 1 to 4 pass on both CI platforms.
