---
title: AgentProof v0.1
status: final
created: 2026-10-22
updated: 2026-10-22
source: PROJECT_SPEC.md (staged, uncommitted, 2026-10-22)
---

# PRD: AgentProof v0.1
*Working title. The name is not final; see OQ-1.*

## 0. Document Purpose

This PRD is for the maintainer, the architecture spine (`bmad-architecture`), and the Product Owner slicing epics and stories (`bmad-agent-po`). It condenses `PROJECT_SPEC.md` into requirements with stable IDs and testable acceptance criteria (AC-n.m under each FR). It does not restate the spec's implementation plan, module layout, or technology choices; those live in `addendum.md` and the architecture spine. Vocabulary is fixed in §3 Glossary. Inferences the maintainer has not confirmed are tagged `[ASSUMPTION]` inline and indexed in §11. Market and competitor statements are hypotheses (§8) unless a source is cited. The context assessment at `../2026-10-22-context-assessment.md` records the tooling state and risk register this PRD builds on. Every story sliced from this PRD inherits the Definition of Done in spec §19 and the quality gates in spec §12.5.

## 1. Vision

AI agents call tools, change state, and make multi-step decisions; a fluent final answer proves none of that happened correctly. Few teams have a repeatable, repository-local way to check that the agent still calls the right tools, with the right arguments, in the right order, and never calls the forbidden ones. The tools that offer such checks (§8 H6) tie them to a test framework, a server, or a hosted account.

AgentProof is a local-first test runner for agent behavior. A developer writes a Scenario in YAML, runs an agent (or loads a saved Trace), and gets a deterministic Evaluation of the recorded Trace, a Report a reviewer can read, a Baseline to compare the next run against, and an Exit Code a pull-request check can act on. The agent itself may behave differently on every Run; the Evaluation of what it did does not. The bet, contingent on OQ-19: no server and no account. A Suite file and a Trace file are the whole integration surface, so any stack that can write the Trace format can be tested, and any CI job can gate on the result.

v0.1 wins when a developer can answer three questions in one workflow: what did my agent do, did it follow my explicit rules, and did the latest change make it worse. Everything else, including hosted history, runtime enforcement, and LLM-judged scoring, is deliberately out of scope until repeat community use proves the core workflow.

## 2. Target User

### 2.1 Jobs To Be Done

- **Catch a behavioral regression before merge.** "My prompt change must not stop the agent from calling `reject_expense` on over-limit requests." Functional, and the job the whole product is built around.
- **Prove a forbidden action did not happen.** "Show me evidence the agent never called `approve_expense`, not just that it said 'rejected'." Functional, with a compliance flavor.
- **Debug a failure from evidence, not from re-running.** "I have the Trace from the failing CI job; let me evaluate new Assertions against it without paying for another model call." Functional and cost-driven.
- **Keep tests next to the code.** "Scenarios live in my repo, run in my CI, and need no account." Contextual: the user is already in a Git and GitHub Actions workflow.
- **Explain a failure to someone who did not write the agent.** "A reviewer or lead reads the Report and understands which rule broke and where in the Trace." Social.

### 2.2 Non-Users (v0.1)

- Teams wanting a hosted dashboard, shared run history, or team permissions.
- Teams needing runtime prevention of unsafe tool calls. AgentProof observes after the fact; it does not intercept.
- Users evaluating answer quality by rubric or LLM judge. Deterministic Assertions only in v0.1.
- Non-Python stacks. The Python package is the only runtime in v0.1; other stacks can only produce a Trace file for offline Evaluation. `[ASSUMPTION: a TypeScript or Go agent team is a secondary audience reached through the Trace format, not through a native SDK.]`

### 2.3 Key User Journeys

- **UJ-1. Dana blocks a regression in a pull request.** Dana, an AI application engineer at a fintech startup, maintains an expense-approval agent. A teammate's prompt change lands as a PR. The GitHub Actions job runs `agentproof run`, the `reject-over-limit` Scenario fails on `tool_not_called: approve_expense`, the job exits 1, and the PR check turns red. Dana opens the uploaded HTML Report, in which the agent's API key is already redacted, sees Event 7 is the offending tool call with its arguments, and asks for the change to be fixed. Realized by FR-12, FR-18, FR-22, FR-23, FR-27, FR-31, FR-32.
- **UJ-2. Marcus turns a bug report into a permanent test.** Marcus maintains an MCP server and gets a user report that a client agent called `delete_file` before `confirm_with_user`. The user attached a Trace exported from their adapter. Marcus runs `agentproof trace validate`, writes a `tool_order` Assertion, runs Replay against the saved Trace with no model credentials, sees the Assertion fail on the recorded evidence, and commits Suite and Trace as a regression test. Realized by FR-7, FR-9, FR-15, FR-18, FR-19.
- **UJ-3. Priya compares two runs after a model upgrade.** Priya, an automation engineer, upgrades the model behind a browser-automation agent. She runs the Suite and keeps the JSON Report as a Baseline, upgrades, runs again, and runs `agentproof compare`. The Comparison shows one Scenario changed from passed to failed and two Scenarios whose tool-call sequence differs, with the standing note that sequence differences between live Runs may be sampling variation rather than regression. She shares the current JSON Report with her lead. Realized by FR-22, FR-25, FR-26.
- **UJ-4. Lee tries AgentProof in five minutes.** Lee, an engineering lead evaluating tools, runs `pip install`, `agentproof init`, and `agentproof run` on the generated example, which uses the built-in Fixture Agent and needs no API key. One Scenario passes, one deliberately fails, and the terminal summary explains why. Realized by FR-4, FR-20, FR-27, FR-28, FR-30, FR-33.

## 3. Glossary

