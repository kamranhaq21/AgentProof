---
id: 3
type: story
title: "Conformance, limits, and a credentialed example run"
parent: epic-11-framework-adapter-after-user-validation
covers: []
after: [2]
hitl: true
risk: medium
---

# Conformance, limits, and a credentialed example run

## Description

Only if the Adapter is built: the conformance check in CI without credentials, a docs page stating the Adapter's known limitations and Capture, and a person running the example Suite against a real agent with a credential to confirm the exported Trace is redacted (hitl). Full criteria are written when the gate opens; the verify line stands until then.

## Requirements

Verify: The conformance check passes in CI without credentials; the credentialed run's exported Trace contains the marker where the key was; the adapter page's tagged blocks pass the docs test.

## Boundaries

- The credentialed run never happens in CI (spine AD-18, PRD NFR-3).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-11-framework-adapter-after-user-validation/epic-11-framework-adapter-after-user-validation.md
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, AC-21.5, SM-3
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-9, AD-10

## Notes

- Files: `docs/adapters/<name>.md`, `tests/unit/adapters/test_<name>_conformance.py`.
- Tests: as listed.
- Depends on: story 2. Risk: medium.
- Hitl step: the credentialed example run on the maintainer's machine.
- Done when: the verify check passes, once criteria are written.
