# AgentProof: Repository, Tooling, and Spec Assessment

Date: 2026-10-22
Source of truth reviewed: `PROJECT_SPEC.md` (1245 lines, staged, uncommitted)
Produced by: bmad-project-context setup run. Nothing existing was modified; no product code was written.

---

## 1. Repository and tooling assessment

### Repository state

| Item | Finding |
|---|---|
| Branch | `main`, unborn (zero commits) |
| Index | `PROJECT_SPEC.md` staged. The earlier `PROJECT_SPEC.md.md` rename is gone from the index. |
| Untracked | `.agents/`, `.claude/`, `skills-lock.json` (from the BMAD install), now also `_bmad/`, `_bmad-output/`, `AGENTS.md` |
| Remote | none configured |
| Git identity | `user.name` = kamranhaq21; `user.email` is **unset** (commits will fail or pick a machine default) |
| `.gitignore` | none |
| `core.symlinks` | false. `.claude/skills/*` are symlinks to `.agents/skills/*`; Git on this machine will store them as text files containing the link path if committed. |
| LICENSE, README, CONTRIBUTING, SECURITY | none |

### Toolchain found on this machine versus what the spec asks for

| Tool | Spec asks | Found | Verdict |
|---|---|---|---|
| Python | 3.12+ initially | `python` on PATH is **3.11.6** (an Autosphere SDK interpreter, not a general install). uv manages 3.13.16 and 3.11.16; 3.12.5 is downloadable. | Must use `uv run` with `requires-python` pinned; do not rely on PATH `python`. |
| uv | lockfile + env management | **0.2.37 (Aug 2024)**. `uv run` and `uv python list` print "experimental" warnings. | Upgrade uv before EPIC A. Lockfile format and `uv run` semantics changed materially after 0.4. |
| pydantic / typer / rich / PyYAML / jsonschema / jinja2 | yes | present globally (pydantic 2.11.5, typer 0.16.0, rich 13.7.1, PyYAML 6.0.2, jsonschema 4.23.0, Jinja2 3.1.4) | Irrelevant for the project env; uv will resolve its own. Useful only to confirm these versions install on Windows. |
| pytest / ruff / mypy | yes | pytest 8.3.2, ruff 0.6.1, mypy 1.11.1 (global) | Same; project pins will govern. |
| pyright | "mypy or pyright" | not installed | Decision needed (see §3). |
| Node | LTS supported by Vite | **v25.9.0** (odd-numbered, not LTS) | Viewer is deferred anyway. If it starts, pin Node 22 LTS via `.nvmrc`/`engines`. |
| pnpm / corepack | pnpm workspace if viewer in monorepo | neither installed | Confirms the Python-only v0.1 layout recommendation. |
| git / gh | yes | git 2.54.0, gh 2.102.0 (authenticated; `gh search` worked) | OK. |

### Name availability (checked today)

| Registry | `agentproof` | Notes |
|---|---|---|
| PyPI | **taken** | v0.1.0 by Sarak Dahal: "pytest-based behavioral testing framework for AI agents". Same problem space. |
| PyPI | `agent-proof` | free (404) |
| npm | **taken** | "Trust scores for 7,000+ agent services" (different space) |
| GitHub | at least 5 repos named `agentproof`/`Agentproof` | Pseudo-Lab/Agentproof (6 stars, active Oct 2026) is the most visible. |

Spec §13.1 and §16 already say to confirm name availability. This is now a known blocker for any public install command, not a hypothetical.

### BMAD installation

- 30 project-scoped skills installed under `.agents/skills/`, symlinked into `.claude/skills/`; `_bmad/` scaffolding created by this run (scripts, config, `custom/.gitignore` protecting `*.user.toml`).
- Output folder: `_bmad-output/`. Active initiative: `initiative-agentproof-mvp` (set in the gitignored `_bmad/custom/config.user.toml`).
- `bmad-retrospective` failed to install from upstream (YAML parse error in its SKILL.md description). Upstream bug.
- A second, global copy of all skills exists under `~/.claude/skills/`. The project copy is the one in use. The global copy also holds three retired skills (`bmad-ticket` → now `bmad-agent-po`, `bmad-spec`, `bmad-correct-course`). The setup check flags these as duplicates and retired; removing them affects every project on this machine, so it was left for you to decide.

