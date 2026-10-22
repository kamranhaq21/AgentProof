---
type: epic
title: "JSON and HTML reports: every run and Replay writes a versioned JSON Report, report renders a safe self-contained HTML page, and golden files prove byte identity on two platforms"
parent: initiative-agentproof-mvp
covers: ["R14", "R15", "R18", "R23", "R24", "R30", "C6"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: medium
---

# JSON and HTML reports

## Description

The artifacts a reviewer reads: `reports.build_report` as the only Report constructor, `reports.json_report.dumps`, the pipeline writing `report.json` and `replay-<id>.report.json`, `reports.html.render` with the escaping, CSP, no-linkify, and collapse rules, the `report` command, and the golden-file tests that strip the volatile paths and run on Linux and Windows.

## Outcome

For a reviewer who did not write the agent, the uploaded HTML Report shows which rule broke and the Event it points at, with secrets redacted (PRD UJ-1 second half).

## Requirements

- R1 (parent R14): `build_report(outcome, suite=, run_id=, created_at=, package_version=, traces=)` is the only constructor; the pipeline writes `report.json` after the Traces for `run` and `replay-<id>.report.json` for Replay; counts equal the listed results; the defaults snapshot is embedded.
- R2 (parent R15): `render(report)` assembles the page from string templates with every value escaped in element or quoted-attribute position only, no value in title, style, script, unquoted attribute, href, or src, no linkify, a CSP meta tag, no external resources, status as text, missing and redacted values labeled, evidence-referenced Events expanded, the first 500 others collapsed, the rest counted.
- R3 (parent R24): golden-file tests per artifact kind strip `VOLATILE_PATHS` and pass on Linux and Windows CI with LF-protected goldens.
- R4 (parent R30): the HTML Report for a 10,000-Event Trace is under 10 MB.
- R5 (parent R18, R23, C6): `report REPORT_PATH --format json|html [--output FILE]` writes the HTML name derived from the JSON name next to it by default, rejects `junit` with exit 2, and writes through `write_atomic`; `loading.report` with `parse_report` and `load_report` is created here (version 1 only) and epic 7 adds version dispatch to it.

## Constraints

- Covered parent constraint: C6 (Canonical form, one volatile list, stdlib HTML with the escaping and CSP rules); the lines below say how.
- Spine AD-11, AD-12, AD-13, AD-14, AD-15: no Jinja2, no JavaScript, no embedded JSON; `render_html` and `dumps_report` are public API.
- Spine AD-1: `reports` returns text only; the shell writes.

## Done when

- After `run`, `report.json` validates against the generated schema and `agentproof report report.json --format html` produces a page that loads offline with the CSP and shows Event 1's arguments expanded under the failing Assertion (R1, R2, R5).
- The HTML vector test renders `<script>`, `</script>`, quotes in attribute position, and a `javascript:` URL as visible text (R2).
- The golden tests for Trace, Report, and HTML pass on both CI platforms and fail when a volatile field is accidentally compared (R3).
- The 10,000-Event Report size test passes (R4).
- Production delivery: the Replay path writes `replay-<id>.report.json` and the CI matrix covers it (R1).

## Boundaries

- No Comparison (epic 7); no JUnit (deferred, rejected with exit 2 here).
- Must not change: the Report model from epic 2; a needed field is a `Source conflict:` there.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-11, AD-12, AD-13, AD-14, AD-15
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-22, FR-23, FR-24, NFR-1, NFR-10
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-011, ADR-012, ADR-013

## Notes

- Decision (2026-10-22): tracer bullet is story 1, `build_report` plus `report.json` written by the pipeline with its first golden file.
- Decision (2026-10-22): the Replay report write (epic 5 story 4 left it printing a summary) lands in story 1 here, since `build_report` is what it waited for.
- Decision (2026-10-22): `loading/report.py` (`parse_report`, `load_report`, version 1 only) is created by story 3 of this epic; epic 7 story 1 extends it with version dispatch and waits on 6.3.