- **Scenario** — One named test case: an input for the agent, a list of Assertions, and an optional `skip: "<reason>"`. Belongs to exactly one Suite. Has a unique id within its Suite.
- **Suite** — A YAML file declaring a Schema Version, Suite defaults, and one or more Scenarios.
- **Suite defaults** — Suite-level settings inherited by every Scenario: `adapter` (which Adapter runs the Scenarios), `fail_on_missing_trace` (default `true`), `compare.include_arguments` (argument paths included in Comparison), and `redact` (keys, paths, and environment variable names; FR-31). `[ASSUMPTION: this is the v0.1 defaults set]`
- **Trace** — The recorded evidence of one agent Run: run-level metadata plus an ordered list of Events. Serialized as JSON with a Schema Version. A Trace is data and is never executed.
- **Event** — One entry in a Trace: an event type (for example `tool_call`, `tool_result`, `agent_finished`, `exception`), a sequence index, and optional timestamp, duration, tool name, arguments, result, status, error information, redaction marker, and metadata conforming to a documented schema.
- **Capture declaration** — An optional run-level Trace field in which the Adapter states what it could observe, for example `tool_calls: complete | partial | unknown`. Negative Assertions report it in their message (FR-12).
- **Final Output** — The agent's terminal text or structured output, carried by the `agent_finished` Event. `[ASSUMPTION: location of Final Output in the Trace is a schema decision; OQ-5]`
- **Assertion** — A typed, declarative check applied to a Trace (for example `tool_called`). Has an Assertion id, a type, and validated configuration, and produces one Assertion Result.
- **Assertion id** — The name of an Assertion within its Scenario: user-supplied `id`, defaulting to `<type>-<declared index>`. Used by Reports and Comparison.
- **Assertion Result** — The outcome of one Assertion: the Assertion id, a Status, a human-readable message, and Evidence.
- **Status** — One of `passed`, `failed`, `error`, `skipped`. `error` means the Assertion could not be evaluated (missing or invalid evidence, or an execution failure); it is never a pass. `skipped` arises only from a Scenario-level `skip: "<reason>"` field or from an absent Trace with `fail_on_missing_trace: false` (FR-18); nothing else produces it.
- **Evidence** — References to the Events (by sequence index) that support an Assertion Result.
- **Evaluation** — Applying every Assertion of a Scenario to one Trace, producing an Evaluation Result. Pure: same Trace, same Scenario, same package version give the same Evaluation Result.
- **Evaluation Result** — Scenario-level outcome: the Assertion Results, a Scenario Status, and summary counts. A Suite-level Evaluation Result aggregates Scenario results into a Suite Status.
- **Suite Status** — The aggregate of Scenario Statuses for one run of a Suite, computed with the AC-18.1 precedence, from which the Exit Code is derived (FR-27).
- **Run** — One execution of an agent that produces a Trace. A live Run calls an Adapter; Replay does not.
- **Replay** — Evaluation of a Scenario against a saved Trace. Replay never calls an agent, a tool, a model, or the network.
- **Adapter** — Code implementing the Adapter protocol to execute an agent for a Scenario input and return a Trace. Framework SDKs are optional dependencies of Adapters only.
- **Fixture Agent** — A built-in deterministic Adapter that returns scripted Traces, used for examples and tests without credentials.
- **Report** — A rendering of an Evaluation Result: JSON (machine-readable, embeds the Trace Events it judged) or HTML (self-contained, human-readable, rendered from the JSON Report).
- **Output Directory** — The directory, given by `--output` or defaulted, into which a run writes its JSON Report and Traces.
- **Baseline** — A JSON Report kept as the reference side of a Comparison. There is no separate Baseline file format.
- **Comparison** — The diff between a Baseline and a current JSON Report.
- **Redaction** — Replacing configured secret-like values in a Trace with a fixed marker as soon as the Trace enters the runner, before Evaluation and before any write or terminal output, recorded as redaction state on the artifact and a redaction marker on each affected Event. A live Run and a Replay of its exported Trace therefore evaluate identical data.
- **Canonical form** — The one serialization used for every written JSON artifact and every determinism test: UTF-8 without BOM, LF newlines, keys sorted, two-space indent, non-ASCII preserved, floats written by shortest round-trip repr, and the volatile fields (run id, timestamps, durations, cost) listed in the Report reference.
- **Schema Version** — The version identifier carried by every serialized Suite, Trace, and Report, independent of the package version.
- **Exit Code** — The process exit status of the CLI, mapped from Suite Status and run outcome (FR-27).

## 4. Features

### 4.1 Scenario definition

**Description:** A developer writes a Suite in YAML, checks it into the repository, and validates it before running. Loading is safe by construction: no custom tags, no object instantiation, strict rejection of unknown fields and unknown Assertion types. Realizes UJ-1, UJ-2, UJ-4.

#### FR-1: Load a Suite from YAML safely
The system can load a Suite file using safe YAML loading only.
- AC-1.1 A Suite containing a YAML custom tag (for example `!!python/object`) is rejected with an error naming the file and line; no object is instantiated.
- AC-1.2 A Suite or Trace file exceeding a configured size limit is rejected before parsing with an error naming the limit. `[ASSUMPTION: default limit 5 MB; OQ-12]`
- AC-1.3 Environment variable substitution is not performed; a `${VAR}` literal is passed through unchanged and documented as such.
- AC-1.4 Duplicate mapping keys at any level are rejected naming the key and line; PyYAML's silent last-wins merge is disabled.
- AC-1.5 YAML aliases are either disallowed or bounded so that a document under the size limit cannot expand beyond a documented node count; a billion-laughs fixture is rejected before model validation. `[ASSUMPTION: aliases disallowed in v0.1]`
- AC-1.6 A Suite file containing more than one YAML document is rejected naming the line of the second document marker.

#### FR-2: Validate a Suite against its Schema Version
The system can validate a loaded Suite against the schema for its declared Schema Version and report every violation.
- AC-2.1 A Suite with no `version` field is rejected with an error naming the missing field.
- AC-2.2 A Suite with an unknown field at any level is rejected, naming the field path. `[ASSUMPTION: the spec requires strict rejection of unknown Assertion types only; rejecting all unknown fields is a fail-closed generalization; OQ-5]`
- AC-2.3 A Suite with a missing required field is rejected, naming the field path and the Scenario id when applicable.
- AC-2.4 `agentproof validate SUITE_PATH` exits 0 on a valid Suite and 2 on an invalid one, printing all violations, not only the first.
- AC-2.5 Scenario ids match `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`, are unique within a Suite when compared case-insensitively, and are not a Windows reserved device name (`CON`, `NUL`, `COM1`, and the rest), so they are safe as file names on every supported platform (FR-29); anything else is rejected naming the id.

#### FR-3: Enforce Scenario and Assertion integrity
The system rejects Suites whose Scenarios or Assertions are ambiguous.
- AC-3.1 Two Scenarios with the same id in one Suite, or two Assertions with the same Assertion id in one Scenario, are rejected, naming the id.
- AC-3.2 An Assertion with an unregistered type is rejected, naming the type and the Scenario id.
- AC-3.3 An Assertion whose configuration fails its own validation (for example `tool_call_count` without an integer) is rejected with the field path.

#### FR-4: Scaffold an example project
`agentproof init [PATH]` creates a runnable example Suite, a Fixture Agent configuration, and a saved Trace, with no credentials required. Realizes UJ-4.
- AC-4.1 Running `init` in an empty directory then `run` on the generated Suite completes without network access and without any provider or AgentProof-specific environment variables set.
- AC-4.2 `init` refuses to overwrite existing files and exits 2 naming the first conflicting path. `[ASSUMPTION: no `--force` in v0.1; OQ-17]`

### 4.2 Trace model and import/export

**Description:** Every Run produces a Trace; every Trace can be written to and read from JSON. Imported Traces are validated before any Evaluation touches them. The Trace format is the integration surface for teams on other stacks. Realizes UJ-2.

#### FR-5: Versioned Trace model
The system defines a Trace with run-level fields (Schema Version, run id, Scenario id, start and end timestamps, agent and adapter metadata, optional model and provider metadata, Events, result summary, optional source revision, optional environment metadata) and Events as defined in the Glossary.
- AC-5.1 Provider name and model name are optional; a Trace without them validates.
- AC-5.2 The documented event types are accepted; an undocumented event type is rejected naming the type and sequence index. `[ASSUMPTION: event type set is the spec §6.3 list: agent_started, agent_finished, tool_call, tool_result, llm_request, llm_response, exception, approval_requested, approval_granted, approval_denied, custom]`
- AC-5.3 Timestamps, when present, must be RFC 3339 strings with an explicit UTC offset; a naive timestamp is rejected. `[ASSUMPTION: OQ-5]`
- AC-5.4 The Event metadata schema, and the rule that `llm_request` carries metadata only whereas `llm_response` content is redaction-sensitive, are documented in the Trace reference.
- AC-5.5 Environment metadata is populated only from a documented allowlist (package version, Python version, operating system, optional source revision); process environment variables, hostnames, and user names are never captured.
- AC-5.6 The Trace carries an optional Capture declaration; the Fixture Agent sets `tool_calls: complete`, and an Adapter that omits it is treated as `unknown`.

