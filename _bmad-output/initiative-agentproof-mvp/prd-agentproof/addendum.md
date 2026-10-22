# PRD Addendum: AgentProof v0.1

Material that supports the PRD but belongs downstream (architecture spine, solution design, launch planning). Nothing here is a requirement; the PRD's FR and NFR ids are the only binding references.

## A. Competitive evidence digest (automated research pass, 2026-10-22)

Gathered by a web-research subagent in this run. Sources are listed per row; spot-check each before quoting publicly. "Unknown" means the pass could not confirm absence.

| Tool | License | Latest release seen | Tool-call assertions | Offline re-evaluation | CI gate | Local, no account | Sources |
|---|---|---|---|---|---|---|---|
| DeepEval | Apache-2.0 | 4.3.1, 2026-10-16 | yes: `ToolCorrectnessMetric`, deterministic core score, args/order options | partial/unknown: evaluates constructed test cases; no documented re-score-a-saved-trace CLI; trace evaluation tied to Confident AI | yes: `deepeval test run` in CI, non-zero exit on threshold | partial: account optional, many metrics need an LLM judge key | pypi.org/project/deepeval ; deepeval.com/docs/metrics-tool-correctness ; deepeval.com/guides/guides-regression-testing-in-cicd |
| Promptfoo | MIT (reported acquired by OpenAI Mar 2026; still OSS) | 0.124.1, 2026-10-08 | yes: `trajectory:tool-used`, `trajectory:tool-args-match`, `trajectory:tool-sequence`, `trajectory:step-count`, `trace-span-count` (OTel traces) | unknown: result caching exists; no documented re-grade-from-file mode found | yes: `promptfoo-action` with `fail-on-threshold` | yes: "evals run 100% locally" | github.com/promptfoo/promptfoo/releases ; promptfoo.dev/docs/configuration/expected-outputs/deterministic/ ; github.com/typpo/promptfoo-action |
| Inspect AI (UK AISI) | MIT | 0.3.283, 2026-10-21 | partial: text scorers built in; tool-event checks need a custom scorer | yes: `--no-score` then `inspect score` on logs | partial: CLI usable in CI, no first-party gate | yes: local logs | pypi.org/project/inspect-ai ; inspect.aisi.org.uk/scoring.html |
| Langfuse | MIT core (ee/ excepted) | Python SDK 5.0.4, 2026-10-21 | partial: code evaluators, no tool-call assertion library found | partial: evaluators run server-side on stored traces | yes: experiments in CI | partial: self-host needs a server | pypi.org/project/langfuse ; langfuse.com/docs/evaluation/overview |
| LangSmith + agentevals | client MIT, platform proprietary; agentevals MIT | langsmith 0.14.12, 2026-10-21 | yes: `agentevals` trajectory match strict/unordered/subset/superset, no LLM call | yes (platform): `evaluate_existing()` on stored runs | yes: pytest plugin | partial: agentevals offline, LangSmith needs account | github.com/langchain-ai/agentevals ; docs.langchain.com/langsmith/trajectory-evals |
| agentproof (PyPI, other author) | MIT | 0.1.0, 2026-02-17; repo praxiumlabs/agentproof, 1 commit, 0 stars | yes: `assert_tool_called`, `assert_tool_order`; adapters for LangChain, CrewAI, OpenAI Agents SDK, OTel | yes: `save_trace`/`load_trace` JSONL replay in tests | yes: GitHub Action + pytest exit codes | yes | pypi.org/project/agentproof ; github.com/praxiumlabs/agentproof |

Other projects in the space found by the pass:
- EvalView (hidai25/eval-view, Apache-2.0, v0.8.1, ~141 stars): "Regression testing for AI agents. Snapshot behavior, diff tool calls, catch regressions in CI"; `snapshot`/`check` commands, PR-comment Action. Closest direct competitor.
- pytest-agent-check: VCR-style YAML cassette record/replay of tool calls with diff.
- AgentCheck / pygent-test: pytest-style checks on tool usage, order, step limits, baseline regression (OpenAI forum post, April 2026, no replies).
- AgentAssay (arXiv 2603.02601): statistical regression testing for non-deterministic agent workflows; single author.
- MLflow GenAI regression-testing docs: pytest-based agent regression in CI.
- proofagent-harness, checkagent, cendor-cassette: small PyPI projects, same space.

Trace standards:
- OpenTelemetry GenAI semantic conventions (`invoke_agent`, `execute_tool` spans; `gen_ai.tool.name`, `gen_ai.tool.call.id`) moved in June 2026 to a dedicated repository with no tagged release; items still marked Development stability as of September 2026 secondary sources.
- OpenInference (Arize, Apache-2.0): parallel vocabulary; several vendors accept both.
- Implication for OQ-18: a native versioned Trace schema is defensible if it documents an import mapping from both and pins the convention version it maps from.