---

## 2. Project context / agent instructions

Written to `AGENTS.md` at the repo root inside the managed `<!-- bmad:context -->` block. Greenfield, so:

- Policy lines come from spec §4, §6.5, §7.2, §9, §11, §13.2 and from facts verified today (PyPI name, `RefResolver` behavior).
- Commands are explicit `TODO (EPIC A)` lines naming the decided stack, not guessed invocations. Refresh the block (`bmad-project-context` refresh) once `pyproject.toml` and CI exist so the commands become verified facts.
- The spec's own suggested `AGENTS.md` (§17.2) was used as input, not copied: its "read PROJECT_SPEC.md before implementation" line was narrowed to the sections that matter per task, because loading 1245 lines every session is paid every session and degrades instruction following.
- No "Known pitfalls" section was written. Pitfalls need observed agent mistakes; none exist yet. Record them with `bmad-project-context record` the moment one happens.
- `CLAUDE.md` was not created. Claude Code reads `AGENTS.md` directly in this setup; add a one-line `CLAUDE.md` containing `@AGENTS.md` only if a harness that needs it is introduced.

---

## 3. Decisions made versus decisions still open

### Made (stated in the spec; treat as binding unless a decision record changes them)

1. Product: scenario-first test runner for tool-using agents; post-run assertions, not runtime enforcement (§2.3, §11.2).
2. Local-first, no account, no telemetry, no hosted upload by default (§4, §11.3).
3. Deterministic assertions first; LLM-as-judge deferred to v0.3 and off by default (§4, §5.3).
4. Stack: Python 3.12+, uv, Pydantic, Typer, rich, safe YAML, pytest, ruff; GitHub Actions for CI (§9).
5. `src/` layout under `packages/python/src/agentproof/` with the module split in §7.3; core never imports a framework (§7.2).
6. Result statuses: `passed | failed | error | skipped`; errors and failures both exit nonzero (§10.2).
7. First assertions: `tool_called`, `tool_not_called`, `tool_call_count`, `tool_arguments_match`, `tool_order`, `final_output_contains` (§6.4, EPIC D).
8. Traces are data; replay never executes anything (§4 principle 7, §6.5).
9. Every serialized artifact carries a schema version independent of the package version (§10.1).
10. v0.1 excludes SaaS, auth, billing, viewer-as-must-have, multiple adapters (§5.1).
11. Branching: short-lived branches, PRs even solo, `main` releasable (§13.2).
12. Build process: AI agents with human review; small verifiable increments; EPIC A + B first (§17, §20).

### Open (the spec explicitly defers these, or contradicts itself, or is silent)

Schema and semantics:
- O1. Schema version format: the example uses `version: "1"` (string). Integer major only, or `major.minor`? How do scenario, trace, report, and package versions relate? (Spec §10.1 says they are independent but gives no scheme.)
- O2. Event identity: §6.3 requires a sequence index; §12.3 tests "duplicate event IDs". Is there an event `id` in addition to `sequence`? Which is authoritative for ordering and evidence references?
- O3. Timestamp format and timezone (§6.5 says "define"). Recommend RFC 3339 with mandatory offset, stored as strings, never naive datetimes.
- O4. Unknown fields: reject (`extra="forbid"`) or ignore for forward compatibility? AGENTS.md currently states forbid; confirm.
- O5. `tool_arguments_match` path language: JSONPath, JMESPath, dotted keys, or a tiny custom subset? Affects a dependency decision.
- O6. `tool_order`: are intervening events allowed? Spec says "define whether".
- O7. String matching case sensitivity and Unicode normalization for `final_output_contains`.
- O8. `final_output_matches` regex engine and limits: Python `re` has no timeout; options are pattern-length limits, a denylist of nested quantifiers, or the third-party `regex` module.
- O9. `final_output_json_schema`: which JSON Schema draft is supported, and how `$ref` is restricted (see risk R2.4).
- O10. What "final output" is when a trace has multiple `agent_finished` events or none.