#### FR-6: Export a Trace as JSON
The system can write a Trace to a JSON file conforming to the published JSON Schema for its Schema Version.
- AC-6.1 Every exported Trace validates against `schemas/trace-v<N>.schema.json`.
- AC-6.2 Export writes the Canonical form, so exporting the same Trace twice produces byte-identical files on Linux and Windows; files are always opened with explicit UTF-8 encoding and newline handling.
- AC-6.3 Export writes the already-redacted Trace (FR-31); no unredacted Trace is ever written.
- AC-6.4 `agentproof run` writes each Scenario's Trace into the Output Directory under a documented name derived from the Scenario id, so a failing CI run leaves the evidence needed for Replay (UJ-2).

#### FR-7: Import and validate a Trace
The system can read a Trace from JSON and validates it against its declared Schema Version before use.
- AC-7.1 A Trace with a Schema Version the package does not support is rejected naming both versions.
- AC-7.2 A Trace with duplicate sequence indexes, or with Events not in ascending sequence order, is rejected naming the first offending index.
- AC-7.3 A Trace file that is not valid JSON, or exceeds the size limit (AC-1.2), is rejected with an error naming the file and the reason; no stack trace is printed.
- AC-7.4 `agentproof trace validate TRACE_PATH` exits 0 on a valid Trace and 2 otherwise.

#### FR-8: Preserve ordering and evidence addressing
Events keep their sequence index through import, Evaluation, Report, and Comparison, so Evidence always points to the same Event.
- AC-8.1 An Assertion Result's Evidence indexes resolve to the same Events in the JSON Report and the HTML Report as in the source Trace.

#### FR-9: Treat Trace content as inert data
No field of a Trace is ever executed, fetched, rendered as HTML, or passed to a shell or interpreter.
- AC-9.1 A Trace whose tool arguments, results, or metadata contain shell commands, URLs, script tags, or Python expressions produces identical Evaluation behavior to a Trace with plain strings, and the HTML Report shows them as escaped text.
- AC-9.2 Replay (FR-19) performs zero network calls and spawns zero subprocesses, verified two ways: an in-process test that makes socket creation and subprocess spawning raise, and a CI job that runs the example Suite inside a container started with networking disabled.

### 4.3 Assertion engine

**Description:** Assertions are typed, registered, and evaluated by pure functions over the Trace. Missing evidence is an `error`, never a pass. Test coverage per Assertion is set by NFR-9. Realizes UJ-1, UJ-2.

#### FR-10: Assertion registry
The system maintains a registry of Assertion types; a Suite may only use registered types.
- AC-10.1 The six built-in Assertions (FR-11 to FR-16) are registered by default.
- AC-10.2 Each registered type validates its own configuration at Suite load time (FR-3).

#### FR-11: `tool_called`
Passes when at least one `tool_call` Event with the given tool name exists.
- AC-11.1 Passes with Evidence listing every matching Event index.
- AC-11.2 Fails when the Trace has Events but no matching one; the message names the tool and lists the distinct tools that were called.
- AC-11.3 Errors when the Trace contains no Events. `[ASSUMPTION: an empty Trace is treated as missing evidence for every tool Assertion; OQ-6]`

#### FR-12: `tool_not_called`
Passes when no `tool_call` Event with the given tool name exists.
- AC-12.1 Fails with Evidence listing every matching Event index.
- AC-12.2 Passes on a Trace with Events but no match.
- AC-12.3 Errors when the Trace contains no Events. `[ASSUMPTION: an empty Trace cannot prove absence; OQ-6]`
- AC-12.4 The result message states the Trace's Capture declaration; when it is `partial` or `unknown`, the message says the absence proof is limited to what the Adapter observed, and the Report shows the same label. The same applies to `tool_call_count` with `less_than`.

#### FR-13: `tool_call_count`
Passes when the number of `tool_call` Events for the tool satisfies the configured comparison (`equals`, `greater_than`, `less_than`) against a non-negative integer. With `less_than`, the result message states the Capture declaration as in AC-12.4.
- AC-13.1 Each operator has a passing and a failing test.
- AC-13.2 Configuration without exactly one operator is rejected at load time.
- AC-13.3 Errors when the Trace contains no Events, consistent with AC-12.3 (OQ-6).

#### FR-14: `tool_arguments_match`
Passes when, for at least one `tool_call` Event with the given tool name, each configured argument path matches its expected value exactly.
- AC-14.1 Nested paths are addressed with a documented path syntax. `[ASSUMPTION: dotted keys with integer list indexes, for example `items.0.amount`; OQ-7]`
- AC-14.2 Matching compares JSON values by value: numbers compare numerically (`1` equals `1.0`); strings, booleans, and null compare exactly; a number never matches a string (`5` and `"5"` do not match). Objects and arrays match by deep equality.
- AC-14.3 Errors when no `tool_call` Event with that tool name exists; the message distinguishes "tool never called" from "called with different arguments". `[ASSUMPTION: a never-called tool is missing evidence rather than a mismatch; OQ-6]`
- AC-14.4 A configured path absent from every matching call's arguments is a `failed` result whose message names the absent path.

#### FR-15: `tool_order`
Passes when the configured list of tool names occurs as `tool_call` Events in the given relative order.
- AC-15.1 Intervening Events between the listed tools are allowed by default. `[ASSUMPTION: a `strict: true` option requiring adjacency is deferred; OQ-8]`
- AC-15.2 Fails naming the first tool found out of order, with Evidence for every tool in the list that was found.
- AC-15.3 Errors when any listed tool was never called. `[ASSUMPTION: absence is an error, not a failure, so the message points at the missing call rather than a misleading ordering]`
- AC-15.4 When a listed tool is called more than once, the first occurrence of each tool is the one ordered, so the Trace `[delete_file, confirm_with_user, delete_file]` fails the order `[confirm_with_user, delete_file]`. The semantics are documented with that example. `[ASSUMPTION: first-occurrence semantics; OQ-8]`

#### FR-16: `final_output_contains`
Passes when the Final Output exists and contains the configured literal substring.
- AC-16.1 Matching is case-sensitive by default with a `case_sensitive: false` option. `[ASSUMPTION: OQ-9]`
- AC-16.2 Structured (non-string) Final Output is compared against its Canonical form text. `[ASSUMPTION: OQ-9]`
- AC-16.3 Errors when no `agent_finished` Event exists or it carries no Final Output.

#### FR-17: Assertion Result semantics
Every Assertion produces exactly one Assertion Result with an Assertion id, a Status, a message, and Evidence.
- AC-17.1 Status is one of the four Glossary values; no other value is serializable.
- AC-17.2 Evaluating the same Assertion against the same Trace twice yields byte-identical Assertion Results.
- AC-17.3 An exception raised inside an Assertion is caught and converted to an `error` result carrying the exception type and message, never a traceback to the user.
- AC-17.4 Every Assertion Result carries the Assertion id of the Assertion that produced it.

### 4.4 Evaluation, Replay, and Adapters

**Description:** The runner applies every Assertion of each Scenario to a Trace. The Trace comes from a live Run through an Adapter, or from a file in Replay. Use `run` when AgentProof drives the agent (through a real Adapter or the Fixture Agent); use `trace replay` when the Trace was produced elsewhere, such as a CI run, another stack, or a user's bug report. The Fixture Agent makes every example and test runnable without credentials. Realizes UJ-1, UJ-2, UJ-4.

