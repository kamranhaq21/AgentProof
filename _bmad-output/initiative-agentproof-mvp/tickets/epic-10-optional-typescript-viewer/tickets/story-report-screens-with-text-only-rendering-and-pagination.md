---
id: 3
type: story
title: "Report screens with text-only rendering and pagination"
parent: epic-10-optional-typescript-viewer
covers: []
after: [2]
hitl: false
risk: medium
---

# Report screens with text-only rendering and pagination

## Description

Only if the viewer is built: the six screens from spec §6.10 rendering every untrusted value as text, with keyboard navigation, pagination for large Reports, and empty and error states. Full criteria are written when the gate opens; the verify line stands until then.

## Requirements

Verify: A Report with a script tag in a tool argument shows it as text; a 10,000-Event Report pages; an invalid file shows the error state; every screen is reachable by keyboard.

## Boundaries

- No evaluation logic in the viewer; it reads Report schema v1 only.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-10-optional-typescript-viewer/epic-10-optional-typescript-viewer.md
- spec — PROJECT_SPEC.md, section 6.10
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-35

## Notes

- Files: `packages/viewer/src/**`.
- Tests: Vitest unit tests per screen; a rendering test with the hostile Report fixture.
- Depends on: story 2. Risk: medium.
- Done when: the verify check passes, once criteria are written.