CLI and reporting:
- O11. Exit code for `error` results: §6.1 proposes 1 = assertion failed, 3 = execution error. Does an assertion `error` map to 1 or 3?
- O12. Command naming: `agentproof trace replay` reads as "re-execute". Consider `trace evaluate` or `trace check` to match principle 11.
- O13. Run ID generation and report timestamps: UUIDs and wall-clock times make outputs non-reproducible byte-for-byte. Decide which fields are volatile and excluded from comparison and golden tests.
- O14. HTML report: Jinja2 with autoescape, or stdlib `html.escape` string assembly with no template dependency?
- O15. JUnit XML: v0.1 "should have" or v0.2? Spec lists it in both.

Repo and tooling:
- O16. Minimum Python: 3.12 as written, or 3.11 to widen adoption? (Dependencies allow either.)
- O17. Type checker: mypy or pyright (one only).
- O18. Monorepo layout now (§8) versus Python-only until the viewer starts (§9). Recommendation: Python-only; AGENTS.md states this.
- O19. Distribution and import name, given the PyPI collision. Candidates: `agent-proof` (free), or a different name entirely. Import name can stay `agentproof` only if the distribution name differs, which confuses users.
- O20. License: Apache-2.0 is the candidate, unconfirmed.
- O21. Where example traces and fixtures live and how real user traces are kept out of git (`.gitignore` policy).
- O22. Adapter protocol shape: sync or async; push (adapter emits events) or pull (runner asks adapter to run and return a trace).
- O23. Size limits for traces and reports (§11.1 says "limit or warn"): pick numbers.

Product validation:
- O24. The five differentiation hypotheses in §3.2 are untested. The spec says interview 5 to 10 developers before building beyond the spike. No evidence exists yet.

### Contradictions found in the spec

| Where | Contradiction | Recommended resolution |
|---|---|---|
| §8 vs §9 | §8 layout includes `package.json`, `pnpm-workspace.yaml`, `packages/viewer/`; §9 says avoid JS tooling for a Python-only MVP | Follow §9. Add JS only when the viewer starts. |
| §5.1 vs §5.3 | JUnit XML is "should have if time permits" in v0.1 and a v0.2 item | Treat as v0.2 unless v0.1 finishes early. |
| §6.1 vs §10.2 | Exit codes list "assertion failed" (1) and "execution error" (3) but result status `error` covers both missing data and internal problems | Define: assertion `error` → exit 1 with status visible in summary; adapter/IO failure → 3; uncaught → 4. Record as a decision. |
| §17.2 vs §4 principle 10 and size budget | Suggested AGENTS.md says read the full spec every time | AGENTS.md points to specific sections per task instead. |
| Title and §17 | Document addresses "OpenCode"; the harness here is Claude Code + BMAD | Harmless, but the final spec revision should be harness-neutral. |
| §6.4 "pure evaluation" vs `duration_under` | Durations come from the trace, so the assertion is pure, but across live runs the result is non-deterministic | Keep it, document that it is deterministic only on a saved trace. |

---

## 4. Risks

### R1. Trace privacy

- R1.1 Redaction is key-based (`api_key`, `token`, `password`, `authorization`, user paths). Secrets inside free-text fields (`llm_response` content, tool results, error messages, stack traces) will not be caught. The spec acknowledges this; the product must make it visible in every artifact, not just in docs.
- R1.2 Redaction happens "before writing artifacts", but terminal output, `--verbose`, rich tracebacks, and exception messages are also outputs. Pydantic validation errors echo the offending value by default.
- R1.3 Redaction must record what was redacted (field path and a marker) or replay and comparison will treat redacted traces as different from originals. Define a `[REDACTED]` placeholder and a per-event or per-trace redaction state, and decide whether redaction is one-way (it should be).
- R1.4 Example and fixture traces will be committed to the repo and to CI artifacts. Real user traces must not be. There is no `.gitignore` yet and no convention for a traces directory.
- R1.5 GitHub Actions artifact upload "even when tests fail" (§6.8) uploads traces to GitHub. Document that uploaded artifacts are visible to anyone with repo read access.
- R1.6 HTML report and viewer render untrusted trace content. Any string from a trace is an XSS vector if inserted unescaped, and any URL is a phishing vector if auto-linked. Never linkify; escape everything; add a CSP meta tag to the self-contained HTML.

