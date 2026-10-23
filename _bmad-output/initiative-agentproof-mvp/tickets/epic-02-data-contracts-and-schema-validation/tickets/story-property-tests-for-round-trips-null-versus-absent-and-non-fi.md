---
id: 6
type: story
title: "Property tests for round trips, null versus absent, and non-finite numbers"
parent: epic-02-data-contracts-and-schema-validation
covers: [R4, R1, R3]
after: [4]
hitl: false
risk: low
refined: true
---

# Property tests for round trips, null versus absent, and non-finite numbers

## Description

Example-based tests miss the shapes users will actually send. Property tests over the models and the serializer back the byte-identity and robustness claims with generated data.

## Requirements

1. **Round trip** (R4; PRD NFR-1)
   **Given** hypothesis strategies for `JsonValue`, Suite, Trace, and Report
   **When** a generated instance is serialized with `canonical.dumps`, parsed with `json.loads`, and validated again
   **Then** the result equals the original, for at least two hundred examples per model.
2. **Null versus absent** (R1, R3; spine AD-19; PRD NFR-5)
   **Given** a generated Trace with optional fields omitted
   **When** it is validated and serialized
   **Then** every optional field is present as `null` in the output, and validating the output again yields an equal object.
3. **Non-finite numbers** (R4; spine AD-11)
   **Given** a tool argument or Final Output containing NaN or infinity
   **When** it is validated
   **Then** a taxonomy error is raised naming the path.
4. **Unicode** (R4; PRD NFR-5)
   **Given** generated strings with non-ASCII, combining characters, and newlines
   **When** round-tripped
   **Then** they are preserved exactly and `dumps` output is byte-identical across two runs.

## Boundaries

- Must not change: model definitions; a property failure is fixed in the model by its own story's rules, reported here as a finding.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-11, AD-19
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, NFR-1, NFR-5

## Notes

- Files: `tests/unit/models/strategies.py`, `tests/unit/models/test_properties.py`.
- Tests: as listed, with `hypothesis` in the dev group and a fixed database seed in CI for reproducibility.
- Depends on: story 4. Risk: low.
- Done when: criteria 1 to 4 pass on both CI platforms.
