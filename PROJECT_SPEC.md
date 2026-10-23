# AgentProof --- OpenCode Master Project Specification

**Document type:** Product requirements, technical design,
implementation plan, and AI-coding-agent execution guide\
**Project status:** Proposed / pre-implementation\
**Target:** Open-source adoption, career portfolio, and a credible path
to a commercial product\
**Primary stack:** Python + TypeScript\
**Build style:** AI coding agents with human review\
**Initial release:** `v0.1.0`\
**Working repository name:** `agentproof`

> This document is the source of truth for building AgentProof. Treat
> the product as unimplemented unless code and tests prove otherwise. Do
> not claim a feature is complete merely because it is described here.

------------------------------------------------------------------------

# 1. Executive Summary

## 1.1 Product

AgentProof is an open-source testing and regression framework for
tool-using AI agents. It helps developers define test scenarios, capture
agent execution traces, assert expected behavior, reproduce failures,
compare runs, and fail CI when important agent behaviors regress.

**One-line promise:** Test your AI agents like you test your software.

## 1.2 Problem

AI agents are non-deterministic systems that may call tools, change
state, handle sensitive data, or make decisions across multiple steps. A
fluent final response does not prove that an agent followed the right
process or respected its constraints. Teams need a repeatable way to
validate actions and outcomes across agent versions.

Common problems: - Tests focus on final text rather than intermediate
actions. - Failures are difficult to reproduce because model output
varies. - Prompt, model, tool, or framework changes can silently cause
regressions. - Tool arguments and action order may be incorrect even
when the final answer looks reasonable. - Evaluation suites are often
tied to one framework or provider. - Teams lack a simple path from local
testing to pull-request checks.

## 1.3 Initial solution

AgentProof provides: 1. A readable YAML scenario format. 2. A Python
evaluation engine and SDK. 3. Deterministic assertions for traces and
final outputs. 4. Versioned trace import/export and replay of assertions
against saved traces. 5. Baseline comparisons and machine-readable
results. 6. A CLI with meaningful exit codes. 7. GitHub Actions
integration. 8. A lightweight TypeScript report viewer that reads
exported JSON. 9. A provider- and framework-neutral adapter interface.
10. Security-minded defaults, including redaction support and no
automatic execution of imported traces.

## 1.4 Strategic goals

Balance three goals: - **Open-source growth:** easy installation, fast
time-to-value, clear demos, contribution-friendly architecture. -
**Career portfolio:** demonstrate product thinking, agent systems,
Python engineering, TypeScript UI, testing, CI/CD, and security. -
**Business potential:** eventually offer shared datasets, collaboration,
hosted run history, team permissions, governance, and managed retention.

Do not build the commercial platform before validating recurring
community usage.

## 1.5 Product positioning

AgentProof is not: - A general-purpose agent builder. - A replacement
for every LLM evaluation framework. - A model-provider hosting
service. - A guarantee that an agent is safe or correct. - A tool that
can infer correctness from any arbitrary task without an explicit test
oracle.

AgentProof is: - A test runner for agent behavior. - A trace and
assertion format. - A regression-testing workflow for tool-using
agents. - A CI-friendly layer that can integrate with different agent
frameworks.

------------------------------------------------------------------------

# 2. Target Users and Use Cases

## 2.1 Primary personas

### Persona A: AI application engineer

Builds tool-using agents and needs reliable regression tests. - Wants a
fast CLI. - Needs trace-level debugging. - Prefers Python and existing
frameworks. - Does not want to run a large platform locally.

### Persona B: Agent framework developer

Maintains an SDK, framework, or MCP server. - Needs contract tests for
tool calls. - Wants reproducible bug reports. - Needs compatibility
tests across versions.

### Persona C: Automation engineer

Builds business workflows using browser automation, APIs, and AI. -
Needs to verify steps and outcomes. - Needs tests for prohibited actions
and approval requirements. - Needs logs and audit-friendly reports.

### Persona D: Engineering lead at an AI startup

Needs to prevent regressions before release. - Wants CI checks and
baselines. - Needs a report that non-specialists can understand. - May
later pay for collaboration and centralized governance.

## 2.2 Initial use cases

1.  Verify an agent calls a required tool.
2.  Verify a tool receives expected arguments.
3.  Verify a forbidden tool is never called.
4.  Verify a required action occurs before another action.
5.  Verify the final output contains a required phrase or matches a JSON
    schema.
6.  Validate an agent against a saved trace without spending money on
    another model call.
7.  Compare the results of two evaluation runs.
8.  Fail a GitHub pull request when a critical assertion fails.
9.  Import a trace from a custom agent adapter.
10. Redact sensitive values before storing or sharing traces.

## 2.3 Example use case

An expense-management agent may be required to reject an expense above a
policy limit. It is not enough that the final answer says "rejected."
The test must also verify that the agent did not call `approve_expense`,
and preferably that the test environment prevented real side effects.

Important distinction: - **Post-run assertion:** detects that an action
occurred. - **Runtime enforcement:** prevents the action from
occurring. - The MVP provides post-run assertions and safe test
fixtures. Runtime enforcement is a later, separate feature.

