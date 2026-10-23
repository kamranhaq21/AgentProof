---
id: 2
type: story
title: "Adapter implementation as an optional extra"
parent: epic-11-framework-adapter-after-user-validation
covers: []
after: [1, "4.6", "5.2"]
hitl: false
risk: medium
---

# Adapter implementation as an optional extra

## Description

Only if the spike names a framework: the Adapter under `adapters/<name>/` against the protocol, registered as an entry point, installable as `agentproof[<name>]`, with a Capture declaration matching what the framework's hooks expose and the SDK imported nowhere else. Full criteria are written when the gate opens; the verify line stands until then.

## Requirements

Verify: `pip install agentproof[<name>]` registers the adapter, `lint-imports` passes, and a scripted test agent produces a Trace with the declared Capture through `agentproof run --adapter <name>`.

## Boundaries

- No framework SDK import outside `adapters/<name>/` (spine AD-2, AD-16).
- Must not change: the Adapter protocol or `RunContext`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-11-framework-adapter-after-user-validation/epic-11-framework-adapter-after-user-validation.md
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-2, AD-9, AD-16
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-21

## Notes

- Files: `src/agentproof/adapters/<name>/**`, `pyproject.toml` (extra and entry point).
- Tests: unit tests against a scripted framework agent without credentials; the conformance check.
- Depends on: story 1's decision, 4.6, 5.2. Risk: medium; ARCH-2 (sync-only) may need revisiting if the framework is async-only.
- Done when: the verify check passes, once criteria are written.
