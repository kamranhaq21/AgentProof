---
id: 2
type: story
title: "Reference docs for Suite format, Assertions, Traces, CLI, and security limits"
parent: epic-09-security-hardening-and-documentation
covers: [R1, R7]
after: [1]
hitl: false
risk: low
refined: true
---

# Reference docs for Suite format, Assertions, Traces, CLI, and security limits

## Description

The pages a user reaches from the README when they write their own Suite, read a Trace, or hit an exit code. Every limit statement comes from the constants so docs cannot drift from what the CLI prints.

## Requirements

1. **Pages** (R1; PRD FR-33)
   **Given** `docs/`
   **When** listed
   **Then** `getting-started.md`, `suite-format.md`, `assertions.md`, `traces.md`, `cli.md`, and `security.md` exist, and `architecture.md` links the spine.
2. **Content** (R1; PRD AC-15.4, AC-16.2, AC-27.5, AC-28.3, AC-31.4, AC-5.4)
   **Given** the pages
   **When** read
   **Then** `assertions.md` shows the one YAML form, the `tool_order` counter-example, and the compact-form rule for structured output; `traces.md` documents the event types, the metadata schema, the `llm_request`/`llm_response` rule, and the Capture declaration; `cli.md` lists every command signature and exit code from spine AD-20 and AD-6; `security.md` states the Redaction limits, the no-network guarantee, the size limits, and that artifacts should be inspected before sharing.
3. **Statements** (R1; spine AD-20)
   **Given** every limit or claim sentence in the pages
   **When** compared with `constants.STATEMENTS`
   **Then** each matches a constant, verified by a test that greps the pages for each statement.
4. **Deferred items** (R7; PRD FR-24, FR-35)
   **Given** `cli.md` and the roadmap section of `getting-started.md`
   **When** read
   **Then** JUnit XML and the viewer are listed as deferred with their target versions.

## Boundaries

- No docs site generator (spine Deferred).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-09-security-hardening-and-documentation/epic-09-security-hardening-and-documentation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-33, AC-31.4, AC-28.3, AC-27.5

## Notes

- Files: `docs/*.md`, `tests/unit/test_docs_statements.py`.
- Tests: the docs test from story 1 over the new pages' tagged blocks; the statements test.
- Depends on: story 1. Risk: low.
- Done when: criteria 1 to 4 pass.