------------------------------------------------------------------------

# 3. Competitive Landscape and Differentiation

Potential adjacent projects include: - DeepEval:
https://github.com/confident-ai/deepeval - Promptfoo:
https://github.com/promptfoo/promptfoo - Langfuse:
https://github.com/langfuse/langfuse - Inspect AI:
https://github.com/UKGovernmentBEIS/inspect_ai - LangSmith:
https://www.langchain.com/langsmith

Verify current capabilities, licenses, releases, and open issues before
making public competitor claims. Do not copy their code or
documentation.

## 3.1 Competitive opportunity

Basic metrics, prompt comparisons, trace dashboards, and LLM-as-a-judge
are already served by established tools. AgentProof should not compete
on a generic feature checklist.

Potential wedge: - Scenario-first workflow. - Deterministic action and
tool-call assertions. - Replay of recorded traces without another model
call. - Small local-first CLI. - Versioned trace schema. - Pull-request
regression gates. - Clear failure diagnostics and baseline diffs. -
Framework-neutral adapter interface.

## 3.2 Differentiation hypotheses to validate

These are hypotheses, not proven market gaps: 1. Developers want a
simpler CLI for agent action contracts. 2. Replaying a saved trace
against new assertions is valuable. 3. Developers want tests that can be
checked into the same Git repository as code. 4. Small projects prefer
local-first tools over a hosted observability platform. 5. A useful
GitHub Actions integration can drive adoption.

Before building beyond the spike, interview 5--10 developers and inspect
competitor issues/discussions. Record evidence and revise these
hypotheses.

------------------------------------------------------------------------

# 4. Product Principles

1.  **Deterministic first:** Prefer explicit assertions over
    model-judged scores.
2.  **Local-first:** Core evaluation should work without an account or
    external service.
3.  **Small installation:** A basic test run should not require Docker,
    Redis, or a database server.
4.  **Framework-neutral:** Core models must not import a specific agent
    framework.
5.  **Trace transparency:** Users should be able to inspect exported
    data.
6.  **Fail closed for critical missing data:** A missing trace or
    assertion input must not silently pass.
7.  **Explicit side effects:** Imported traces are data, never
    executable instructions.
8.  **Security by design:** Redact secrets, avoid unsafe HTML rendering,
    and document limitations.
9.  **Stable public contracts:** Version schemas and CLI output.
10. **Practical UX:** A new user should run a working example in under
    five minutes.
11. **Honest claims:** Never claim full reproducibility of stochastic
    model behavior. Replay means deterministic re-evaluation of recorded
    evidence unless a live re-run is explicitly requested.
12. **Test the tool itself:** AgentProof must run its own tests and CI
    checks.

------------------------------------------------------------------------

# 5. Scope and Roadmap

## 5.1 MVP / v0.1 scope

Must have: - Python package and CLI. - YAML scenario loading and
validation. - Versioned trace model. - Deterministic assertion engine. -
Built-in fake agent/test fixtures. - Trace JSON import/export. - Offline
assertion replay. - JSON report. - Simple self-contained HTML report. -
Baseline comparison. - Meaningful CLI exit codes. - GitHub Actions
example. - Documentation and examples. - Unit and integration tests. -
Basic redaction of configured secret-like fields. - Security policy and
contribution guide.

Should have if time permits: - Minimal React/TypeScript trace viewer. -
One real framework adapter chosen after user validation. - JUnit XML
output for CI systems.

Must not have in v0.1: - Hosted SaaS. - User accounts and
authentication. - Billing. - Complex distributed worker architecture. -
Full agent orchestration. - Production runtime policy enforcement. -
Automatic browser or desktop operation. - Dozens of framework
integrations. - Claims of universal safety certification.

## 5.2 Four-week implementation plan

### Week 1 --- Foundation

-   Create repository, package, lint/type/test configuration.
-   Finalize scenario and trace schemas.
-   Implement config loading and validation.
-   Implement five deterministic assertions.
-   Add a fake trace fixture and CLI command.
-   Add CI.
-   Exit gate: sample suite runs without API credentials and returns
    correct pass/fail status.

### Week 2 --- Trace workflow

-   Add trace JSON import/export.
-   Add offline replay of assertions.
-   Add Python adapter protocol.
-   Add JSON and HTML reports.
-   Add redaction.
-   Write end-to-end docs.
-   Exit gate: a user can test a simple agent or imported trace and
    diagnose a failure.

### Week 3 --- Regression and developer experience

-   Add baseline snapshots and comparisons.
-   Add GitHub Actions workflow.
-   Add clear failure summaries and stable exit codes.
-   Start TypeScript viewer if core remains stable.
-   Add malformed-input, regression, and security tests.
-   Exit gate: a pull request can fail due to a declared critical
    regression.

### Week 4 --- Launch preparation

-   Validate one real framework integration.
-   Polish quick start and sample repository.
-   Record a short demo.
-   Run security and license checks.
-   Publish package and release notes.
-   Recruit 5--10 design partners.
-   Exit gate: an external developer can install and use the project
    without live assistance.

