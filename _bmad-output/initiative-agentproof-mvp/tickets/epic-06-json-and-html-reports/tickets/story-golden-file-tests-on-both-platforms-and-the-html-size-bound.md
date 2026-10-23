---
id: 4
type: story
title: "Golden-file tests on both platforms and the HTML size bound"
parent: epic-06-json-and-html-reports
covers: [R3, R4]
after: [3]
hitl: false
risk: medium
refined: true
---

# Golden-file tests on both platforms and the HTML size bound

## Description

The determinism claim for every artifact kind, proven on both CI platforms with the volatile paths stripped and the golden files protected from line-ending conversion, plus the one size bound for large Reports.

## Requirements

1. **Goldens per kind** (R3; spine AD-11, AD-17; PRD NFR-1)
   **Given** `tests/golden/` holding `trace-example.json`, `report-example.json`, and `report-example.html`
   **When** the golden tests run on Linux and Windows CI
   **Then** the freshly produced artifacts, stripped of `VOLATILE_PATHS`, equal the goldens byte for byte.
2. **Strip uses the one list** (R3)
   **Given** the strip helper
   **When** a field outside `VOLATILE_PATHS` differs
   **Then** the test fails; and the helper imports `models.canonical.VOLATILE_PATHS` rather than its own list.
3. **Line endings** (R3)
   **Given** `.gitattributes`
   **When** the Windows job checks out
   **Then** a test asserts each golden file contains no `\r`.
4. **HTML size bound** (R4; PRD NFR-10)
   **Given** a 10,000-Event Report
   **When** rendered
   **Then** the HTML is under 10 MB, measured in a test marked `performance`.

## Boundaries

- Must not change: Canonical form or the renderer; a failing golden is investigated, never regenerated without a dated note.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-06-json-and-html-reports/epic-06-json-and-html-reports.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-11, AD-17
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, NFR-1, NFR-6, NFR-10

## Notes

- Files: `tests/golden/*`, `tests/helpers/golden.py`, `tests/integration/test_goldens.py`, `tests/performance/test_html_size.py`.
- Tests: as listed.
- Depends on: story 3. Risk: medium; platform-specific float repr or path strings leaking into artifacts will show here and must be fixed at the source.
- Done when: criteria 1 to 4 pass on both CI platforms.