Demand signals (desk research only, not user research):
- "Measuring Agents in Production" (306 practitioners, ICLR 2026): reliability is the top development challenge; 74% rely primarily on human evaluation. arxiv.org/abs/2512.04123
- AlphaEval survey (Jan 2026, n=27): 59% cite output instability; 63% low confidence that a prompt or model update improved results. arxiv.org/pdf/2604.12162
- Firebase CLI PR #9357 adds `expectToolCalls` to an in-house agent test runner: large projects hand-roll tool-call assertions.
- Blog posts (April 2026, dev.to 2026) arguing deterministic checks gate CI more reliably than LLM-judge scores, and that binary pass/fail breaks on non-deterministic agents.
- Gap: no GitHub issue in LangGraph, CrewAI, or OpenAI Agents repositories explicitly requesting this was found.

## B. Technology and layout decisions carried from PROJECT_SPEC.md (architecture input, not requirements)

- Python 3.12+ initially (OQ-13), `uv` for environments and lockfile, Pydantic models, Typer CLI, rich terminal output, PyYAML with safe loading, pytest, ruff, one of mypy or pyright, jsonschema only if needed, Jinja2 only if autoescaping is proven by test. Keep the runtime dependency list to this set.
- `src/` layout at `packages/python/src/agentproof/` with modules: `models`, `config`, `runner`, `assertions/{base,registry,builtin}`, `traces/{io,validation,redaction}`, `adapters/protocol`, `reports/{json_report,html_report}`, `compare`, `storage/interface` (optional), `cli`, `errors`. Rename when implementation shows a clearer design.
- Dependency rules: core models never depend on CLI or viewer; Assertions depend on normalized Trace models only; Adapters may depend on optional SDKs; Reports depend on result models only; CLI orchestrates with minimal business logic; no circular imports; explicit public exports.
- Potential public symbols (names not final): `Scenario`, `Trace`, `TraceEvent`, `AssertionResult`, `EvaluationResult`, `evaluate_trace()`, `load_scenario()`, `load_trace()`.
- Published JSON Schemas under `schemas/` generated from the Pydantic models with a test that committed files match generated output (context assessment R4.2).
- v0.1 is Python-only: no root `package.json`, no pnpm workspace, no viewer package until the viewer starts (spec §9 overrides the §8 tree).
- Repository files at launch: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, AGENTS.md, pyproject.toml, uv.lock, .gitignore, .editorconfig, .pre-commit-config.yaml, CI workflows with pinned actions and least-privilege permissions.

## C. Options considered (for the architecture spine to settle)

| Decision | Options | Lean | Why |
|---|---|---|---|
| HTML Report rendering | Jinja2 with autoescape; stdlib `html.escape` string assembly | stdlib first | one fewer dependency; the Report is one template; escaping is explicit and testable (AC-23.2) |
| Type checker | mypy; pyright | undecided | both fit; pick one and pin it in EPIC A |
| Exit code for `error`-only Suites | 1; 3 | 1 | an unevaluated rule is not a passed rule; 3 is reserved for Adapter and I/O failures (OQ-3) |
| Argument path syntax | dotted keys; JSONPath (dependency); JMESPath (dependency) | dotted keys | covers the expense example; no dependency; can be extended (OQ-7) |
| Replay command name | `trace replay`; `trace evaluate`; `trace check` | proposal only: `trace evaluate` | removes the re-execute reading before any docs exist; the PRD keeps the spec's term `replay` until OQ-4 is decided |
| Schema Version format | integer; `major.minor` | integer, per PRD NFR-8 | `major.minor` with additive tolerance was considered and withdrawn because it conflicts with rejecting unknown fields (AC-2.2); every additive field is a new integer version (OQ-5) |
| Unknown fields | forbid; ignore | forbid | fail closed; forward compatibility by version |
| Trace schema vs OTel GenAI | native with import mapping; adopt OTel attribute names | native with mapping | OTel GenAI conventions unstable as of 2026-10 (OQ-18) |

## D. Spec items intentionally not restated in the PRD

- The four-week implementation plan and its exit gates (spec §5.2): planning, not requirements; becomes epics and stories.
- Parallel agent roles and OpenCode instructions (spec §17): process; AGENTS.md covers the binding parts.
- Backlog EPIC A to H (spec §18): input to `bmad-agent-po` slicing; FR ids in this PRD map onto them.
- Business model tiers and launch channels (spec §14, §16): out of scope for v0.1 requirements; kept as context for the maintainer.
- Release checklist (spec §13.3): becomes the release story's acceptance list.

## E. Risk register pointer

The privacy, parsing, replay, schema-versioning, and determinism risks are enumerated in `../2026-10-22-context-assessment.md` §4 (R1 to R6). NFR-1 to NFR-5 in the PRD are the requirement-level responses to them.