These are estimates, not guaranteed dates. Do not sacrifice test quality
to meet the calendar.

## 5.3 Post-MVP roadmap

### v0.2

-   First community-requested framework adapter.
-   JUnit XML.
-   Improved trace diff.
-   Better redaction rules.
-   More assertion types.
-   Versioned schema migration tests.

### v0.3

-   Optional TypeScript report viewer.
-   Dataset organization.
-   Run labels and metadata.
-   More useful flaky-test diagnostics.
-   Optional LLM judge interface, disabled by default and clearly marked
    non-deterministic.

### v0.5

-   Multiple adapter packages.
-   Performance and cost budgets where data is available.
-   Team-friendly artifact sharing.
-   Optional storage backend abstraction.
-   Plugin/extension documentation.

### v1.0

Only when schema, CLI, extension points, and migration policy are
stable: - Stable public APIs. - Semantic versioning. - Documented
compatibility policy. - Security disclosure process. - Maintainer and
release process. - User evidence showing repeated use.

### Possible commercial roadmap

Only after demonstrated demand: - Hosted run history. - Shared team
datasets. - Role-based access controls. - Retention controls and audit
logs. - Private deployments and enterprise support. - Managed
integrations.

------------------------------------------------------------------------

# 6. Detailed Functional Requirements

## 6.1 CLI

Proposed commands:

``` text
agentproof init [PATH]
agentproof validate [SCENARIO_PATH]
agentproof run [SCENARIO_PATH]
agentproof trace validate TRACE_PATH
agentproof trace replay TRACE_PATH --scenario SCENARIO_PATH
agentproof compare BASELINE CURRENT
agentproof report RESULT_PATH --format json|html|junit
agentproof version
```

Implement only commands whose behavior is fully tested. Adjust names if
Typer conventions or usability testing suggests a better interface.

### CLI requirements

-   Helpful `--help` output.
-   Clear errors with file and field context.
-   No stack trace for ordinary user input errors.
-   `--verbose` for diagnostic details.
-   Stable exit codes documented before release.
-   Do not print secret values.
-   `--output` path support for artifacts.
-   Deterministic JSON output ordering where practical.
-   A clear summary of passed, failed, skipped, and errored assertions.

Proposed exit codes: - `0`: all required checks passed. - `1`: one or
more assertions failed. - `2`: invalid configuration or invalid input. -
`3`: execution/integration error. - `4`: internal unexpected error.

If the implementation adopts different codes, update tests and
documentation together.

## 6.2 Scenario configuration

Illustrative YAML:

``` yaml
version: "1"
suite: expense-agent
description: "Expense approval policy regression tests"

defaults:
  fail_on_missing_trace: true

scenarios:
  - id: reject-over-limit
    description: "An expense above the limit must not be approved"
    input:
      expense_amount: 5000
      currency: USD
    assertions:
      - type: tool_not_called
        tool: approve_expense
      - type: tool_called
        tool: reject_expense
      - type: final_output_contains
        value: "rejected"
```

This is an initial proposal. Finalize schema and semantics in tests
before publishing v1 of the format.

Requirements: - Explicit schema version. - Unique scenario IDs within a
suite. - Strict validation of unknown assertion types. - Clear errors
for missing required fields. - Do not evaluate YAML custom tags or
instantiate arbitrary Python objects. - Document environment variable
substitution if supported; do not implement it implicitly. - Avoid
embedding credentials in scenario files. - Define whether string
matching is case-sensitive. - Define how assertion errors and skipped
assertions affect overall status.

## 6.3 Trace model

Suggested conceptual event types: - `agent_started` - `agent_finished` -
`tool_call` - `tool_result` - `llm_request` (optional metadata only) -
`llm_response` (optional, redaction-sensitive) - `exception` -
`approval_requested` - `approval_granted` - `approval_denied` - `custom`

Every event should have: - Event type. - Sequence index. - Timestamp if
available. - Optional duration. - Optional tool name. - Optional
arguments and result. - Optional status and error information. -
Metadata with a documented schema. - Redaction state when relevant.

Run-level fields: - Schema version. - Run ID. - Scenario ID. - Start/end
timestamps. - Agent and adapter metadata. - Optional model/provider
metadata. - Events. - Result summary. - Optional source revision. -
Optional environment metadata, excluding secrets.

Do not require a provider name or model name for custom/offline traces.

## 6.4 Assertion engine

Each assertion must have: - A unique type name. - Validated
configuration. - A pure evaluation function where possible. - A result
status. - A clear human-readable message. - Optional evidence
references, such as event indexes. - Unit tests for pass, fail, invalid
input, and missing evidence.

Initial assertions: 1. `tool_called` 2. `tool_not_called` 3.
`tool_call_count` 4. `tool_arguments_match` 5. `tool_order` 6.
`final_output_contains` 7. `final_output_matches` 8.
`final_output_json_schema` 9. `run_completed` 10.
`no_unhandled_exception` 11. `duration_under` 12. `required_metadata`
13. `event_exists` 14. `event_not_exists`

Do not implement every assertion at once. Start with the first five plus
one final-output assertion, then expand based on user feedback.

