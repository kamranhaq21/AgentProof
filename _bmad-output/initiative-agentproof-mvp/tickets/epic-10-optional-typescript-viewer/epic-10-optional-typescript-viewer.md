---
type: epic
title: "Optional TypeScript viewer: if the maintainer opens the gate, a local React viewer reads a JSON Report with no network"
parent: initiative-agentproof-mvp
covers: ["R23"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: false
risk: low
---

# Optional TypeScript viewer

## Description

The PRD defers the viewer to v0.3 (FR-35, §6.2) and the user lists it as an optional epic that must not block the core. This epic exists so the decision has a home: a spike decides whether the viewer starts in v0.1 at all, and only if it does are the scaffold and screens built. Its contract is Report schema v1 from epic 2 and epic 6. No `package.json` or pnpm workspace exists until the gate opens.

## Outcome

For a reader of a large Report, a local page with keyboard navigation shows summary, Scenarios, Assertions, timeline, Event details, and Comparison without a network request; or, if the gate stays closed, nothing is built and the HTML Report remains the reading surface.

## Done when

- The spike records a dated decision to build or to keep deferring (R23).
- If building: `packages/viewer` loads an exported `report.json` from disk, renders every untrusted value as text, makes no network request by default, handles a 10,000-Event Report with pagination, and has empty and error states, with Vitest tests and ESLint in the check entry point.
- Production delivery, if building: the viewer is a static build attached to the GitHub release, not a backend.

## Boundaries

- Never blocks epics 1 to 9; no evaluation logic lives here (spine Deferred).
- No backend, no account, no telemetry.
- Must not change: Report schema v1.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-35, section 6.2
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, Deferred
- spec — PROJECT_SPEC.md, section 6.10

## Notes

- Unknown: whether the viewer starts in v0.1 or stays deferred to v0.3; gates every entry; the maintainer decides after epic 6.
- Decision (2026-10-22): planned thin; Requirements are written when the gate opens.
