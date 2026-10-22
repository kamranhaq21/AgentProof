---
id: 1
type: story
title: "Pivot gate: developer interviews on H1 to H4 recorded"
parent: epic-05-trace-import-export-and-offline-replay
covers: [R1]
after: []
hitl: true
risk: high
refined: true
---

# Pivot gate: developer interviews on H1 to H4 recorded

## Description

The PRD commits epics 1 to 4 regardless and requires evidence before the Trace workflow is built. A person runs five to ten interviews with developers who build tool-using agents, using a script derived from the PRD hypotheses and the competitor evidence, and records whether to continue. Every other story in this epic waits on this one.

## Requirements

1. **Script** (R1; PRD §8 H1 to H4, H6)
   **Given** `interviews/script.md` in the initiative folder
   **When** read
   **Then** it asks about current agent testing practice, saved traces, where tests live, local versus hosted preference, and why not Promptfoo, EvalView, or agentevals, and shows the example Suite and a Report.
2. **Record** (R1)
   **Given** `interviews/interviews.md`
   **When** the gate closes
   **Then** it holds at least five dated entries with role, framework, answers per hypothesis, and whether the developer would adopt the file-based, no-server combination for their own agent.
3. **Decision** (R1; PRD pivot criterion)
   **Given** the adopter count
   **When** it is three or more
   **Then** a dated `Decision:` line says continue; otherwise it says pause at epic 4 and reopen OQ-19, and the maintainer confirms either way.

## Boundaries

- No product code.
- Must not change: the PRD; a hypothesis status update is a PRD update run, referenced here.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-05-trace-import-export-and-offline-replay/epic-05-trace-import-export-and-offline-replay.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, section 8 Hypotheses and Evidence
- research — _bmad-output/initiative-agentproof-mvp/prd-agentproof/addendum.md, section A

## Notes

- Files: `_bmad-output/initiative-agentproof-mvp/interviews/script.md`, `_bmad-output/initiative-agentproof-mvp/interviews/interviews.md`.
- Tests: none; the verify check is the record's presence and the maintainer's confirmation.
- Depends on: nothing in code; practically, a runnable example from epic 4 to show interviewees.
- Risk: high; a pause decision stops epics 5 to 9 and is the point of the gate.
- Done when: criteria 1 to 3 are met and the done checkpoint is confirmed.