Suggested semantics: - `tool_called`: at least one matching tool-call
event exists. - `tool_not_called`: no matching tool-call event exists. -
`tool_call_count`: count equals, greater than, or less than a specified
integer. - `tool_arguments_match`: selected JSON paths match expected
values. - `tool_order`: specified events occur in order; define whether
intervening events are allowed. - `final_output_contains`: final output
is available and includes a literal substring. - `final_output_matches`:
a documented regex match; prevent pathological regex use where
practical. - `final_output_json_schema`: final output parses as JSON and
satisfies a declared schema. - `run_completed`: trace contains a
successful terminal event. - `no_unhandled_exception`: no event is
marked as an unhandled exception. - `duration_under`: run duration
exists and is below a specified threshold. - `required_metadata`:
metadata key exists and optionally matches a value.

Missing evidence should not be treated as a pass. The engine must
distinguish failed assertions from evaluation errors.

## 6.5 Trace import/export and replay

-   Export a trace as JSON conforming to a versioned schema.
-   Validate imported traces before use.
-   Replay means applying assertions to saved trace evidence; it must
    not call the agent or tools.
-   Never execute commands, URLs, code, or tool calls found in a trace.
-   Preserve sequence ordering.
-   Define timestamp parsing and timezone behavior.
-   Support redaction before writing artifacts.
-   Include source and schema version metadata.
-   Add migration tooling only when a schema change requires it.

## 6.6 Baseline comparison

Compare: - Overall pass/fail status. - Failed assertion IDs. - Tool-call
sequence. - Tool names and selected arguments. - Duration when
comparable. - Cost when supplied by the adapter. - Missing or additional
events.

Do not claim two live stochastic runs are identical. Explain whether
comparison is: - Exact comparison of saved trace data. - Semantic
comparison using declared normalization rules. - Statistical comparison
across multiple runs.

The MVP should prioritize exact/normalized trace comparison and avoid
statistical claims.

## 6.7 Reports

JSON report: - Stable schema version. - Suite/run identifiers. -
Scenario status. - Assertion results. - Failure messages and evidence. -
Summary counts. - Optional timing/cost values.

HTML report: - Self-contained output. - Escaped user and trace
content. - No remote scripts or tracking by default. - Accessible status
labels. - Clear display of missing data. - Avoid unsafe insertion of
trace content as HTML.

JUnit XML: - Add only after basic reporting is stable. - Map assertion
failures to test failures and execution errors to errors. - Escape XML
correctly.

## 6.8 GitHub Actions integration

Provide a copy-paste workflow that: 1. Checks out the repository. 2.
Installs a supported Python version. 3. Installs AgentProof. 4. Runs the
test suite. 5. Saves reports as artifacts even when tests fail. 6. Fails
the job on critical assertion failure.

Do not require a hosted AgentProof account. Keep secrets out of workflow
logs. Document how to test without model API credentials using saved
traces and deterministic fixtures.

## 6.9 Python adapter interface

The core should define a small protocol rather than importing a
framework.

Adapter responsibilities: - Receive or produce normalized trace
events. - Attach safe metadata. - Surface errors explicitly. - Avoid
silently dropping events. - Document limitations. - Keep framework
dependencies optional.

An adapter must not be allowed to bypass the assertion engine or mark
itself successful without valid result evidence.

## 6.10 TypeScript viewer

Optional for MVP; the CLI and HTML report are higher priority.

Initial screens: - Run summary. - Scenario list. - Assertion result
list. - Trace timeline. - Event details. - Baseline diff.

Requirements: - Read exported JSON locally. - No account required. - No
network requests by default. - Clearly label missing/redacted fields. -
Render untrusted trace values as text, never executable HTML. -
Accessible keyboard navigation. - Handle large traces with a reasonable
size limit or pagination. - Provide useful empty and error states.

Use React + Vite + TypeScript. Do not build a backend for the first
viewer.

------------------------------------------------------------------------

# 7. Architecture and Boundaries

## 7.1 Logical architecture

``` text
Scenario YAML / Python API / CLI arguments
                    |
                    v
           Config Loader + Validator
                    |
                    v
             Scenario Runner
                    |
         +----------+-----------+
         |                      |
         v                      v
  Adapter / Trace Input   Test Fixtures
         |                      |
         +----------+-----------+
                    |
                    v
              Trace Model
                    |
                    v
             Assertion Engine
                    |
                    v
            Evaluation Result
                    |
         +----------+-----------+
         |          |           |
         v          v           v
       JSON        HTML       JUnit
         |
         v
   Baseline / Compare
         |
         v
   CLI Exit Code / CI
```

## 7.2 Dependency rules

-   Core models must not depend on CLI or viewer modules.
-   Assertion functions should depend on normalized trace models, not a
    specific framework.
-   Adapters may depend on optional framework SDKs.
-   Reports depend on result models, not on agent execution.
-   CLI orchestrates components but should contain minimal business
    logic.
-   Viewer consumes exported result schemas; it does not own evaluation
    semantics.
