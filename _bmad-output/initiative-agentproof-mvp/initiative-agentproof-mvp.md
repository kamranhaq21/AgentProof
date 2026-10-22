---
type: initiative
title: "AgentProof v0.1: a developer tests an agent's tool behavior locally and gates a pull request on it"
parent: none
sources: ['_bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md', '_bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md', '_bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md', 'PROJECT_SPEC.md']
companions: ['_bmad-output/initiative-agentproof-mvp/prd-agentproof/addendum.md', '_bmad-output/initiative-agentproof-mvp/2026-10-22-context-assessment.md']
after: []
risk: high
---

# AgentProof v0.1: a developer tests an agent's tool behavior locally and gates a pull request on it

## Description

AgentProof v0.1 is a Python package and CLI that loads a YAML Suite of Scenarios, obtains a Trace of what an agent did (from the built-in Fixture Agent, an Adapter, or a saved file), evaluates deterministic Assertions on tool calls and final output, writes JSON and HTML Reports, compares a Report against a Baseline, and exits with a code a CI job can act on. It runs locally with no account, server, database, or telemetry. The PRD fixes the requirements; the architecture spine fixes the invariants every epic shares (AD-1 to AD-20). When this initiative is done, the launch demo in PRD UJ-1 works end to end from a clean install.

## Outcome

For an AI application engineer, a behavioral regression in a tool-using agent is caught by a failing CI check before merge, and the failure can be re-evaluated from the saved Trace without another model call. Success signals: PRD SM-1 (first successful run under five minutes), SM-2 (the demo PR is blocked by a declared Assertion failure), SM-3 (five developers test their own agent within thirty days).

## Requirements