#### FR-18: Evaluate a Scenario against a Trace
The system evaluates all Assertions of a Scenario against one Trace and produces an Evaluation Result.
- AC-18.1 Scenario Status is `failed` if any Assertion `failed`, `error` if none failed and any errored, `skipped` if every Assertion skipped, otherwise `passed`. Suite Status uses the same precedence over Scenario Statuses. `[ASSUMPTION: failed outranks error for the Scenario Status; OQ-3]`
- AC-18.2 A Trace is absent when the Adapter returns none for a live Run, or when the Trace file named for Replay does not exist. With `fail_on_missing_trace: true` (the default) an absent Trace produces an `error` Scenario Status; with `false` it produces `skipped`. It never produces `passed`.
- AC-18.3 Assertions are evaluated in declared order and every Assertion is evaluated even after an earlier failure.
- AC-18.4 A Scenario with `skip: "<reason>"` produces `skipped` for every Assertion and the reason appears in the summary and Report.
- AC-18.5 A run in which no Assertion was evaluated (every Scenario skipped) exits 1 with a message naming the cause, so a renamed Trace directory cannot turn CI green; if any absence counted as an execution failure (AC-27.3), that code wins. `[ASSUMPTION: OQ-3]`

#### FR-19: Replay a saved Trace
`agentproof trace replay TRACE_PATH --suite SUITE_PATH --scenario SCENARIO_ID` evaluates the named Scenario against the saved Trace with no agent, tool, model, or network call. `[NOTE FOR PM: the verb "replay" invites the reading "re-execute"; the spec defines it deliberately (principle 11) and uses it throughout; see OQ-4 on renaming.]`
- AC-19.1 Completes with no API keys present and with network access disabled.
- AC-19.2 Produces the same Evaluation Result as evaluating the Trace through the public API (FR-34).
- AC-19.3 Exits with the same Exit Code mapping as `run` (FR-27).
- AC-19.4 Writes a JSON Report named `replay-<scenario id>.report.json` into the Output Directory, so it never overwrites the Report a `run` produced (FR-22).

#### FR-20: Fixture Agent
A built-in Adapter returns scripted Traces read from referenced Trace JSON files, so the Suite schema never embeds the Trace schema.
- AC-20.1 The `init` example Suite uses the Fixture Agent and includes one passing and one deliberately failing Scenario.
- AC-20.2 The Fixture Agent produces byte-identical Traces across runs when the Suite fixes timestamps and derives the run id from the Scenario id.

#### FR-21: Adapter protocol
The system defines a small Python protocol an Adapter implements to execute an agent for a Scenario input and return a Trace.
- AC-21.1 The protocol is importable from the public API (FR-34) without importing any framework SDK.
- AC-21.2 An Adapter cannot set Scenario Status; the runner computes Status only from Assertion Results.
- AC-21.3 An exception raised by an Adapter yields a Scenario Status of `error` with the exception type and message, the Suite continues with the next Scenario, and the run is marked as having an execution failure (FR-27).
- AC-21.4 v0.1 ships the Fixture Agent and the Adapter protocol. A real-framework Adapter ships in v0.1 only if OQ-15 is decided before the release branch; otherwise own-agent users implement the protocol or export a Trace. `[NON-GOAL for MVP: more than one real Adapter]`
- AC-21.5 An Adapter must surface every tool call it observes or raise; silently dropping Events is a documented protocol obligation that each Adapter's own tests cover against a known agent. A generic conformance test suite checks what it can observe: the returned Trace validates, carries a Capture declaration, keeps sequence order, and Adapter exceptions propagate. Each Adapter documents its known limitations.

### 4.5 Reports

**Description:** Every Evaluation produces a JSON Report; an HTML Report is rendered from it. Both carry the Events they judged, show missing or redacted data explicitly, and never render Trace content as markup. Realizes UJ-1, UJ-3.

#### FR-22: JSON Report
`agentproof run` and `trace replay` write a JSON Report containing Schema Version, Suite and run identifiers, per-Scenario Status, every Assertion Result with Assertion id, message, and Evidence, each Scenario's Trace Events, summary counts, and optional timing and cost.
- AC-22.1 The Report validates against a published JSON Schema with its own Schema Version.
- AC-22.2 Reports are written in Canonical form; two Reports of the same Evaluation differ only in the listed volatile fields (run id, timestamps, durations, cost), verified by a golden-file test that strips exactly those fields.
- AC-22.3 Summary counts (passed, failed, error, skipped) equal the counts of the listed Assertion Results.
- AC-22.4 The Report embeds each Scenario's Trace Events after Redaction, so a Report alone is enough to show Evidence and to serve as a Baseline.

#### FR-23: HTML Report
`agentproof report REPORT_PATH --format html` renders a single self-contained HTML file from a JSON Report.
- AC-23.1 The file loads with no network requests (no remote scripts, styles, fonts, or images).
- AC-23.2 Every string from the Trace or Suite appears only as escaped element content or inside a quoted attribute; nothing from a Trace is placed in `<title>`, `<style>`, an unquoted attribute, or an `href`/`src`, and URLs are never linkified. If the JSON Report is embedded in a `<script type="application/json">` block, `</` is escaped as `<\/`. The page carries a `Content-Security-Policy` meta tag of `default-src 'none'; style-src 'unsafe-inline'`. Test vectors include `<script>`, `</script>`, quotes in attribute position, and a `javascript:` URL, each rendering as visible text.
- AC-23.3 Status labels are text, not color alone, and each Scenario's failing Assertions are listed with their Evidence Event indexes.
- AC-23.4 Each Scenario shows its Events in sequence order with type, tool name, and arguments, so a reader can find the Event an Evidence index points at (UJ-1).
- AC-23.5 Missing and redacted values are labeled as such, not shown as empty.
- AC-23.6 `report` writes `<report name>.html` next to the JSON Report by default; `--output PATH` overrides; the file is written per AC-29.3.

#### FR-24: JUnit XML Report `[NON-GOAL for MVP unless time permits]`
`agentproof report --format junit` maps Assertion `failed` to test failures and `error` to test errors with correct XML escaping.
- AC-24.1 Deferred; see §6.2. Listed here so the FR id is stable.

### 4.6 Baseline comparison

**Description:** A developer keeps a JSON Report as a Baseline and compares a later Report against it. Comparison is exact or normalized comparison of saved data. It makes no statistical claim and never compares two live runs as if they were deterministic. Realizes UJ-3.

#### FR-25: Use a JSON Report as a Baseline
Any JSON Report of a supported Schema Version can serve as a Baseline; no separate command or format is needed.
- AC-25.1 `compare` accepts two JSON Report paths and rejects, with exit 2, a file that is not a valid Report, naming the reason.
- AC-25.2 The quick start shows the two-command flow: `run --output baseline/` once, then `run` and `compare`.

#### FR-26: Compare Baseline and current Report
`agentproof compare BASELINE_REPORT CURRENT_REPORT` reports differences in Suite Status, per-Scenario Status, failed Assertion ids, tool-call sequence (tool names in sequence order), selected arguments, and missing or additional Events; duration and cost are reported only when present on both sides.
- AC-26.1 Run id, timestamps, and durations are excluded from the equality decision by default.
- AC-26.2 Comparing a Report against itself reports no differences and exits 0.
- AC-26.3 A Scenario present on one side only is reported as added or removed, not as an error.
- AC-26.4 Exit Code is 1 when any Scenario regressed from `passed` to `failed` or `error`, 0 otherwise. `[ASSUMPTION: improvements and sequence-only changes are reported but do not fail the Comparison by default; OQ-10]`
- AC-26.5 Argument comparison covers only the paths listed under the Suite defaults `compare.include_arguments`; by default no arguments are compared. `[ASSUMPTION: OQ-10]`
- AC-26.6 The output states that it is an exact comparison of saved data, never a claim about agent reproducibility.