-   Storage is an implementation detail behind a narrow interface.
-   Avoid circular imports.
-   Use explicit public exports and keep internal modules private.

## 7.3 Suggested Python module responsibilities

-   `models.py`: Pydantic models for scenario, event, trace, assertion,
    and result.
-   `config.py`: safe YAML loading and validation.
-   `runner.py`: orchestrate scenario evaluation.
-   `assertions/base.py`: assertion protocol and common result type.
-   `assertions/registry.py`: register built-in assertion types.
-   `assertions/builtin.py`: initial deterministic assertion
    implementations.
-   `traces/io.py`: JSON import/export.
-   `traces/validation.py`: schema and semantic validation.
-   `traces/redaction.py`: configurable redaction.
-   `adapters/protocol.py`: framework-neutral adapter contract.
-   `reports/json_report.py`: machine-readable report.
-   `reports/html_report.py`: safe HTML output.
-   `compare.py`: baseline and current result comparison.
-   `storage/interface.py`: optional run-storage abstraction.
-   `cli.py`: Typer command definitions.
-   `errors.py`: user-facing exception hierarchy.

Refactor names if implementation shows a clearer design. Keep module
responsibilities narrow.

------------------------------------------------------------------------

# 8. Repository Layout

Recommended monorepo:

``` text
agentproof/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── AGENTS.md
├── pyproject.toml
├── uv.lock
├── package.json
├── pnpm-workspace.yaml
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── release.yml
│   │   └── docs.yml
│   ├── ISSUE_TEMPLATE/
│   └── pull_request_template.md
├── packages/
│   ├── python/
│   │   ├── src/agentproof/
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── config.py
│   │   │   ├── models.py
│   │   │   ├── runner.py
│   │   │   ├── compare.py
│   │   │   ├── errors.py
│   │   │   ├── assertions/
│   │   │   ├── traces/
│   │   │   ├── adapters/
│   │   │   ├── reports/
│   │   │   └── storage/
│   │   └── tests/
│   └── viewer/
│       ├── package.json
│       ├── src/
│       │   ├── components/
│       │   ├── pages/
│       │   └── lib/
│       └── tests/
├── schemas/
│   ├── scenario-v1.schema.json
│   └── trace-v1.schema.json
├── examples/
│   ├── basic-agent/
│   ├── expense-agent/
│   └── tool-policy/
├── docs/
│   ├── getting-started.md
│   ├── architecture.md
│   ├── scenario-format.md
│   ├── assertions.md
│   ├── traces.md
│   ├── integrations.md
│   ├── security.md
│   └── roadmap.md
└── benchmarks/
    └── baseline/
```

Do not create empty directories just to match this tree. Add modules
when they have a real purpose.

------------------------------------------------------------------------

# 9. Technology Choices

## Python

-   Python 3.12+ initially; choose the minimum supported version based
    on dependencies and CI.
-   `uv` for local environment and lockfile management.
-   `pydantic` for typed models and validation.
-   `typer` for CLI.
-   `rich` for terminal output.
-   `PyYAML` or another safe YAML parser; use safe loading only.
-   `pytest` for tests.
-   `ruff` for linting/formatting.
-   `mypy` or `pyright` for type checking; choose one initially.
-   `jsonschema` if JSON Schema validation is needed.
-   `jinja2` only if HTML templates are safely escaped and well tested.

## TypeScript

-   Node.js LTS supported by the chosen Vite version.
-   TypeScript strict mode.
-   React + Vite for the optional viewer.
-   Vitest for unit tests.
-   ESLint and Prettier.
-   pnpm workspace only if the viewer is included in the monorepo; avoid
    unnecessary JS tooling for a Python-only MVP.

## CI

-   GitHub Actions.
-   Test supported Python versions.
-   Lint, type-check, test, build package.
-   Test installation from a clean environment.
-   Add dependency and secret scanning where practical.
-   Use pinned action versions and least-privilege permissions.

## Dependency policy

-   Keep the runtime dependency list small.
-   Pin or constrain dependencies appropriately.
-   Review transitive dependencies and licenses.
-   Avoid dependencies that force users into a specific model vendor.
-   Use optional extras for framework adapters.

------------------------------------------------------------------------

# 10. Data Contracts and Public API

## 10.1 Versioning

-   Every serialized scenario and trace includes a schema version.
-   Use semantic versioning for package releases.
-   Avoid breaking public APIs in patch releases.
-   Document migrations for breaking schema changes.
-   Test old fixtures against current readers.
-   Do not assume the package version and trace schema version are
    identical.

## 10.2 Result status

Suggested statuses: - `passed` - `failed` - `error` - `skipped`

Definitions: - `passed`: assertion evaluated and succeeded. - `failed`:
assertion evaluated and condition was not met. - `error`: assertion
could not be evaluated due to invalid/missing required data or internal
execution problem. - `skipped`: intentionally not evaluated under
documented rules.

At suite level, define whether any `error` always fails the suite. The
safe default should be nonzero exit code for errors and failures.

## 10.3 Public API stability

Keep the initial public API small. Export only the models and protocols
users need. Avoid promising stability for internal helpers until v1.0.