### R2. Safe parsing

- R2.1 YAML: `yaml.safe_load` is the rule. Also cap document size and nesting, and reject anchors/aliases that expand pathologically (billion-laughs) or set a size limit on the raw text before parsing.
- R2.2 JSON traces: stdlib `json` is safe from code execution but not from memory exhaustion. Size limits (O23) must exist before any "large trace" claim.
- R2.3 Pydantic with `extra="forbid"` plus strict mode is the safest default. Note that Pydantic error messages include input values; sanitize before surfacing to users (ties to R1.2).
- R2.4 `jsonschema` with the deprecated `RefResolver` fetches remote `$ref`s over HTTP. The modern `referencing.Registry` path does not retrieve unless given a `retrieve` callable. A user-supplied schema must never trigger a network call. Covered in AGENTS.md policy.
- R2.5 Regex assertions: Python `re` has no timeout and catastrophic patterns hang the process. The spec says "prevent pathological regex where practical". Pick an approach (O8) before shipping `final_output_matches`.
- R2.6 Path handling: `--output` and `init [PATH]` must refuse to write outside the intended directory and must not follow attacker-controlled symlinks. Spec §11.1 asks for tests; make them part of EPIC C/F definition of done.
- R2.7 Environment variable substitution in scenario YAML is listed as "document if supported; do not implement implicitly". Default to not supporting it in v0.1.

### R3. Action replay

- R3.1 The word "replay" will be read as "re-execute the agent". Principle 11 defines it correctly, but the CLI command `trace replay` and the marketing line "reproduce failures" pull the other way. Users will file bugs expecting live re-runs. Rename the command (O12) and use "re-evaluate" in docs.
- R3.2 Nothing in the trace may be executed: this must be enforced structurally, not by convention. The trace model should contain no field whose type is callable, URL-to-fetch, or command, and `custom` event metadata must be a plain JSON object. Adapters are the only code path that runs anything, and the runner must never pass trace content back to an adapter.
- R3.3 An adapter "must not mark itself successful without valid result evidence" (§6.9). The protocol needs a shape that makes this impossible (adapter returns events; runner computes status), not a rule in docs.
- R3.4 "Reproduce failures" is only true for the assertion layer. A saved trace reproduces the evaluation of one past run; it does not reproduce the agent. The README draft in §14.4 says "reproduce failures" without this qualification.

### R4. Schema versioning

- R4.1 Four independent versions exist (scenario schema, trace schema, report schema, package). Without a written policy on day one, the first breaking change will be unmanageable. Decide O1 before EPIC B.
- R4.2 JSON Schema files in `schemas/` and Pydantic models can drift. Generate the JSON Schemas from the Pydantic models and add a test that the committed files match the generated output.
- R4.3 `extra="forbid"` plus a version field means old readers reject new-version artifacts cleanly (good) but also means every additive field is a schema bump. Decide whether minor additive changes bump a minor number that readers tolerate.
- R4.4 §10.1 says "test old fixtures against current readers". That requires keeping every historical fixture in the repo from v1 of the schema onward. Start the fixture archive at the first tagged schema.
- R4.5 Baseline files are also a persisted schema. Comparing a baseline written by an older version against a current result needs the same versioning discipline.

### R5. Claims about deterministic evaluation

- R5.1 "Deterministic" is true only for: same trace bytes + same scenario + same package version → same assertion results. It is not true across live agent runs, and `duration_under` is not stable even on re-recording. Every public claim must carry the first qualification.
- R5.2 Determinism of outputs (byte-identical reports) requires sorted keys, fixed float formatting, no wall-clock fields in compared sections, stable event ordering by sequence index, and no reliance on set or dict iteration order. Golden-file tests are the only way to keep this true.
- R5.3 Baseline comparison of "tool-call sequence" between two live runs will flap for any agent that is not fully deterministic. The MVP must compare saved results, and the docs must say that comparing two live runs is a statistical question the tool does not answer (§6.6 already says so; keep it).
- R5.4 Assertion evaluation must be pure (no clock, no randomness, no I/O). `required_metadata`, `duration_under`, and `run_completed` all read trace fields, which is fine; the risk is a future assertion that reads the environment. Enforce with a test that evaluates every built-in assertion twice and compares results.
- R5.5 Unicode and case handling (O7) can make "deterministic" string matching behave differently on Windows versus Linux CI if normalization is not explicit. The development machine is Windows; CI will likely be Linux. Test both.