- R1 (prd FR-1, FR-2, FR-3): A Suite file loads only through safe YAML parsing, is validated against its integer Schema Version with every violation reported, and is rejected on unknown fields, duplicate Scenario or Assertion ids, unregistered Assertion types, and invalid Assertion configuration, each naming the field path.
- R2 (prd FR-4): `agentproof init` scaffolds a runnable example with the Fixture Agent and saved Traces that passes and fails as documented with no credentials and no network, and refuses to overwrite existing files.
- R3 (prd FR-5, FR-8): A Trace is a versioned model with run-level identity, agent and adapter metadata, an allowlisted environment block, a Capture declaration, redaction state, and contiguous 0-based Events whose `seq` is the only evidence address.
- R4 (prd FR-6): `agentproof run` writes each Scenario's redacted Trace in Canonical form into the Output Directory, byte-identical across platforms for the same input.
- R5 (prd FR-7): A Trace file is validated on import against a supported Schema Version, with ordering, size, and format errors reported without a traceback, and `agentproof trace validate` exits 0 or 2 accordingly.
- R6 (prd FR-9): No content of a Trace is ever executed, fetched, rendered as markup, or passed to a shell; Replay makes no network call and spawns no subprocess, verified by test.
- R7 (prd FR-10, FR-17): Six built-in Assertions are registered, each validating its own configuration at load and producing exactly one Assertion Result with an Assertion id, a four-valued Status, a message, and Evidence; an exception inside an Assertion becomes an `error` result.
- R8 (prd FR-11, FR-12, FR-13): `tool_called`, `tool_not_called`, and `tool_call_count` behave per their acceptance criteria, treat an empty Trace as missing evidence, and state the Capture declaration in negative results.
- R9 (prd FR-14, FR-15, FR-16): `tool_arguments_match` matches dotted paths by JSON value, `tool_order` orders first occurrences with intervening Events allowed, and `final_output_contains` matches a literal substring case-sensitively by default against text or the compact Canonical form of structured output.
- R10 (prd FR-18): Evaluation of a Scenario fans out one result per Assertion, interprets `skip`, an absent Trace, and an execution failure in a fixed precedence, evaluates every Assertion in declared order, and folds statuses as `failed` over `error` over all-`skipped` over `passed`.
- R11 (prd FR-19): `agentproof trace replay` evaluates a named Scenario against a saved Trace with no agent, tool, model, or network call, produces the same result as the public API, and writes its own Report without overwriting a run's output.
- R12 (prd FR-20): The Fixture Agent returns scripted Traces from files referenced by the Suite and produces byte-identical Traces across runs when configured deterministic.
- R13 (prd FR-21): A synchronous Adapter protocol lets third parties execute an agent and return a Trace; Adapters cannot set Status, their exceptions become Scenario execution errors while the run continues, and a shipped conformance check validates what a generic test can observe.
- R14 (prd FR-22): Every run and Replay writes a JSON Report with its own Schema Version that embeds each Scenario's redacted Events, carries Assertion ids, messages, Evidence, counts, the Suite defaults snapshot, and differs between identical evaluations only in the listed volatile paths.
- R15 (prd FR-23): `agentproof report --format html` renders a single self-contained HTML file with no network resources, every value escaped, evidence-referenced Events expanded, status labels as text, missing and redacted values labeled, and a CSP meta tag.
- R16 (prd FR-25, FR-26): Any JSON Report serves as a Baseline; `agentproof compare` reports status, Assertion id, tool-sequence, selected-argument, and added or removed Scenario differences, excludes volatile paths, exits 1 only on a regression from `passed` to `failed` or `error`, and states that it compares saved data.
- R17 (prd FR-27, FR-28): Exit codes 0, 1, 2, 3, 4 are documented, each reachable by an integration test, with precedence 4, 2, 3, 1, 0; user-input errors print one line per violation with no traceback; a run with zero evaluated Assertions exits 1.
- R18 (prd FR-29, FR-30): The command set is `init`, `validate`, `run`, `trace validate`, `trace replay`, `compare`, `report`, `version`, with the signatures in spine AD-20; user input never becomes a path except a validated Scenario id inside fixed file names, and writes are temp-then-rename inside the Output Directory.
- R19 (prd FR-31): Redaction replaces configured keys, user paths, and the values of declared environment variables with a fixed marker at Trace ingress, before Evaluation and before any output, records what it redacted, and the limits are documented.
- R20 (prd FR-32): A copy-paste GitHub Actions workflow runs the Suite, renders the HTML Report, uploads the Output Directory on success and failure, and fails the job on a non-zero exit, with pinned actions and least privilege, running in the project's own CI with no secrets.
- R21 (prd FR-33): A README quick start and reference docs exist, every documented command executes in CI against the built wheel, the §5 limits are stated, and three external testers reach a passing and a failing run in under five minutes.
- R22 (prd FR-34): The public Python API is exactly the names in spine AD-15, imports no framework SDK, and evaluates identically to the CLI.
- R23 (prd FR-24, FR-35): JUnit XML and the TypeScript viewer are deferred; `report --format junit` is rejected with exit 2 in v0.1, and no viewer package or JavaScript tooling exists until the viewer starts.
- R24 (prd NFR-1): Same Trace bytes, Suite, and package version produce byte-identical results and Reports after stripping volatile paths, verified by golden files on Linux and Windows.
- R25 (prd NFR-2, NFR-5): No `eval`, `exec`, pickle, shell, or unsafe deserialization anywhere; YAML rejects custom tags, duplicate keys, aliases, and multi-document streams; files over the size limit are rejected before parsing; every malformed-input class in NFR-5 has a test and a clear error.
- R26 (prd NFR-3, NFR-4): Core Evaluation, Replay, Report, and Comparison make no network calls; no telemetry; no upload; Traces are treated as sensitive by default.
- R27 (prd NFR-6, NFR-7): Supported on Linux, macOS, and Windows for Python 3.12 and later; CI tests Linux and Windows; a basic run needs only the installed wheel with four runtime dependencies.
- R28 (prd NFR-8): Every serialized artifact carries an integer Schema Version; readers accept only a listed set; JSON Schemas are generated from the models and drift fails CI; releases follow 0.x semver with the pre-1.0 policy documented.
- R29 (prd NFR-9): Every Assertion has pass, fail, invalid-configuration, and missing-evidence tests; every exit code, malformed-input class, and secret-leak path has an integration test; one end-to-end test runs the spec §12.4 chain; CI runs lint, type check, tests, wheel build, and a clean-environment install.
- R30 (prd NFR-10): A 10,000-Event Trace evaluates against a 20-Assertion Scenario in under two seconds on the CI runner, and its HTML Report stays under 10 MB using the collapse rule.
- R31 (prd §8 pivot criterion): Before Trace-workflow work starts, five to ten developer interviews on hypotheses H1 to H4 are recorded; fewer than three would-be adopters pauses the initiative at the assertion engine and reopens positioning.

