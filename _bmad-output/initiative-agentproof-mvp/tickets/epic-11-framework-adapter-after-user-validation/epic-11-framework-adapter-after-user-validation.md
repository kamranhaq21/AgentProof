---
type: epic
title: "One framework adapter selected after user validation: a real agent framework runs through the Adapter protocol as an optional extra"
parent: initiative-agentproof-mvp
covers: ["R13"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: false
risk: medium
---

# One framework adapter selected after user validation

## Description

The PRD ships at most one real Adapter in v0.1 and only if the interviews pick one (AC-21.4, OQ-15). This epic holds that decision and, once made, the Adapter: an optional extra under the `agentproof.adapters` entry-point group, a Capture declaration that states what it can observe, the conformance check passing, documented limitations, and the example Suite running against a real agent when credentials are present. Its contract is the Adapter protocol from epic 4 and Redaction from epic 5.

## Outcome

For a developer on the chosen framework, their own agent runs through `agentproof run --adapter <name>` and produces a redacted Trace the rest of the product evaluates (PRD SM-3).

## Done when

- The spike records which framework, from the interview data, with a dated decision, or records that none ships in v0.1 (R13).
- If building: the Adapter installs as `agentproof[<name>]`, passes `testing.adapter_conformance.check`, declares its Capture, documents its limits, and the example Suite runs against the framework in a credentialed, non-CI session with Redaction removing the key.
- Production delivery, if building: the extra is in the published wheel's metadata.

## Boundaries

- Never more than one Adapter in v0.1 (PRD non-goal).
- No framework SDK import outside `adapters/<name>/` (spine AD-2).
- Must not change: the Adapter protocol or `RunContext`; a needed change is a `Source conflict:` in epic 4.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-21, AC-21.4, AC-21.5, OQ-15
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-9, Deferred
- research — _bmad-output/initiative-agentproof-mvp/prd-agentproof/addendum.md, section A

## Notes

- Unknown: OQ-15, which framework, if any; gates every entry; answered from the epic 5 interviews.
- Decision (2026-10-22): planned thin; Requirements are written when the gate opens.
