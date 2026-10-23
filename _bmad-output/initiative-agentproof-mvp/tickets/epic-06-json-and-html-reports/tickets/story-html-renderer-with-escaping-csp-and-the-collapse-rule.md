---
id: 2
type: story
title: "HTML renderer with escaping, CSP, and the collapse rule"
parent: epic-06-json-and-html-reports
covers: [R2]
after: [1]
hitl: false
risk: high
refined: true
---

# HTML renderer with escaping, CSP, and the collapse rule

## Description

The page a reviewer opens. It is built from string templates with every value escaped in a safe position, no scripts, no external resources, and the rule that keeps a 10,000-Event Trace readable without JavaScript.

## Requirements

1. **Escaping positions** (R2; spine AD-12; PRD AC-23.2)
   **Given** `reports.html.render(report)`
   **When** a Trace value contains `<script>`, `</script>`, `"` and `'` in attribute position, or `javascript:alert(1)`
   **Then** each renders as visible text; no value appears in `<title>`, `<style>`, `<script>`, an unquoted attribute, `href`, or `src`; nothing is linkified; verified by a vector test and by a grep of the rendered page.
2. **Self-contained with CSP** (R2; PRD AC-23.1)
   **Given** the rendered page
   **When** inspected
   **Then** it contains `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">`, no `<script>` element, no external URL in any attribute, and no embedded JSON.
3. **Content** (R2; PRD AC-23.3 to AC-23.5)
   **Given** the example Report
   **When** rendered
   **Then** each Scenario shows its status as text, its failed and errored Assertions with id, message, and Evidence seqs, and missing and redacted values labeled as such; Event 1 of `reject-over-limit` appears expanded under the failing Assertion with its arguments.
4. **Collapse rule** (R2; spine AD-12; PRD NFR-10)
   **Given** a Scenario with 1,200 Events where Evidence points at seq 1,150
   **When** rendered
   **Then** seq 1,150 is expanded, the first 500 non-evidence Events are present inside `<details>` elements, and the remainder is a count with the JSON Report path as text.

## Boundaries

- No command wiring (story 3).
- No Jinja2 and no JavaScript (spine AD-12, AD-16).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-06-json-and-html-reports/epic-06-json-and-html-reports.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-12
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-23, AC-23.1 to AC-23.5, NFR-10, UJ-1

## Notes

- Files: `src/agentproof/reports/html.py`, `src/agentproof/reports/templates.py` (string templates), `src/agentproof/__init__.py` (`render_html`), `tests/fixtures/reports/hostile-report.json`.
- Tests: `tests/unit/reports/test_html_vectors.py`, `tests/unit/reports/test_html_content.py`, `tests/unit/reports/test_html_collapse.py`.
- Depends on: story 1. Risk: high; escaping mistakes are the product's main XSS surface.
- Done when: criteria 1 to 4 pass.
