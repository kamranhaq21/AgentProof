---
id: 2
type: story
title: "Viewer scaffold under packages/viewer"
parent: epic-10-optional-typescript-viewer
covers: []
after: [1]
hitl: true
risk: low
---

# Viewer scaffold under packages/viewer

## Description

Only if the spike says build: the React, Vite, TypeScript strict scaffold with Vitest and ESLint, Node LTS pinned, wired into the check entry point, loading a `report.json` from disk with no network request. A person runs the starter (hitl). Full criteria are written when the gate opens; the verify line stands until then.

## Requirements

Verify: The viewer builds statically, opens `report.json` from the example run, and the browser's network panel shows no requests after load.

## Boundaries

- No backend, no account, no telemetry (spine Deferred, PRD §5).
- Must not change: Report schema v1.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-10-optional-typescript-viewer/epic-10-optional-typescript-viewer.md
- spec — PROJECT_SPEC.md, sections 6.10, 9 TypeScript

## Notes

- Files: `packages/viewer/**`, root `package.json` and `pnpm-workspace.yaml` (only when this story starts), `scripts/check.py` (viewer steps).
- Tests: Vitest smoke test; ESLint in the check entry point.
- Depends on: story 1's decision. Risk: low.
- Done when: the verify check passes, once criteria are written.