## Constraints

- C1 (spine AD-1, AD-2): Functional core, imperative shell, with the dependency direction and forbidden imports enforced by import-linter and ruff in the single check entry point; nothing in the core touches files, clocks, ids, environment, or threads.
- C2 (spine AD-3, AD-4, AD-5): Frozen, forbid-unknown models without Pydantic strict mode; timestamps as validated strings; integer Schema Versions; generated JSON Schemas; contiguous `seq`; Final Output on `agent_finished`; required Capture declaration.
- C3 (spine AD-6, AD-7, AD-20): One status fold, one exit-code module, exits only in `cli/app.py`; the error taxonomy in `errors.py`; the exact CLI signatures in AD-20.
- C4 (spine AD-8): Assertion config models and the static discriminated union in `models.assertions`; evaluators in `assertions.builtin`; one YAML form; ids assigned in `models.suite`.
- C5 (spine AD-9, AD-13, AD-18): The runner owns run identity, drives one pipeline for run and Replay, is the only caller of `build_report` and `write_atomic`, and runs sequentially in one process.
- C6 (spine AD-10, AD-11, AD-12, AD-19): One redaction function and one text scrubber; Canonical and compact forms with one volatile-path list; stdlib HTML rendering with the escaping and CSP rules; one safe YAML loader and constant size limits.
- C7 (spine AD-14, AD-15, AD-16, AD-17): Fixed artifact names; the public API list and parse/load split; four runtime dependencies; claims verified by the named tests; one check entry point mirrored by CI across Python 3.12 to 3.15 on Linux and Windows.
- C8 (prd §5, spec §5.1): No hosted service, accounts, billing, telemetry, runtime enforcement, LLM judge, database, message broker, or more than one real Adapter in v0.1.
- C9 (prd OQ-1, OQ-2): No install command or distribution name is published until the name decision is recorded, and no LICENSE file until the license is confirmed.
- C10 (spec §13.2, AGENTS.md): Short-lived branches with pull requests even when solo; `main` stays releasable; every story inherits the Definition of Done in spec §19.

## Done when

- A clean `pip install` of the built wheel, then `agentproof init`, `agentproof run`, `agentproof report --format html`, `agentproof trace replay`, and `agentproof compare` complete the spec §12.4 chain with no credentials, on Linux and Windows CI (R2, R4, R11, R15, R16, R29).
- The example GitHub Actions workflow in this repository fails on a deliberately failing Scenario and uploads a JSON Report, an HTML Report, and redacted Traces as artifacts (R20).
- Three external testers each reach a passing and a failing run from the README in under five minutes, recorded (R21, SM-1).
- Every public claim in the README about determinism, replay, and redaction is backed by a named test in CI (R24, R6, R19, R29).
- The spec §13.3 release checklist is satisfied and a 0.1.0 wheel is published under the decided name (C9).
- The package has exactly four runtime dependencies and no network, database, or service dependency (R26, R27, C8).

## Boundaries

