---
id: 3
type: story
title: "Size-limited reading and parse_suite with every violation"
parent: epic-03-scenario-loader-and-cli
covers: [R1]
after: [1, 2, "2.2"]
hitl: false
risk: medium
refined: true
---

# Size-limited reading and parse_suite with every violation

## Description

The parse/load split the spine fixes: the shell reads with a size check and a symlink policy, the core parses text into a Suite and reports every violation at once so a user fixes a file in one pass.

## Requirements

1. **read_limited** (R1; spine AD-14, AD-19; PRD AC-1.2)
   **Given** `io.read_limited(path, max_bytes, base_dir=)`
   **When** a file larger than `max_bytes` is read, or a symlink resolves outside `base_dir`
   **Then** it raises `PathError` naming the limit or the escape before reading the content; otherwise it returns the text decoded as UTF-8.
2. **parse_suite collects violations** (R1; PRD AC-2.1 to AC-2.4, AC-3.1 to AC-3.3)
   **Given** `parse_suite(text, source=)` on a Suite with a missing version, an unknown field, and a duplicate Scenario id
   **When** it runs
   **Then** it raises one `SuiteError` whose `violations` list all three in field order, each with `source`, `field`, and `message`.
3. **load_suite** (R1; spine AD-15)
   **Given** `load_suite(path)`
   **When** it runs on the spine's Suite seed file
   **Then** it returns a Suite equal to `parse_suite` on the file's text, with `source` set to the path.
4. **Violation formatting** (R1; PRD AC-28.1)
   **Given** a `SuiteError`
   **When** the CLI formatter renders it
   **Then** each violation becomes one line `SuiteError: <message> (<source>:<field>)`.

## Boundaries

- No command wiring (story 4).
- Must not change: the models; a needed rule is a `Source conflict:` in epic 2.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-03-scenario-loader-and-cli/epic-03-scenario-loader-and-cli.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-1, AD-14, AD-15, AD-19
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-1 to FR-3, AC-28.1

## Notes

- Files: `src/agentproof/io/artifacts.py` (`read_limited`), `src/agentproof/loading/suite.py`, `src/agentproof/__init__.py` (exports), `src/agentproof/cli/app.py` (formatter).
- Tests: `tests/unit/io/test_read_limited.py` (limit, symlink, encoding), `tests/unit/loading/test_parse_suite.py` (multi-violation), `tests/unit/test_public_api.py` (names present).
- Depends on: stories 1 and 2 (it edits `cli/app.py` and `__init__.py` after story 1 created them) and 2.2. Risk: medium; Pydantic groups errors per model, so collecting across nested models needs a flattening step with stable ordering.
- Done when: criteria 1 to 4 pass.