### 4.7 Command-line interface

**Description:** The CLI is the primary surface. It must be usable by a person reading `--help` and by a CI job reading the Exit Code. Realizes UJ-1, UJ-4.

#### FR-27: Stable Exit Codes
Every command exits with a documented code: 0, every non-skipped Assertion passed and at least one was evaluated; 1, one or more Assertions failed or errored, or no Assertion was evaluated (AC-18.5); 2, invalid configuration or input; 3, execution or integration error; 4, internal unexpected error.
- AC-27.1 Each code has an integration test that triggers it through the CLI; code 4 is triggered through a documented, test-only fault-injection environment variable that is ignored in release builds unless explicitly enabled. `[ASSUMPTION]`
- AC-27.2 A run whose Assertion Results include `error` but no execution failure exits 1. `[ASSUMPTION: an unevaluated rule is not a passed rule; OQ-3]`
- AC-27.3 A run exits 3 when an Adapter raised for any Scenario (AC-21.3), an Adapter could not be loaded, a Trace was absent with `fail_on_missing_trace: true` or could not be read, or a Report could not be written; this takes precedence over 1. An absent Trace with `fail_on_missing_trace: false` is a skip, not an execution failure.
- AC-27.4 Precedence when several conditions hold: 4, then 2, then 3, then 1, then 0. `[ASSUMPTION: OQ-3]`
- AC-27.5 Exit Codes are documented in the CLI reference before the first release.

#### FR-28: Actionable errors and output
User-input errors print a one-line message with file and field context and no stack trace; `--verbose` adds diagnostics; every run ends with a summary of passed, failed, error, and skipped counts.
- AC-28.1 Malformed YAML, malformed JSON, missing file, and unknown Assertion type each produce an error with no traceback unless `--verbose` is set.
- AC-28.2 All terminal output, log lines, and exception messages (including those surfaced by AC-17.3 and AC-21.3) pass through Redaction (FR-31) before printing, at any verbosity. Verified by a test that plants one value both under a redacted key and in a `redact.env` variable, then places it in an Adapter exception message, and asserts it is scrubbed from captured output. A value present only under a key is not expected to be caught in free-text exception messages; AC-31.4 documents that limit.
- AC-28.3 `--help` on every command lists its arguments, options, and Exit Codes.

#### FR-29: Safe output paths
`--output` and `init [PATH]` may point anywhere the user chooses, but nothing escapes the chosen directory.
- AC-29.1 Files written inside the Output Directory are named from Scenario ids (constrained by AC-2.5) and fixed suffixes; no name from a Suite or Trace is used as a path in any other way.
- AC-29.2 A symlink inside the Output Directory that points outside it is not followed; the write is refused with exit 3.
- AC-29.3 Reports and Traces are written to a temporary file in the Output Directory and then renamed over the target; if the rename fails (for example a locked file on Windows), the run exits 3 naming the file and leaves the temporary file for inspection. `[ASSUMPTION]`

#### FR-30: Command set
`init`, `validate`, `run`, `trace validate`, `trace replay`, `compare`, `report`, `version` are implemented in v0.1; a command ships only with integration tests covering its documented behavior.
- AC-30.1 `agentproof run SUITE_PATH [--adapter NAME] [--output DIR]` runs every Scenario; `--adapter` overrides the Suite defaults `adapter`; the Output Directory defaults to `./agentproof-output/`. `[ASSUMPTION: flag names and default directory; OQ-16]`
- AC-30.2 `agentproof version` prints the package version and the supported Suite, Trace, and Report Schema Versions.

### 4.8 Redaction

**Description:** Traces are sensitive by default. As soon as a Trace enters the runner, configured secret-like keys, user-specified paths, and the exact values of named environment variables are replaced with a marker; Evaluation, terminal output, and every artifact then see only the redacted Trace. Redaction is one-way. It is key-based plus declared-value-based; the product never claims it catches an undeclared secret embedded in free text. Realizes UJ-1.

#### FR-31: Configurable Redaction
The system replaces, in Trace Events and Final Output, the values of configured keys (default set: `api_key`, `token`, `password`, `authorization`, plus user-specified paths) and every occurrence of the current value of each environment variable named under `redact.env` (for example `OPENAI_API_KEY`) with a fixed marker, before Evaluation and before any output.
- AC-31.1 Default keys are matched case-insensitively at any nesting depth in arguments, results, and metadata. `[ASSUMPTION]`
- AC-31.2 The artifact carries redaction state listing the paths that were redacted and the names (never values) of environment variables whose values were scrubbed, and each affected Event carries a redaction marker.
- AC-31.3 A test plants one known value under a redacted key in arguments, results, and metadata, and plants the value of a named environment variable in Final Output and in a tool result; it asserts neither value appears in any written artifact or captured terminal output.
- AC-31.4 Documentation states that Redaction covers configured keys and declared environment values only, that Assertions see the redacted Trace, and that users must inspect artifacts before sharing.

### 4.9 CI integration

**Description:** A copy-paste GitHub Actions workflow runs the Suite, keeps Reports and Traces as artifacts even on failure, and fails the job on Assertion failure, with no hosted account. Realizes UJ-1.

#### FR-32: GitHub Actions example workflow
The repository ships a workflow that checks out the repository, installs a supported Python, installs AgentProof, runs the Suite, renders the HTML Report from the JSON Report, uploads the Output Directory (JSON Report, HTML Report, redacted Traces) as an artifact on success and failure, and fails the job when the Exit Code is non-zero.
- AC-32.1 The workflow runs in the project's own CI against the example Suite using the Fixture Agent and no secrets, and the uploaded artifact contains the HTML Report UJ-1 opens.
- AC-32.2 The workflow pins action versions and declares least-privilege permissions.
- AC-32.3 Documentation explains how to run with saved Traces and the Fixture Agent so no model credentials are needed in CI, and states that uploaded artifacts are visible to anyone with read access to the repository's Actions.

### 4.10 Documentation, examples, and public API

**Description:** The quick start is a product requirement, not an afterthought: a stranger must reach a working run without help. The Python API is the second surface after the CLI and is what Adapters and test suites import. Realizes UJ-4.

#### FR-33: Quick start and examples
The repository ships a README quick start, an expense-policy example, and reference pages for the Suite format, Assertions, Traces, CLI, and security limits.
- AC-33.1 Every install and usage command in the docs is executed in CI against the wheel built in that CI run, never against a package fetched from PyPI by name (H7).
- AC-33.2 A first-time user reaches a passing and a failing run from the quick start in under five minutes, measured with at least three external testers before release. `[ASSUMPTION: five minutes is the spec's target; the measurement protocol is OQ-14]`
- AC-33.3 The README states the limits in §5 verbatim or by reference: no reproducibility of stochastic runs, no runtime enforcement, key-based Redaction only.

#### FR-34: Public Python API
The package exports a small, documented API: the Suite, Scenario, Trace, Event, Assertion Result, and Evaluation Result models; functions to load a Suite, load a Trace, and evaluate a Scenario against a Trace; and the Adapter protocol.
- AC-34.1 Importing the public API imports no framework SDK and makes no network call.
- AC-34.2 Evaluating through the API and through the CLI produce the same Evaluation Result for the same inputs.
- AC-34.3 Symbols outside the documented public API are private and carry no stability promise before 1.0 (NFR-8). `[ASSUMPTION: final symbol names are an architecture decision; candidates in addendum §B]`

