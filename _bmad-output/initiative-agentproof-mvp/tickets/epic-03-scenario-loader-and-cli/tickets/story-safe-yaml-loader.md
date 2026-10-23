---
id: 2
type: story
title: "Safe YAML loader"
parent: epic-03-scenario-loader-and-cli
covers: [R1]
after: ["2.1"]
hitl: false
risk: high
refined: true
---

# Safe YAML loader

## Description

The only YAML entry point in the package, with the four rejections that `yaml.safe_load` alone does not give: duplicate keys, aliases, multi-document streams, and custom tags, each reported with a line number. The security of every Suite rests here.

## Requirements

1. **Custom tags** (R1; PRD AC-1.1; spine AD-19)
   **Given** a document with `!!python/object` or any custom tag
   **When** `yaml_safe.load(text, source=)` runs
   **Then** it raises `SuiteError` naming the source and line, and no object is constructed.
2. **Duplicate keys** (R1; PRD AC-1.4)
   **Given** a mapping with the same key twice at any level
   **When** loaded
   **Then** it raises naming the key and the line of the second occurrence.
3. **Aliases and anchors** (R1; PRD AC-1.5)
   **Given** a document using `&a` and `*a`, or the billion-laughs fixture
   **When** loaded
   **Then** it raises before any expansion, naming the line.
4. **Multi-document and plain documents** (R1; PRD AC-1.6)
   **Given** a stream with a second `---` document
   **When** loaded
   **Then** it raises naming the line of the second marker; and the spine's Suite seed loads to a dict with string keys and native scalars.

## Boundaries

- No model validation; the result is a dict.
- Must not change: `errors`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-03-scenario-loader-and-cli/epic-03-scenario-loader-and-cli.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-19
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-1, AC-1.1 to AC-1.6

## Notes

- Files: `src/agentproof/loading/yaml_safe.py`, `tests/fixtures/yaml/*.yaml`.
- Tests: `tests/unit/loading/test_yaml_safe.py` with one fixture per rejection class and a memory assertion for the billion-laughs case.
- Depends on: 2.1. Risk: high; PyYAML's loader hooks differ between the C and pure-Python loaders, so the tests run with the pure loader forced.
- Done when: criteria 1 to 4 pass.
