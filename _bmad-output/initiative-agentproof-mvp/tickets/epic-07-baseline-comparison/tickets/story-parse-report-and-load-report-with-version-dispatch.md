---
id: 1
type: story
title: "parse_report and load_report with version dispatch"
parent: epic-07-baseline-comparison
covers: [R1]
after: ["6.3"]
hitl: false
risk: low
refined: true
---

# parse_report and load_report with version dispatch

## Description

The tracer bullet: the run's own `report.json` round-trips through the public API. `parse_report` and `load_report` already exist from epic 6 story 3; this story adds the version dispatch, the hook the first schema bump will use, and the unsupported-version and size-limit paths.

## Requirements

1. **parse_report** (R1; spine AD-3, AD-15, Deferred)
   **Given** `parse_report(data, source=)`
   **When** given the run's `report.json`
   **Then** it returns a Report equal to the one `build_report` produced; it dispatches on the integer `version` to the version-1 model through an `upgrade_to_latest` stub that is identity for version 1.
2. **Unsupported and malformed** (R1; PRD AC-25.1)
   **Given** a file with `version: 2` or a JSON object that is not a Report
   **When** parsed
   **Then** it raises `UnsupportedVersionError` naming both versions, or a taxonomy error with a field path.
3. **load_report** (R1; spine AD-14)
   **Given** `load_report(path)`
   **When** the file exceeds `MAX_REPORT_BYTES`
   **Then** it raises `PathError` before parsing; otherwise it returns `parse_report`.
4. **Public API** (R1; spine AD-15)
   **Given** `agentproof.__all__`
   **When** read
   **Then** it contains `parse_report` and `load_report`.

## Boundaries

- No comparison logic (story 2).
- Must not change: the Report model.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-07-baseline-comparison/epic-07-baseline-comparison.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-3, AD-14, AD-15, Deferred (schema version bumps)
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-25, AC-25.1

## Notes

- Files: `src/agentproof/loading/report.py`, `src/agentproof/__init__.py`.
- Tests: `tests/unit/loading/test_parse_report.py`.
- Depends on: 6.1 (and, through the epic gate, 6.3 which created the module). Risk: low.
- Done when: criteria 1 to 4 pass.
