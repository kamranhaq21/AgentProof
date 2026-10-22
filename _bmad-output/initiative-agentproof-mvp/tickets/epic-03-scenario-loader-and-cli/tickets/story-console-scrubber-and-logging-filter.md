---
id: 5
type: story
title: "Console scrubber and logging filter"
parent: epic-03-scenario-loader-and-cli
covers: [R5]
after: [3]
hitl: false
risk: medium
refined: true
---

# Console scrubber and logging filter

## Description

Nothing the CLI prints may contain a declared secret. The one text scrubber lives in `redaction` so epic 5's `redact` and this console filter share it, and the filter is installed before any Trace is read.

## Requirements

1. **scrub_text** (R5; spine AD-10)
   **Given** `redaction.scrub_text(text, secret_values)`
   **When** `secret_values` contains `abcdefgh` and `abcdefghijkl`
   **Then** `x abcdefghijkl y abcdefgh z` becomes `x [REDACTED] y [REDACTED] z` (longest first), and an empty `secret_values` returns the text unchanged.
2. **Console wrapper** (R5; PRD AC-28.2)
   **Given** `io.console` with secret values set
   **When** anything is printed through it, including rich tables and error lines
   **Then** every occurrence is replaced, including inside rich markup.
3. **Logging filter** (R5; spine Conventions Logging)
   **Given** a `logging` record whose message contains a secret value
   **When** it is emitted through the configured handler
   **Then** the output shows the marker; the filter is installed by `io.console.install()` and the core emits no log records (asserted by a test that enables a handler during a core call).
4. **Global options** (R5; spine AD-20)
   **Given** `--no-color` and `--verbose`
   **When** set
   **Then** output contains no ANSI escapes, and verbose diagnostics appear only for exit 3 and 4 paths.

## Boundaries

- No `redact` function for Traces (epic 5 story 2).
- Must not change: the single-exit-site rule.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-03-scenario-loader-and-cli/epic-03-scenario-loader-and-cli.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-10, AD-20, Conventions (Logging)
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, AC-28.2

## Notes

- Files: `src/agentproof/redaction/apply.py` (`scrub_text`), `src/agentproof/io/console.py`, `src/agentproof/cli/app.py` (global options).
- Tests: `tests/unit/redaction/test_scrub_text.py`, `tests/unit/io/test_console.py`, `tests/integration/cli/test_no_color.py`.
- Depends on: story 3 (which is after story 1), so edits to `cli/app.py` are serialized. Risk: medium; rich markup can split a secret across styled spans, so the scrub runs on the final rendered text.
- Done when: criteria 1 to 4 pass.
