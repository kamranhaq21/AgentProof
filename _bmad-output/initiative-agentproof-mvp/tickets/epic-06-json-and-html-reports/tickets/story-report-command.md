---
id: 3
type: story
title: "report command"
parent: epic-06-json-and-html-reports
covers: [R5]
after: [2]
hitl: false
risk: low
refined: true
---

# report command

## Description

The command that turns a JSON Report into the HTML page, with the naming rule the spine fixes and the rejection of the deferred JUnit format.

## Requirements

1. **HTML output** (R5; spine AD-14, AD-20; PRD AC-23.6)
   **Given** `agentproof report report.json --format html`
   **When** it runs
   **Then** it writes `report.html` next to the input through `write_atomic` and exits 0; `--output other.html` writes there instead; `replay-x.report.json` yields `replay-x.report.html`.
2. **JSON output** (R5)
   **Given** `--format json`
   **When** it runs
   **Then** it re-emits the Report in Canonical form to `--output` or stdout.
3. **JUnit rejected** (R5; PRD FR-24, §6.2)
   **Given** `--format junit`
   **When** it runs
   **Then** it exits 2 with one line saying JUnit is planned for v0.2.
4. **Public API only** (R5; spine AD-15)
   **Given** the command module
   **When** inspected
   **Then** it calls `load_report`, `render_html`, `dumps_report`, and `io.write_atomic` and imports no core module directly.

## Boundaries

- Must not change: the renderer.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-06-json-and-html-reports/epic-06-json-and-html-reports.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-14, AD-15, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-23, FR-24, AC-23.6

## Notes

- Files: `src/agentproof/cli/commands/report.py`, `src/agentproof/loading/report.py` (this story creates `parse_report` and `load_report` for version 1, exported in the public API; epic 7 story 1 adds the version dispatch and upgrade stub).
- Tests: `tests/integration/cli/test_report.py` (subprocess; html, json, junit, naming), `tests/unit/loading/test_parse_report.py` (version 1, malformed input).
- Depends on: story 2. Risk: low.
- Done when: criteria 1 to 4 pass.