Potential public symbols: - `Scenario` - `Trace` - `TraceEvent` -
`AssertionResult` - `EvaluationResult` - `evaluate_trace(...)` -
`load_scenario(...)` - `load_trace(...)`

These are proposed names, not existing symbols. Implement and test
before documenting them as available.

------------------------------------------------------------------------

# 11. Security, Privacy, and Safety

AgentProof will handle potentially sensitive prompts, tool arguments,
outputs, and traces. Treat traces as sensitive by default.

## 11.1 Required safeguards

-   No network calls in core evaluation unless an explicitly configured
    adapter needs them.
-   No execution of imported trace content.
-   Safe YAML parsing.
-   Escape user content in HTML reports.
-   Avoid `eval`, `exec`, shell execution, and arbitrary
    deserialization.
-   Never log API keys or authorization headers.
-   Provide configurable redaction for keys such as `api_key`, `token`,
    `password`, `authorization`, and user-specified paths.
-   Do not claim redaction is complete for every possible secret.
-   Document that users should inspect artifacts before sharing.
-   Do not upload traces to a hosted service by default.
-   Add a security reporting process.
-   Use least-privilege GitHub Actions permissions.
-   Test path traversal and unsafe output file handling.
-   Limit trace and report sizes or warn about very large files.
-   Treat regex assertions carefully; document potential performance
    concerns.

## 11.2 Runtime enforcement boundary

The MVP observes and tests agent behavior. It does not guarantee
prevention of unsafe tool calls in a live system.

A future enforcement layer would need: - A tool-call interception
boundary. - Explicit allow/deny policy. - Human approval for sensitive
actions. - Fail-safe behavior on policy-engine failure. - Auditable
decisions. - Clear integration requirements.

Never market post-run tests as a substitute for runtime access controls.

## 11.3 Privacy defaults

-   Local-only execution by default.
-   No telemetry by default.
-   If telemetry is ever introduced, make it opt-in and documented.
-   Keep trace storage user-controlled.
-   Make redaction visible and testable.
-   Never send user traces to an LLM judge without explicit
    configuration.

------------------------------------------------------------------------

# 12. Testing Strategy

## 12.1 Unit tests

-   Scenario parsing and validation.
-   Each assertion's pass/fail/error behavior.
-   Trace model validation.
-   Redaction behavior.
-   Report serialization.
-   Baseline comparison.
-   Exit-code mapping.

## 12.2 Integration tests

-   Run a suite from disk.
-   Import a trace and replay assertions offline.
-   Generate JSON and HTML reports.
-   Verify CLI exit codes.
-   Verify malformed files produce clear errors.
-   Verify secrets are redacted from reports where configured.

## 12.3 Property and edge-case tests

-   Empty traces.
-   Missing final output.
-   Duplicate event IDs or sequence indexes.
-   Out-of-order events.
-   Invalid timestamps.
-   Unknown event types.
-   Unknown assertion types.
-   Null versus absent fields.
-   Unicode and multiline content.
-   Large trace files.
-   Malformed JSON/YAML.
-   Unexpected adapter exceptions.

## 12.4 End-to-end acceptance tests

1.  Install the package in a clean environment.
2.  Initialize an example project.
3.  Run a passing suite.
4.  Run a deliberately failing suite.
5.  Confirm a nonzero exit code.
6.  Generate a report.
7.  Replay a saved trace without provider credentials.
8.  Compare baseline and current output.
9.  Inspect artifacts for leaked test secrets.

## 12.5 Quality gates

A change is not complete until: - Tests pass. - Lint and type checks
pass. - Public docs are updated. - Errors are actionable. -
Security-sensitive behavior has tests. - The diff is limited to the
requested task. - No undocumented dependency is added. - No feature is
claimed as complete without verification.

------------------------------------------------------------------------

# 13. Packaging, Releases, and Version Control

## 13.1 Package release

-   Publish to PyPI only after clean-install tests pass.
-   Use a test PyPI workflow if appropriate.
-   Build distributions and validate metadata.
-   Keep package name availability unconfirmed until checked.
-   Confirm trademark and project-name availability before public
    launch.
-   Tag releases using semantic versioning.

## 13.2 Branching

For a solo project: - `main` remains releasable. - Feature branches are
short-lived. - Use pull requests even when working alone for review
history. - Keep commits small and descriptive. - Do not commit secrets,
local traces, virtual environments, build artifacts, or private
datasets.

## 13.3 Release checklist

-   [ ] Tests, lint, and type checks pass.
-   [ ] Clean installation verified.
-   [ ] README quick start tested.
-   [ ] Changelog updated.
-   [ ] Version and schema compatibility checked.
-   [ ] License and dependency review completed.
-   [ ] Security notes reviewed.
-   [ ] Example artifacts checked for secrets.
-   [ ] GitHub release notes written.
-   [ ] Package build verified.
-   [ ] Rollback plan documented.

------------------------------------------------------------------------

# 14. Open-Source Adoption and Marketing

## 14.1 Before launch

1.  Interview 5--10 AI/agent developers.
2.  Inspect current competitor documentation, issues, discussions,
    licenses, and recent releases.