#### FR-35: TypeScript Trace viewer `[NON-GOAL for MVP]`
A React/Vite viewer that reads an exported JSON Report locally: run summary, Scenario list, Assertion Results, Event timeline, Event details, Comparison. Requirements carried from the spec for when it starts: no account, no network requests by default, untrusted values rendered as text never markup, keyboard navigation, a size limit or pagination for large Traces, useful empty and error states, no backend.
- AC-35.1 Deferred to v0.3 (§6.2). Listed so the id and the carried requirements are stable. `[NOTE FOR PM: the spec made this a v0.1 should-have "if core remains stable"; this PRD defers it because the HTML Report (FR-23) covers the v0.1 reading need.]`

## 5. Non-Goals (Explicit)

What AgentProof is not. Items deferred to a later version are listed in §6.2, not here.

- Not a hosted service: no accounts, authentication, billing, upload, telemetry, or shared run history in v0.1. The commercial tiers in the spec are not requirements of this PRD.
- Not a runtime policy engine: AgentProof detects that an action occurred after the fact. It does not intercept, block, or require approval for tool calls, and documentation never positions post-run tests as a substitute for access controls.
- Not an agent builder, orchestrator, or framework.
- Not a general LLM evaluation platform: no LLM-as-judge, rubric scoring, or prompt comparison in v0.1.
- Not a guarantee of safety or correctness, and not a claim of reproducing stochastic model behavior. Replay re-evaluates recorded evidence; it does not re-create the Run.
- Not a dozen framework integrations: at most one real Adapter in v0.1.
- Not a distributed or queued execution system; no Docker, database, or message broker required for a basic run.
- Not a browser or desktop automation tool.

## 6. MVP Scope

### 6.1 In Scope (v0.1)

- Python package, CLI, and public API (FR-27 to FR-30, FR-34).
- Suite loading and validation (FR-1 to FR-4).
- Versioned Trace model with JSON import and export (FR-5 to FR-9).
- Six built-in Assertions and the registry (FR-10 to FR-17).
- Evaluation, Replay, Fixture Agent, Adapter protocol and conformance tests (FR-18 to FR-21). A real-framework Adapter only per AC-21.4.
- JSON and self-contained HTML Reports (FR-22, FR-23).
- Baseline and Comparison (FR-25, FR-26).
- Key-based Redaction (FR-31).
- GitHub Actions example and docs (FR-32, FR-33).
- Unit, integration, malformed-input, and secret-leak tests, and one end-to-end acceptance test (NFR-9); AgentProof runs its own Suite in its own CI.
- SECURITY.md, CONTRIBUTING.md, and a license file once the license is confirmed (OQ-2).

### 6.2 Out of Scope for MVP

- JUnit XML (FR-24): deferred to v0.2 unless v0.1 finishes early. `[NOTE FOR PM: the spec lists it in both v0.1 "should have" and v0.2; this PRD picks v0.2.]`
- TypeScript/React Trace viewer (FR-35): deferred to v0.3. No root `package.json` or pnpm workspace until it starts.
- Additional Assertions (`final_output_matches`, `final_output_json_schema`, `run_completed`, `no_unhandled_exception`, `duration_under`, `required_metadata`, `event_exists`, `event_not_exists`): v0.2, driven by user feedback. Regex and JSON Schema Assertions need the safety decisions in OQ-11 first.
- Second and later Adapters, storage backend abstraction, dataset organization, run labels, and Scenario selection on `run` (`--scenario ID`, tags): v0.2 and later.
- Statistical comparison across multiple Runs, flaky-test diagnostics: v0.3.
- Optional LLM judge (disabled by default): v0.3.
- Schema migration tooling: only when a breaking schema change requires it.

## 7. Success Metrics

The spec's first-month numbers are illustrative targets, not predictions. Measurement is manual or from public GitHub data; no telemetry exists.

**Primary**
- **SM-1: Time to first successful run.** Minutes from `pip install` to a passing and a failing example run. Target: under 5 minutes for 3 of 3 external testers before release. Validates FR-4, FR-20, FR-33.
- **SM-2: Regression caught in CI.** The launch demo PR is blocked by a declared Assertion failure, reproducible by a stranger from the sample repository. Target: achieved before launch. Validates FR-27, FR-32.
- **SM-3: Own-agent adoption.** Distinct GitHub accounts that, within 30 days of launch, open an issue, discussion, or PR showing a Suite or Trace for their own agent, or reply to the launch survey saying so. Target: 5. Validates FR-5, FR-7, FR-21, FR-34.

**Secondary**
- **SM-4: Repeat use.** Distinct GitHub accounts with a second interaction (issue, discussion, PR, or survey) at least a week after their first, within 30 days. Target: 3. Validates the thesis in §8 (H1, H3).
- **SM-5: Developers who report running the example.** Survey responses and discussion posts in the first month. Target: 100. Clone counts are not used; they include bots and cover only 14 days.
- **SM-6: External feedback items.** Bug reports that reproduce, or feature requests that lead to a merged change or an accepted §6.2 item, within 30 days. Target: 10.
- **SM-7: Reported installation or quick-start failures.** Absolute count of distinct reports in the first month, because no denominator exists without telemetry. Target: under 5, each answered within a week.

**Counter-metrics (do not optimize)**
- **SM-C1: GitHub stars.** Stars are discovery, not value; rising stars with flat SM-4 means fix usability, not marketing. Counterbalances SM-5.
- **SM-C2: Number of Assertion types or Adapters shipped.** More surface before SM-4 is evidence of building the platform before the workflow is proven. Counterbalances SM-3.
- **SM-C3: Features claimed in the README.** Every claim must be backed by a tested command (AC-33.1). Counterbalances SM-1 pressure to over-promise.

## 8. Hypotheses and Evidence

**Status at 2026-10-22:** H6 (competitive wedge) largely refuted; H7 (name) refuted for PyPI; H8 and H9 supported with caveats; H1 to H5 untested pending interviews.

All market and competitor claims in the spec are hypotheses until supported by evidence. The spec itself requires interviews with 5 to 10 developers before building beyond the spike. Evidence gathered on 2026-10-22 by an automated web-research pass is summarized in `addendum.md` §A with sources. It is desk research, not user research: it can refute an availability claim (H7) or show a feature already exists (H6), but it cannot confirm demand. The table below states only what that evidence changes.

Pivot criterion: EPIC A to D (package, contracts, engine, six Assertions) proceed regardless, because they are the minimum needed to show anyone anything. Before EPIC E (Trace workflow) starts, the interviews for H1 to H4 must have happened; if fewer than 3 of the interviewed developers would adopt the §1 combination over Promptfoo, EvalView, or agentevals for their own agent, work pauses at EPIC D and OQ-19 is reopened. `[ASSUMPTION: threshold and gate point]`