### R6. Delivery and project risks

- R6.1 Name collision on PyPI with a same-space package. Launch messaging and install docs are blocked until resolved.
- R6.2 Git identity unset and no remote; the first commit will carry a wrong or empty email.
- R6.3 uv 0.2.37 is old enough that lockfiles and `uv run` behave differently from current docs and from CI runners that install latest uv.
- R6.4 Windows development, Linux CI: path separators, symlinks (`core.symlinks=false`), line endings (no `.gitattributes`), and timezone defaults will all surface. Add `.gitattributes` and `.editorconfig` in EPIC A.
- R6.5 The four-week plan assumes the five differentiation hypotheses hold. Zero user evidence exists. The spec itself says to interview before building beyond the spike.
- R6.6 The symlinked `.claude/skills/` directory, if committed from this machine, becomes 30 text files for collaborators on other platforms. Decide whether to commit `.agents/` and `.claude/` at all, or gitignore them and have contributors install BMAD themselves.

---

## 5. Proposed BMAD artifact plan and next workflow

The spec is already a PRD-and-more. Running `bmad-prd` to create another PRD would duplicate it. The plan below uses the spec as the input to the ticket tree and spends BMAD effort where the spec is weakest: unresolved design decisions and executable stories.

| Step | Skill | Input | Output | Status |
|---|---|---|---|---|
| 0 | `bmad` setup | installed skills | `_bmad/`, config, active initiative `initiative-agentproof-mvp` | done today |
| 1 | `bmad-project-context` | spec | `AGENTS.md` managed block | done today (refresh after EPIC A) |
| 2 | `bmad-agent-po` (Sofia) | `PROJECT_SPEC.md` | fills `initiative-agentproof-mvp.md` requirements; records the "made" decisions above as constraints and the "open" ones as questions | next |
| 3 | `bmad-architecture` | initiative + §3 of this doc | architecture spine with one AD per open decision O1 to O23 that affects EPIC A/B/C/D; dependency rules from §7.2 made checkable | after 2 |
| 4 | `bmad-agent-po` | initiative + spine | slice into epics (reuse A to H from spec §18) and write stories for EPIC A and EPIC B only | after 3 |
| 5 | `bmad-build` + `bmad-code-review` | one story at a time | code, tests, review | after 4 |
| 6 | `bmad-project-context` refresh | repo with `pyproject.toml` and CI | verified commands replace the TODO lines | after EPIC A lands |
| 7 (parallel, optional) | `bmad-deep-recon` competitive | §3 competitor list, especially the PyPI `agentproof` package, DeepEval, Promptfoo, Inspect AI | evidence for or against the five hypotheses and for the naming decision | any time |
| 8 (optional) | `bmad-forge-idea` | the "replay" and "deterministic" promises | pressure-test the two claims most likely to be challenged publicly | before launch messaging |

Deliberately skipped: `bmad-prd` (the spec is the PRD; use its validate mode later only if you want an outside critique), `bmad-ux` (no UI in v0.1), `bmad-product-brief` (§1 and §2 of the spec already serve as one).

### Next recommended workflow

Invoke Sofia with `bmad-agent-po` and ask her to write the initiative from `PROJECT_SPEC.md`, pointing her at §3 of this document so the open questions become explicit requirements questions rather than silent assumptions. Before that, two five-minute housekeeping items will save pain later:

1. Set `git config user.email` and add a `.gitignore` (at minimum `.venv/`, `_bmad/custom/*.user.toml` is already covered, build output, local traces).
2. Decide whether `.agents/`, `.claude/`, and `skills-lock.json` are committed or ignored.