3.  Write a one-page differentiation brief.
4.  Build a working demo showing a regression.
5.  Create a sample repository that users can run without API
    credentials.
6.  Write a clear README, CONTRIBUTING guide, SECURITY policy, and
    roadmap.
7.  Invite a small number of developers to try it and report friction.

## 14.2 Launch demonstration

The most compelling demo: 1. Run an agent scenario that passes. 2.
Change a tool policy or agent behavior to introduce a regression. 3. Run
the same AgentProof suite. 4. Show the failed assertion and event
evidence. 5. Show GitHub Actions blocking the pull request. 6. Replay
the saved trace offline to inspect the failure.

Keep the demo short, real, and reproducible. Do not fake stars,
benchmarks, user quotes, or download numbers.

## 14.3 Launch channels

Use relevant channels when the product is ready: - GitHub repository and
release. - Hacker News, if the project has a useful technical story. -
Relevant Reddit communities, respecting self-promotion rules. - AI
engineering and agent-development communities. - Technical blog posts
with reproducible examples. - Short demo videos. - Discussions and
issues in adjacent projects, where genuinely relevant.

Do not spam identical promotional content. Participate helpfully and
disclose your relationship to the project.

## 14.4 README opening draft

``` markdown
# AgentProof

**Test your AI agents like you test your software.**

AgentProof is an open-source testing and regression framework for AI agents. Define tasks, validate tool calls and outcomes, reproduce failures, and catch regressions in CI before they reach production.

## Why AgentProof?
- Test behavior, not just answers.
- Validate tool calls, arguments, outcomes, and policies.
- Replay supported traces without rerunning model calls.
- Catch regressions with baseline comparisons.
- Run locally and integrate with GitHub Actions.

AgentProof is an early-stage project. APIs and integrations may change before v1.0.
```

Only publish install commands and usage examples after they have been
tested against the actual package.

------------------------------------------------------------------------

# 15. Metrics and Validation Gates

Illustrative first-month targets, not predictions: - 100 developers
successfully run an example. - 5 developers test their own agent. - 3
repeat users or external contributors. - 10 useful external feedback
items or bug reports.

Measure: - Time to first successful run. - Installation failure rate. -
Number of users who run a second suite. - Number of independent projects
using the tool. - Issues that reveal repeated missing capabilities. -
Contributions merged. - CI integration success rate. - Release
regressions.

Do not optimize solely for stars. Stars are a discovery signal, not
proof of recurring value.

Decision gates: - Week 1: can a saved trace reproduce a real failure? -
Week 2: can a stranger test their own agent without substantial help? -
Week 3: does CI detect a meaningful regression? - Week 4: do external
developers return and request improvements? - Day 30: is there evidence
of repeat use and a clear next feature?

If stars rise but repeat usage remains low, prioritize usability and
product value.

------------------------------------------------------------------------

# 16. Business Model

Keep the core project useful and open source.

Possible later tiers: - **Community:** CLI, local evaluation,
assertions, traces, reports. - **Team:** shared datasets, centralized
run history, collaboration. - **Enterprise:** access control, audit
logs, retention controls, private deployment, support. - **Hosted
cloud:** optional managed evaluation and artifact retention.

Do not implement billing, accounts, or multi-tenant infrastructure until
users demonstrate a recurring need.

Apache-2.0 is a reasonable permissive-license candidate, but confirm
contributor policy, dependency licenses, name/trademark availability,
and legal suitability before release.

------------------------------------------------------------------------

# 17. OpenCode Instructions

## 17.1 How OpenCode should use this specification

This file is the project brief and implementation contract. OpenCode
should: - Read this document before making changes. - Inspect the
repository before assuming files or modules exist. - Create a phased
implementation plan. - Work in small, verifiable increments. - Prefer
tested, working behavior over broad scaffolding. - Ask for clarification
only when a decision materially blocks safe implementation. - Record
important decisions in `docs/decisions/`. - Update this spec if an
architectural decision changes the plan. - Never claim a command, test,
build, or feature succeeded without actually running it and checking the
result. - Avoid implementing all roadmap items at once.

## 17.2 Recommended `AGENTS.md`

Create an `AGENTS.md` in the repository root with rules similar to:

``` markdown
# Agent Instructions

## Product
AgentProof is a local-first, framework-neutral testing and regression tool for AI agents.
Read `PROJECT_SPEC.md` before implementation.

## Engineering rules
- Keep core evaluation deterministic and provider-neutral.
- Do not execute imported trace content.
- Use safe YAML parsing.
- Never log secrets or tokens.
- Add tests for every new assertion and error path.
- Do not add a dependency without explaining why.
- Keep public schemas versioned.
- Keep changes focused and avoid unrelated refactors.
- Do not claim tests passed unless they were run successfully.
- Do not claim features exist until implemented and verified.
- Update docs when CLI, schema, or public APIs change.

## Required checks
Run the repository's documented lint, type-check, and test commands.
Verify a clean installation for packaging changes.
Verify exit codes for CLI changes.
Inspect reports for secret leakage when changing trace/report code.

## Workflow
1. Inspect repository and git status.
2. Read relevant modules and tests.
3. State a short implementation plan.
4. Implement one coherent task.
5. Add or update tests.
6. Run required checks.
7. Summarize files changed, checks run, results, and remaining risks.
```

