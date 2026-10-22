---
id: 1
type: spike
title: "Decide whether the viewer starts in v0.1"
parent: epic-10-optional-typescript-viewer
covers: []
after: ["6.4"]
hitl: true
risk: low
---

# Decide whether the viewer starts in v0.1

## Description

The question: is the HTML Report enough for v0.1 readers, or does the viewer start now? Who waits: stories 2 and 3 of this epic. Where the answer goes: this epic's Notes as a dated Decision, and if building, its Requirements written by the Product Owner. The PRD defers the viewer to v0.3 (FR-35, §6.2); the user listed it as optional and non-blocking.

## Requirements

1. **Inputs** (epic Done when)
   **Given** the HTML Report from epic 6 on the example and on a 10,000-Event Report
   **When** the maintainer reviews it against the viewer screens in spec §6.10
   **Then** the spike records what the HTML Report cannot do that a reader needs, if anything.
2. **Decision**
   **Given** that record and the maintainer's capacity after epic 9
   **When** the spike closes
   **Then** the epic file carries a dated `Decision:` line: build in v0.1, or keep deferred to v0.3; if building, `refined: true` and Requirements are written from spec §6.10 and PRD FR-35.

## Boundaries

- No code.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-10-optional-typescript-viewer/epic-10-optional-typescript-viewer.md
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-35, section 6.2
- spec — PROJECT_SPEC.md, section 6.10

## Notes

- Unknown: build the viewer in v0.1 or keep it deferred; gates every entry in this epic.
- Files: the epic file's Notes and Requirements.
- Tests: none.
- Depends on: 6.4. Risk: low.
- Done when: criterion 2 is met.