| Id | Hypothesis (from spec §3) | Evidence status (2026-10-22) | Validation step |
|---|---|---|---|
| H1 | Developers want a simpler CLI for agent action contracts than existing evaluation frameworks offer. | Hypothesis. No user interviews yet. | Interview 5 to 10 developers before EPIC E starts (pivot criterion above). |
| H2 | Replaying a saved Trace against new Assertions is valuable enough to adopt a Trace format. | Hypothesis. | Same interviews; count how many have saved traces today. |
| H3 | Developers want agent tests checked into the same Git repository as the code. | Hypothesis, consistent with how unit tests are kept; no direct evidence. | Interviews; inspect how competitor users store suites. |
| H4 | Small projects prefer a local-first tool over a hosted observability platform. | Hypothesis. | Interviews; competitor issue trackers. |
| H5 | A GitHub Actions integration can drive adoption. | Hypothesis. | Track SM-2 and workflow-related issues after launch. |
| H6 | The competitive wedge (scenario-first, deterministic action assertions, offline Replay, local CLI, versioned Trace schema, PR gate) is not already covered by DeepEval, Promptfoo, Inspect AI, Langfuse, or LangSmith. | **Largely refuted by an automated research pass (addendum §A, sources listed, spot-check before citing).** Deterministic tool-call assertions and a CI gate already exist in Promptfoo (`trajectory:*` asserts), DeepEval (`ToolCorrectnessMetric`), LangChain `agentevals`, and EvalView, which markets itself as "regression testing for AI agents, snapshot behavior, diff tool calls, catch regressions in CI". Offline re-scoring of saved logs exists in Inspect AI and in LangSmith's platform. No single tool found in the pass combines all of: YAML Scenarios, a versioned framework-neutral Trace file format, Replay from a file with no server, and a self-contained HTML Report. `[NOTE FOR PM: the wedge is narrower than the spec assumes. Decide whether the combination is the product thesis or whether positioning changes before EPIC E starts.]` | Hand-verify the four closest tools (Promptfoo, agentevals, EvalView, the PyPI `agentproof`) against FR-11 to FR-19 before any comparative statement. Add "why not EvalView or Promptfoo" to the interview script for H1. |
| H7 | The name "AgentProof" is available. | **Refuted for PyPI**: `agentproof` 0.1.0 (MIT, 2026-02-17, apparently dormant) is published by another author as a pytest-based agent testing framework that overlaps on tool assertions, JSONL trace replay, and a GitHub Action (checked 2026-10-22). `agent-proof` is free. npm `agentproof` is taken by an unrelated project. | Decide OQ-1 before any install command is published. |
| H8 | A project-specific Trace schema is the right integration surface (spec §6.3). | Supported with a caveat: the OpenTelemetry GenAI semantic conventions (`invoke_agent`, `execute_tool` spans) are the convergence point but had no stable release as of the research pass; OpenInference is a parallel vocabulary. A versioned AgentProof Trace is defensible if it documents an import mapping from both. | Decide OQ-18 before FR-5 is finalized. |
| H9 | Developers want to test agent behavior in CI at all. | Supported weakly: practitioner surveys and papers from 2025 to 2026 (addendum §A) rank reliability as the top agent development challenge and report low confidence that updates improve results; no issue-tracker requests were found. Not evidence for AgentProof specifically. | Interviews (H1); track SM-3 and SM-4. |

## 9. Non-Functional Requirements

### NFR-1: Determinism of Evaluation
Same Trace bytes, same Suite, same package version produce byte-identical Evaluation Results and JSON Reports in Canonical form, after stripping the listed volatile fields. Verified by golden-file tests that run on Linux and Windows CI with the golden files stored with LF endings and `.gitattributes` protecting them from autocrlf. Supports FR-17, FR-22.

### NFR-2: Security of parsing and rendering
No `eval`, `exec`, pickle, shell execution, or unsafe deserialization anywhere in the package. YAML via safe loading only. HTML output escapes all untrusted content. A user-supplied JSON Schema (when the v0.2 Assertion lands) must never trigger remote `$ref` retrieval. Verified by test and by a lint rule where practical.

### NFR-3: No network in core
Core Evaluation, Replay, Report, and Comparison make no network calls. Only an explicitly configured non-fixture Adapter may. Cost appears in a Report only when an Adapter supplies it; the core ships no pricing table and performs no lookup. Verified as in AC-9.2.

### NFR-4: Privacy defaults
Local-only execution; no telemetry; no upload. Traces are treated as sensitive: Redaction is applied before any write when configured, and docs tell users to inspect artifacts before sharing. If telemetry is ever proposed, it is opt-in and a separate PRD.

### NFR-5: Input size and robustness
Suite, Trace, and Report files above a configured size limit are rejected before parsing with an error naming the limit. Empty Traces, missing Final Output, duplicate or out-of-order sequence indexes, invalid timestamps, unknown event types, null versus absent fields, Unicode and multiline content, and malformed JSON or YAML each have a test and a clear error.

### NFR-6: Portability
Supported on Linux, macOS, and Windows for the supported Python versions; CI tests at least Linux and Windows. `[ASSUMPTION: the spec names no operating systems; the maintainer develops on Windows and CI runners are Linux, so both are tested. Minimum Python is 3.12 per spec; OQ-13]` Path handling, line endings, and timezone handling must not change Evaluation Results across platforms.

### NFR-7: Installation footprint
A basic run needs only `pip install` (or `uv`) of the package: no Docker, Redis, database, Node, or account. Runtime dependencies are limited to the set in `addendum.md` §B; each addition needs a stated reason.

### NFR-8: Public contract stability
Every serialized Suite, Trace, and Report carries its own Schema Version as a single integer. A reader supports a documented set of versions and rejects any other (AC-7.1); unknown fields are rejected at every version (AC-2.2), so any field addition is a new integer version. `[ASSUMPTION: integer versions with forbid-unknown; the `major.minor` alternative was considered and withdrawn (addendum §C); OQ-5]` Breaking schema changes require a documented migration note and a fixture-compatibility test. Package releases follow semantic versioning; before 1.0, public API stability is best-effort and documented as such. Exit Codes and CLI output formats are documented before each release and changed only with tests and docs updated together.

### NFR-9: Test discipline
Each Assertion has tests for pass, fail, invalid configuration, and missing evidence. Every Exit Code, every malformed-input class in NFR-5, and secret leakage (AC-31.3, AC-28.2) are covered by integration tests. One end-to-end acceptance test runs the spec §12.4 chain in sequence: clean install, `init`, passing run, failing run with non-zero exit, Report generation, Replay without credentials, Comparison of a changed run against its Baseline, and inspection of every artifact for a planted secret. AgentProof's own CI runs lint, type check, tests, package build, and a clean-environment install. Each story inherits the Definition of Done and quality gates named in §0.

### NFR-10: Performance
A Trace of 10,000 Events evaluates against a 20-Assertion Scenario in under 2 seconds on the CI runner. The HTML Report for that Trace is under 10 MB, renders Events referenced by Evidence expanded, and collapses the rest beyond the first 500 per Scenario with a pointer to the JSON Report, so AC-23.4 holds without client-side scripting. `[ASSUMPTION: numbers chosen to set a bound, not from measurement; OQ-12]`

## 10. Open Questions

Phase-blockers (must be decided before architecture or EPIC B) are marked **[B]**. Blockers: OQ-1, OQ-3, OQ-5, OQ-7, OQ-18.