## 17.3 Parallel agent roles

Use separate agents only for tasks with clear boundaries: -
**Architect:** schema, interfaces, dependency rules. - **Core
engineer:** models, scenario loading, assertion engine. - **CLI
engineer:** Typer commands and terminal output. - **QA engineer:** test
cases, fixtures, edge cases. - **Docs engineer:** README, examples,
guides. - **Reviewer:** inspect diff and challenge assumptions.

For the first week, avoid excessive parallelism. The scenario and trace
contracts are shared dependencies; finalize them before multiple agents
build on top of them.

------------------------------------------------------------------------

# 18. Initial Backlog

## EPIC A --- Repository foundation

-   A1: Create Python package layout.
-   A2: Configure `uv`, pytest, Ruff, and type checker.
-   A3: Add CI workflow.
-   A4: Add license and contribution files after license choice is
    confirmed.
-   A5: Add `AGENTS.md` and this specification.

## EPIC B --- Data contracts

-   B1: Define Pydantic scenario models.
-   B2: Define trace/event models.
-   B3: Define assertion result and evaluation result.
-   B4: Add versioned JSON schemas.
-   B5: Add valid and invalid fixtures.

## EPIC C --- Scenario engine

-   C1: Safely load YAML.
-   C2: Validate scenarios.
-   C3: Evaluate a scenario against a supplied trace.
-   C4: Produce deterministic suite summaries.
-   C5: Map statuses to CLI exit codes.

## EPIC D --- Assertions

-   D1: `tool_called`.
-   D2: `tool_not_called`.
-   D3: `tool_call_count`.
-   D4: `tool_arguments_match`.
-   D5: `tool_order`.
-   D6: `final_output_contains`.
-   D7: Assertion registry and validation errors.

## EPIC E --- Trace workflow

-   E1: Import/export JSON.
-   E2: Validate imported trace.
-   E3: Replay assertions offline.
-   E4: Redaction rules.
-   E5: Malformed trace tests.

## EPIC F --- Reporting and comparison

-   F1: JSON report.
-   F2: Self-contained HTML report.
-   F3: Baseline snapshot.
-   F4: Baseline/current comparison.
-   F5: Clear failure evidence.

## EPIC G --- CI integration

-   G1: Example GitHub Actions workflow.
-   G2: Artifact upload example.
-   G3: Document secret handling.
-   G4: End-to-end CI fixture.

## EPIC H --- Launch readiness

-   H1: Quick-start tutorial.
-   H2: Expense-policy example.
-   H3: Demo script.
-   H4: Security review.
-   H5: Package build and release workflow.
-   H6: First external user feedback.

------------------------------------------------------------------------

# 19. Definition of Done

A feature is done only when: 1. Requirements and behavior are explicit.
2. Implementation is complete. 3. Relevant unit tests pass. 4.
Integration tests pass where applicable. 5. Errors are understandable.
6. Security implications are considered. 7. Documentation is updated. 8.
Public schema/API changes are versioned or justified. 9. The change does
not introduce unapproved dependencies or unrelated refactoring. 10. The
final summary lists the actual files changed and actual commands run.

A green test suite is necessary but not sufficient; inspect the diff and
verify the behavior manually for high-impact features.

------------------------------------------------------------------------

# 20. First OpenCode Task

Do not implement the entire project in one prompt.

Start with this task:

``` text
Read PROJECT_SPEC.md and AGENTS.md in full.

Inspect the repository, current git status, Python/Node versions, and installed tooling.
Do not overwrite existing work.

Create a concise implementation plan for EPIC A and EPIC B only.
Identify unresolved schema decisions and recommend defaults.
Then implement the repository foundation and initial data contracts only.

Requirements:
- Python package with src layout.
- Configure uv, pytest, Ruff, and one type checker.
- Define versioned Pydantic models for scenarios, trace events, traces,
  assertion results, and evaluation results.
- Add valid and invalid fixtures.
- Add unit tests for schema validation.
- Add a minimal CI workflow.
- Do not implement all assertions, adapters, the viewer, SaaS, or future roadmap items.
- Do not invent successful test results.
- Run all checks that are available and report exact results.
- If a command cannot run, explain why and leave a reproducible next step.
- Finish with a summary of changed files, design decisions, tests run,
  results, and remaining risks.
```

After that task is reviewed and merged, implement the assertion engine
as a separate task.

------------------------------------------------------------------------

# 21. Final Product North Star

AgentProof wins when a developer can answer three questions quickly:

1.  **What did my agent do?**
2.  **Did it behave correctly according to my explicit rules?**
3.  **Did the latest change make it worse?**

Everything in the initial product should support those questions. Keep
the core small, the trace format transparent, the assertions
deterministic, and the installation experience excellent.

The long-term opportunity is to become a trusted testing layer across
agent frameworks---not to become another all-in-one AI platform before
the core workflow is proven.