- Not a hosted service, not a runtime policy engine, not an agent framework, not an LLM evaluation platform, not a guarantee of safety, not a browser or desktop automation tool (prd §5).
- The TypeScript viewer (epic 10) and the real framework Adapter (epic 11) are optional in v0.1 and must never block epics 1 to 9.
- Tracer path across epics: scaffold and CI (epic 1) → models and schemas (epic 2) → `validate` on the example Suite (epic 3) → `run` with the Fixture Agent producing exit 1 on the failing Scenario (epic 4) → export and `trace replay` (epic 5) → JSON and HTML Reports (epic 6) → `compare` (epic 7) → the workflow blocks a PR (epic 8) → docs and hardening (epic 9).
- Touch point: PyPI — the distribution name and trusted publishing; owner: epic-01-repository-foundation-and-ci.
- Touch point: GitHub Actions — the project's own CI and the example workflow; owners: epic-01-repository-foundation-and-ci (CI) and epic-08-github-actions-example (example).
- Touch point: PROJECT_SPEC.md and AGENTS.md — updated when a decision changes them, never rewritten by a story.

## References

- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, sections 3 Glossary, 4 Features (FR and AC ids), 9 Non-Functional Requirements, 10 Open Questions
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, Invariants & Rules AD-1 to AD-20, Structural Seed, Capability → Architecture Map
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-001 to ADR-020 and Decisions explicitly not made
- spec — PROJECT_SPEC.md, sections 5.1, 12, 13, 19
- research — _bmad-output/initiative-agentproof-mvp/prd-agentproof/addendum.md, section A competitive evidence
- assessment — _bmad-output/initiative-agentproof-mvp/2026-10-22-context-assessment.md, section 4 risks

## Notes

- Open question: OQ-1 distribution name; blocks epic 1 story 1 (pyproject name) and every install command; the maintainer decides.
- Open question: OQ-2 license; blocks the LICENSE file in epic 1 and public launch in epic 9.
- Open question: OQ-3 whether one Adapter failure should exit 3 for the whole run; spine AD-6 implements the PRD default; epic 4 builds it as written.
- Open question: OQ-5 integer `version`, string timestamps, Final Output on `agent_finished`; epic 2 builds the spine defaults; confirm before epic 2 starts.
- Open question: OQ-7 argument path syntax; epic 4 builds dotted keys with list indexes.
- Open question: OQ-15 which real Adapter ships; gates epic 11 after the interviews in R31.
- Open question: ARCH-1 mypy or pyright; epic 1 story 2 builds mypy unless told otherwise.
- Open question: ARCH-6 minimum scrubbed secret length; epic 5 builds no floor.
- Decision (2026-10-22): the maintainer approved the whole backlog as sliced and delegated the open defaults to the Product Owner; the five spine defaults bound by stories stand as decided: mypy over pyright (ARCH-1), a `scripts/check.py` entry point invoked as `uv run check` (ARCH-4), 5 MB input limits per Suite, Trace, and Report file (OQ-12), integer `version` with RFC 3339 string timestamps and Final Output on `agent_finished` (OQ-5), no minimum scrubbed secret length (ARCH-6). Changing one later re-slices the story that binds it.
- Decision (2026-10-22): every leaf in epics 1 to 9 is `refined: true` on the maintainer's blanket approval; epics 10 and 11 stay unrefined behind their gates.
- Decision (2026-10-22): the distribution name (OQ-1) and license (OQ-2) remain the maintainer's own calls; they gate epic 9 stories 4 and 5 and nothing earlier.
- Assumption: epics 10 and 11 are planned thin with gating unknowns because the PRD defers the viewer to v0.3 and the Adapter to after user validation; their stories are written when the gate opens.
- Assumption: the pivot interviews (R31) are a human step placed as the first entry of epic 5, so epics 1 to 4 proceed regardless, as the PRD states.
- Decision (2026-10-22): the user named eleven epics in a fixed order; the slice follows it. Where the spine's dependency rules would cut differently is recorded in each epic's Notes.
- Decision (2026-10-22): `parse_trace` and `trace validate` are built in epic 4, not epic 5, because the Fixture Agent that epic 4's tracer needs reads Trace files; epic 5 owns export, redaction, and Replay.
- Decision (2026-10-22): `scrub_text` (the console scrubber) is built in epic 3 with the CLI console; the full `redact` function is built in epic 5; both live in `redaction/` per spine AD-10.
