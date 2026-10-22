---
type: epic
title: "Trace import/export and offline replay: a run leaves redacted Traces on disk and trace replay re-evaluates one with no network, after the pivot interviews are recorded"
parent: initiative-agentproof-mvp
covers: ["R4", "R6", "R11", "R19", "R26", "R31", "C5", "C6"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: high
---

# Trace import/export and offline replay

## Description

The second half of the product promise: Redaction at ingress with one rule set and the merge semantics, the runner writing each redacted Trace in Canonical form through the atomic writer, `runner.replay` sharing the run pipeline, the `trace replay` command, the proofs that Trace content is inert and that Replay touches neither network nor subprocess, and the secret-leak tests over artifacts and terminal output. It opens with the human gate the PRD places before this work: the developer interviews on hypotheses H1 to H4.

## Outcome

For a maintainer with a user's bug report, a saved Trace is validated, a new Assertion is written, and `trace replay` reproduces the failing result with no credentials (PRD UJ-2); for the maintainer, the interviews say whether to continue past the engine (PRD §8).

## Requirements

- R1 (parent R31): Five to ten developer interviews on H1 to H4 are recorded in the initiative folder with the adoption count; fewer than three would-be adopters records a pause decision and this epic's remaining entries wait.
- R2 (parent R19, C6): `redaction.redact(trace, rules, secret_values)` replaces configured keys at any depth of `arguments`, `result`, `metadata`, `output`, user dotted paths, and every occurrence of declared environment values with `[REDACTED]`, marks affected Events, records state, merges with prior state, and is idempotent; the runner applies it once at ingress for run and Replay, resolving `redact.env` values itself.
- R3 (parent R4): `run` writes `scenario-<id>.trace.json` for each Scenario in Canonical form through `io.write_atomic` into the Output Directory, refusing symlinks that escape it, and leaves the temp file on a failed rename with exit 3.
- R4 (parent R11): `runner.replay` and `agentproof trace replay TRACE_PATH --suite SUITE_PATH --scenario ID [--output DIR]` evaluate the named Scenario through the same pipeline, write `replay-<id>.report.json` once epic 6 provides the Report (until then print the summary), never overwrite run output, and give the same `ScenarioResult` as `evaluate_scenario(scenario, redact_trace(...), defaults)`.
- R5 (parent R6, R26): a Trace whose arguments, results, and metadata contain shell commands, URLs, script tags, and Python expressions evaluates identically to plain strings; a `conftest` guard makes socket creation and subprocess spawning raise for every test not marked `allow_subprocess`; a CI step runs the example Suite inside `docker run --network none`.
- R6 (parent R19): a planted value under a redacted key, in a declared environment variable placed in Final Output and a tool result, and in an adapter exception message appears in no written artifact and no captured console output.

## Constraints

- Covered parent constraints: C5 (one pipeline for run and Replay; `write_atomic` the only writer) and C6 (one redaction function, one scrubber, Canonical form); the lines below say how.
- Spine AD-10: one `redact`, one `scrub_text`; the core never reads the environment.
- Spine AD-13: one pipeline; the CLI never calls core for run or Replay.
- Spine AD-14: fixed artifact names; `replay` never writes `scenario-*.trace.json` or `report.json`.
- ARCH-6 is built as no minimum secret length.

## Done when

- After `run`, each `scenario-<id>.trace.json` validates, is byte-identical across two runs in deterministic mode, and contains `[REDACTED]` where the fixture planted secrets (R2, R3).
- `trace replay` on an exported Trace with network blocked and no environment variables set exits with the same code and prints the same Assertion Results as the run (R4, R5).
- The secret-leak integration test and the inert-Trace test pass on Linux and Windows CI, and the networkless Docker step passes (R5, R6).
- The interview record exists with the adoption count and a dated decision to continue or pause (R1).
- Production delivery: the CI matrix runs the Replay and leak tests on both platforms (R5).

## Boundaries

- No Report files (epic 6); Replay prints its summary until `build_report` exists, then story 4's follow-up in epic 6 writes `replay-<id>.report.json`.
- No `compare` (epic 7).
- Must not change: the Trace model's redaction-state shape from epic 2.
- Touch point: Docker on the CI runner for the networkless step; owner: this epic.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-10, AD-13, AD-14, AD-17, AD-18
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-6, FR-7, FR-9, FR-19, FR-31, NFR-3, NFR-4, section 8 pivot criterion
- research — _bmad-output/initiative-agentproof-mvp/prd-agentproof/addendum.md, section A (interview script sources)

## Notes

- Decision (2026-10-22): the interview gate (R1) is the first entry and is a human step with a done checkpoint; stories 2 to 7 wait on it per the PRD's pivot criterion.
- Decision (2026-10-22): tracer bullet is story 2, `redact` wired into the runner so the example run's summary shows `[REDACTED]` for the fixture's planted key.
- Assumption: no minimum scrubbed secret length (ARCH-6); a declared empty variable contributes nothing.
- Open question: whether the interviews pause the initiative; owner: maintainer, answered in story 1.