1. **OQ-1 [B] Distribution and import name.** PyPI `agentproof` is taken by a same-space project (H7). Options: `agent-proof` on PyPI with import name `agentproof`, or a new name. Owner: maintainer. Blocks: README, FR-33, FR-32.
2. **OQ-2 License.** Apache-2.0 is the candidate; contributor policy and dependency-license review pending. Blocks: §6.1 license file, public launch.
3. **OQ-3 [B] Status precedence and Exit Codes.** Confirm: `failed` outranks `error` at Scenario level (AC-18.1); Assertion-only errors exit 1 (AC-27.2); execution failures exit 3 and outrank 1 (AC-27.3, AC-27.4); a run with zero evaluated Assertions exits 1 (AC-18.5). Trade-off: a single Adapter raise masks Assertion failures in the Exit Code, though the Report still lists them; the alternative keeps per-Scenario raises at 1 and reserves 3 for Adapter load, Suite read, and Report write failures. Blocks: FR-18, FR-27.
4. **OQ-4 Command name for Replay.** Keep `trace replay` (matches the spec's defined term and marketing) or rename to `trace evaluate`/`trace check` to avoid the "re-execute" reading (FR-19 note). Blocks: CLI docs; cheap to change before release. The addendum §C lean to rename is a proposal, not a decision.
5. **OQ-5 [B] Timestamp, Schema Version format, and Final Output location.** Assumed: RFC 3339 with offset (AC-5.3); integer Schema Versions with unknown fields rejected (NFR-8), which makes every additive field a new version. Alternative: `major.minor` with additive tolerance, which conflicts with AC-2.2. Does Final Output live on `agent_finished` or at run level? Blocks: FR-5, FR-6, FR-7, NFR-8.
6. **OQ-6 Empty-Trace and never-called semantics.** AC-11.3, AC-12.3, AC-13.3, AC-14.3 treat an empty Trace or a never-called tool as `error`. Alternative: `failed` for positive Assertions, `passed` with a warning for negative ones. Blocks: FR-11 to FR-14.
7. **OQ-7 [B] Argument path syntax for `tool_arguments_match`.** Assumed: dotted keys with list indexes (AC-14.1). Alternatives: JSONPath or JMESPath, each adding a dependency. Blocks: FR-14, AC-26.5.
8. **OQ-8 `tool_order` adjacency and repeated tools.** Assumed: intervening Events allowed and first-occurrence ordering (AC-15.1, AC-15.4). Alternatives: every occurrence must respect the order; a `strict` adjacency option. Blocks: FR-15 docs.
9. **OQ-9 String matching defaults.** Assumed: case-sensitive, no Unicode normalization, canonical JSON for structured output (AC-16.1, AC-16.2). Blocks: FR-16 docs; NFR-6 cross-platform determinism.
10. **OQ-10 Comparison failure and argument policy.** Should tool-sequence changes without Status change fail `compare` (AC-26.4)? Is "no arguments by default" the right `compare.include_arguments` default (AC-26.5)? Blocks: FR-26.
11. **OQ-11 Regex and JSON Schema safety policy** for the v0.2 Assertions `final_output_matches` and `final_output_json_schema`: pattern limits versus third-party engine; schema draft and `$ref` policy. Not blocking v0.1; blocks v0.2 design.
12. **OQ-12 Size limits and performance bounds.** Default file size limit (AC-1.2) and the NFR-10 numbers need a decision or a measurement. Blocks: NFR-5, NFR-10.
13. **OQ-13 Minimum Python version.** 3.12 per spec, or 3.11 to widen adoption; dependencies allow either. Blocks: NFR-6, FR-32.
14. **OQ-14 Quick-start measurement protocol.** How SM-1 is measured (screen-recorded sessions, self-report, timed task). Blocks: SM-1 acceptance.
15. **OQ-15 Which real Adapter, if any, ships in v0.1** (AC-21.4). Decided after interviews (H1 to H4). Blocks: FR-21 scope, SM-3.
16. **OQ-16 Output Directory default and Trace hygiene.** Assumed: default `./agentproof-output/` (AC-30.1). Open: which directories hold committed example Traces versus local Traces that must be gitignored. Blocks: FR-4, FR-6, docs, `.gitignore`.
17. **OQ-17 Should `init` offer `--force`?** AC-4.2 assumes no. Low impact.
18. **OQ-18 [B] Relationship of the Trace model to OpenTelemetry GenAI and OpenInference span conventions.** Options: native AgentProof schema with a documented import mapping (assumed), or adopt the OTel attribute names directly despite their unstable status (H8). Blocks: FR-5, FR-7, and the Adapter protocol (FR-21).
19. **OQ-19 Positioning against EvalView, Promptfoo trajectory asserts, and agentevals** (H6). Is the combination of YAML Scenarios, versioned Trace file, file-based Replay, and HTML Report the thesis, or does the product need a different wedge? Blocks: §1 wording, README and launch messaging; does not block EPIC A or B.

## 11. Assumptions Index

- §2.2 — Non-Python stacks are a secondary audience reached through the Trace format only.
- §3 Suite defaults — The v0.1 defaults set is `adapter`, `fail_on_missing_trace`, `compare.include_arguments`, and `redact`.
- §3 Final Output — Carried by the `agent_finished` Event (OQ-5).
- AC-1.2 — Default Suite/Trace size limit 5 MB (OQ-12).
- AC-1.5 — YAML aliases disallowed in v0.1.
- AC-2.2 — All unknown fields rejected, generalizing the spec's rule for Assertion types (OQ-5).
- AC-4.2 — `init` has no `--force` in v0.1 (OQ-17).
- AC-5.2 — Event type set equals spec §6.3 list.
- AC-5.3 — Timestamps are RFC 3339 with explicit offset (OQ-5).
- AC-11.3 — Empty Trace is missing evidence for every tool Assertion (OQ-6).
- AC-12.3 — `tool_not_called` on an empty Trace is `error` (OQ-6).
- AC-14.1 — Argument paths use dotted keys with integer list indexes (OQ-7).
- AC-14.3 — A never-called tool is missing evidence for `tool_arguments_match` (OQ-6).
- AC-15.1 — `tool_order` allows intervening Events; strict adjacency deferred (OQ-8).
- AC-15.3 — A listed tool never called makes `tool_order` an `error`, not a `failed`.
- AC-15.4 — `tool_order` orders the first occurrence of each tool (OQ-8).
- AC-16.1 — `final_output_contains` is case-sensitive by default (OQ-9).
- AC-16.2 — Structured Final Output is matched against its canonical JSON text (OQ-9).
- AC-18.1 — `failed` outranks `error` for Scenario Status (OQ-3).
- AC-18.5 — A run with zero evaluated Assertions exits 1 (OQ-3).
- AC-26.4 — Sequence-only changes and improvements do not fail `compare` (OQ-10).
- AC-26.5 — No arguments compared unless listed in `compare.include_arguments` (OQ-10).
- AC-27.1 — Exit code 4 is reached through a test-only fault-injection variable.
- AC-27.2 — Assertion-only errors exit 1 (OQ-3).
- AC-27.4 — Exit Code precedence 4, 2, 3, 1, 0 (OQ-3).
- AC-29.3 — Reports and Traces are written atomically.
- AC-30.1 — `run` flag names and default Output Directory `./agentproof-output/` (OQ-16).
- AC-31.1 — Default Redaction keys match case-insensitively at any depth.
- AC-33.2 — Five-minute quick start is the target; protocol undefined (OQ-14).
- AC-34.3 — Public API symbol names are an architecture decision.
- §8 pivot criterion — Interviews gate EPIC E; threshold 3 of the interviewed developers.
- NFR-6 — Linux, macOS, Windows supported; CI on Linux and Windows; minimum Python 3.12 (OQ-13).
- NFR-8 — Integer Schema Versions with unknown fields rejected (OQ-5).
- NFR-10 — Performance numbers are bounds set by judgment, not measurement (OQ-12).
