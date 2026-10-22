---
id: 1
type: spike
title: "Pick the framework from the interview data"
parent: epic-11-framework-adapter-after-user-validation
covers: []
after: ["5.1"]
hitl: true
risk: medium
---

# Pick the framework from the interview data

## Description

The question: which agent framework, if any, gets the one real Adapter in v0.1 (PRD OQ-15, AC-21.4)? Who waits: stories 2 and 3 of this epic. Where the answer goes: this epic's Notes as a dated Decision, and if one is named, its Requirements written by the Product Owner.

## Requirements

1. **Count** (PRD AC-21.4)
   **Given** the interview record from epic 5 story 1
   **When** the frameworks the would-be adopters use are tallied
   **Then** the spike records the tally and the capture completeness each framework's hooks can offer (which tool calls are observable).
2. **Decision**
   **Given** the tally
   **When** the spike closes
   **Then** the epic file carries a dated `Decision:` line naming one framework or none for v0.1; if one, `refined: true` and Requirements are written from PRD FR-21 and spine AD-9.

## Boundaries

- No code; at most one Adapter in v0.1 (PRD §5).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-11-framework-adapter-after-user-validation/epic-11-framework-adapter-after-user-validation.md
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-21, AC-21.4, OQ-15
- research — _bmad-output/initiative-agentproof-mvp/prd-agentproof/addendum.md, section A

## Notes

- Unknown: OQ-15; gates every entry in this epic.
- Files: the epic file's Notes and Requirements.
- Tests: none.
- Depends on: 5.1. Risk: medium.
- Done when: criterion 2 is met.
