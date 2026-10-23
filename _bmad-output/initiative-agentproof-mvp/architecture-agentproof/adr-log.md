# AgentProof v0.1 — Architecture Decision Records

One ADR per AD in `architecture-agentproof.md`. Status values: **Accepted** (settled by the spec, PRD, or this run), **Proposed** (chosen here under an `[ASSUMPTION]`; the maintainer confirms or changes it). When the repository is scaffolded (EPIC A), move each record to `docs/decisions/NNNN-<slug>.md` and keep the AD id in its title. All versions cited were verified against PyPI and python.org on 2026-10-22 (see `reviews/review-versions.md`).

---

## ADR-001 (AD-1) — Functional core, imperative shell
**Status:** Accepted.
**Context.** The product's central promise is deterministic re-evaluation of a recorded trace (PRD NFR-1; spec principle 11). Determinism fails the moment evaluation code touches a clock, the environment, or the filesystem. The first draft banned only writes; the adversarial review showed a reader in the core produced two incompatible `load_suite` signatures and a second non-atomic writer.
**Decision.** Everything that computes is a pure function over frozen models and never touches files, clocks, ids, or the environment. The shell (`adapters`, `runner`, `io`, `cli`) does all of that and passes values in. Enforced by an import-linter forbidden contract and a ruff banned-API list.
**Alternatives.** Layered services holding state; an actor or pipeline framework.
**Consequences.** Core functions take text or bytes plus a `source` label; the public API has a `parse_*` (core) and `load_*` (shell) pair for every artifact kind.

## ADR-002 (AD-2) — Enforced dependency direction with one written contract
**Status:** Accepted.
**Context.** The first draft had three inconsistent descriptions of the graph (diagram, layer list, registry union). Independent builders would have followed different ones.
**Decision.** The `.importlinter` layer contract is reproduced verbatim in the spine and is the authority; the diagram mirrors it, and `forbidden` contracts cover the modules outside the stack (`io`, `adapters`, `testing`, `cli`). `constants` is a new layer directly above `errors` so `io` and `models` can share scenario-id rules and limits without a cycle. `io` may import `redaction` for the single text scrubber.
**Consequences.** `runner` sits above `reports` and `compare` and is therefore the only place a Report is built and written (AD-13).

## ADR-003 (AD-3) — Frozen, forbid-unknown models; integer schema versions; no strict mode
**Status:** Proposed (`[ASSUMPTION]`: integer version, not the spec example's string `"1"`).
**Context.** PRD AC-2.2 rejects unknown fields; the adversarial review showed `major.minor` tolerance contradicts that. The version lens showed Pydantic `strict=True` accepts RFC 3339 strings for `datetime` in JSON mode but rejects them in Python mode, so the same file would validate differently through the fixture and through `trace validate`.
**Decision.** `frozen=True, extra="forbid"`, no `strict`. Timestamps are validated `str` fields stored as given. One `parse_*` entry point per kind, always Python-mode validation on a dict. Integer versions with `SUPPORTED_VERSIONS` as the single reader allowlist.
**Alternatives.** `datetime` fields with a timezone check (normalizes `Z` to `+00:00` and breaks byte identity); `major.minor` with additive tolerance.
**Consequences.** Frequent integer bumps before 1.0; fixtures archived per version; other-stack producers emit an integer.

## ADR-004 (AD-4) — JSON Schemas generated from Pydantic
**Status:** Accepted.
**Decision.** Generate 2020-12 schemas with `model_json_schema()`, commit, fail CI on drift. `jsonschema` is dev-only.
**Consequences.** Field descriptions on serialized models are required so the published schema is readable.

## ADR-005 (AD-5) — Event addressing, Final Output, required Capture
**Status:** Proposed (`[ASSUMPTION]`: contiguous `seq`).
**Context.** Evidence must resolve identically everywhere (AC-8.1). The adversarial review found two owners of the capture default (runner and assertion).
**Decision.** `seq` 0-based contiguous; evidence is `list[int]`; Final Output on the last `agent_finished`; `Trace.capture` is required with model default `unknown`, so no shell step exists and the API and CLI agree.
**Alternatives.** Event UUIDs; run-level `final_output`; nullable capture defaulted by the runner.

## ADR-006 (AD-6) — One fold, one exit-code module, skip and absence in core
**Status:** Accepted (PRD AC-18.1 to AC-18.5, AC-21.3, AC-27.3, AC-27.4). The exit-3 trade-off stays PRD OQ-3.
**Context.** The first draft's fold ranked `skipped` above `passed`, contradicting AC-18.1, and left `skip`, absent traces, and adapter exceptions to whichever unit got there first.
**Decision.** Fold: `failed` > `error` > all-`skipped` > `passed`. `evaluate_scenario` interprets skip, execution errors, and absence, in that precedence, by fan-out to per-assertion results; an absent Trace under `fail_on_missing_trace: true` sets `execution_error`, so it reaches exit 3 as AC-27.3 requires; `engine.fold` is the only constructor of `SuiteOutcome` and derives `execution_failed` from the per-scenario errors; the runner converts adapter exceptions and continues; `cli/app.py` is the only exit site and maps escaped exceptions to 4. Scenarios require at least one assertion.
**Consequences.** A single adapter raise yields exit 3 for the run while the Report still lists every assertion failure; change `from_outcome` if OQ-3 goes the other way.

## ADR-007 (AD-7) — Error taxonomy
**Status:** Accepted.
**Decision.** `errors.py` is the only module defining exceptions; `InputError` carries a list of violations printed one per line; a malformed Trace named on the command line is input (2) while one read for an adapter during `run` is execution (3).

## ADR-008 (AD-8) — Assertion config in models, evaluators in assertions, one YAML form
**Status:** Accepted.
**Context.** The first draft built the discriminated union from the registry, which made `models` import `assertions` and inverted the layers. The PRD's prose shorthand (`tool_not_called: approve_expense`) invited a second YAML spelling.
**Decision.** Config models and the static union live in `models.assertions`; pure evaluators live in `assertions/builtin`; `EVALUATORS` maps type to evaluator with a test that its keys equal the union. Flat `type:` mapping is the only YAML form; `tool_call_count` takes exactly one operator key; ids default to `<type>-<index>` assigned in `models.suite`.
**Consequences.** Adding an assertion touches two modules plus the registry; third-party assertion plugins are a later decision.

## ADR-009 (AD-9) — Sync adapter protocol; the runner owns run identity
**Status:** Proposed (`[ASSUMPTION]`: sync-only; dotted-path adapter form).
**Context.** `run_id` and timestamps had three owners in the first draft; the Fixture Agent had no Suite field for its trace file and no base directory.
**Decision.** The runner generates and overwrites `run_id`, `started_at`, `ended_at`, and `environment` after `run` returns; adapters cannot influence them. `RunContext` lives in `adapters/protocol.py` and carries `suite_dir`. `scenario.trace` and `defaults.fixture.deterministic` are the Fixture Agent's Suite surface. Adapters raise `TraceMissingError` when they cannot produce a Trace. `testing.adapter_conformance.check` ships publicly.
**Alternatives.** Async protocol; adapters emitting events through a callback.
**Consequences.** Streaming adapters buffer; revisit with the first real adapter (PRD OQ-15).

## ADR-010 (AD-10) — Redaction at ingress, one rule set, one marker, one scrubber
**Status:** Accepted (PRD FR-31).
**Context.** Write-time redaction made live and replay evaluate different data; a second scrubber in `io.console` diverged on minimum length and ordering.
**Decision.** `redact` and `scrub_text` are the only two functions; `io` imports `scrub_text`. Redaction state merges across ingresses. The 8-character floor from the first draft was withdrawn into ARCH-6 because it narrows FR-31.
**Consequences.** Assertions see `[REDACTED]`; API equivalence is defined with `redact_trace` in the call.

## ADR-011 (AD-11) — Canonical form, compact form, volatile paths
**Status:** Proposed (`[ASSUMPTION]`: compact form for matching, PRD OQ-9).
**Context.** Assertions could not reach the serializer in `reports`; `VOLATILE_FIELDS` by key name at any depth would strip a tool argument named `cost` and missed event timestamps.
**Decision.** `models.canonical` at the bottom of the core with `dumps` (artifacts) and `dumps_compact` (matching); `VOLATILE_PATHS` as path patterns including event-level timestamps and durations.
**Consequences.** PRD AC-16.2 should read "compact Canonical form"; recorded as a conflict to update upstream.

## ADR-012 (AD-12) — Stdlib HTML rendering, no Jinja2, no JavaScript
**Status:** Accepted.
**Decision.** String templates with `html.escape(quote=True)`, `<details>` collapsing, CSP meta, evidence-referenced events always expanded, then the first 500 collapsed, the rest counted.

## ADR-013 (AD-13) — One pipeline, one Report builder, one writer
**Status:** Accepted.
**Context.** Critical adversarial finding: nobody owned Report construction, and replay written against the public API could skip env-value scrubbing.
**Decision.** `runner.run_suite` and `runner.replay` share one private pipeline; `reports.build_report` is the only Report constructor; `io.write_atomic` the only writer; the CLI never assembles a Report.

## ADR-014 (AD-14) — Fixed artifact names, atomic writes, one id rule
**Status:** Accepted (PRD FR-29, AC-2.5, AC-19.4, AC-23.6).
**Decision.** Id regex and device-name list in `constants`, validated once in `models.suite`; `io.paths` only asserts. `run`/`replay --output` is a directory; `report --output` is a file; HTML name derives from the JSON name. Temp files via `NamedTemporaryFile` then `os.replace`; atomic on POSIX, best effort on Windows.

## ADR-015 (AD-15) — Public API with a parse/load split and a 0.x policy
**Status:** Accepted (spec §10.3, PRD FR-34).
**Decision.** `parse_*` (core) and `load_*` (shell) for suite, trace, report; `evaluate_*`, `run_suite`, `replay`, `compare`; models; `Adapter`, `RunContext`; `testing`; `SUPPORTED_VERSIONS`; `__version__` from `importlib.metadata`. Minor releases may change the API before 1.0 with a changelog entry; patch releases may not.

## ADR-016 (AD-16) — Four runtime dependencies
**Status:** Accepted.
**Decision.** `pydantic`, `typer`, `rich`, `pyyaml`. Rejected for v0.1: `jsonschema` at runtime, `jinja2`, `jsonpath-ng`, `jmespath`, `orjson`.

## ADR-017 (AD-17) — Claims are tests; one check entry point mirrored in CI
**Status:** Proposed (`[ASSUMPTION]`: task runner open; mypy over pyright).
**Context.** The version lens showed `--network none` is not supported for Actions container jobs; the reconciliation showed the network guard covered only core tests and docs commands could drift from CI.
**Decision.** Guard active for every test except marked subprocess tests; networkless run via `docker run --network none` from a `run:` step; docs commands extracted from tagged fenced blocks; CI matrix 3.12 to 3.15 on Linux and Windows; actions pinned by SHA.

## ADR-018 (AD-18) — No services, no database, no telemetry, single process
**Status:** Accepted (user instruction, spec §5.1, PRD §5).
**Decision.** Files in the Output Directory are the only state; the runner is sequential and single-threaded; no storage abstraction.

## ADR-019 (AD-19) — Safe parsing and input limits
**Status:** Proposed (`[ASSUMPTION]`: 5 MB per file, PRD OQ-12).
**Context.** Safe YAML alone still allowed duplicate-key last-wins and alias expansion; limits had no home and "configured" contradicted the no-config convention.
**Decision.** One `SafeLoader` subclass rejecting duplicate keys, aliases, and multi-document streams; stdlib JSON only; size enforced by `io.read_limited` before parse against constants; `null` and absent equivalent on input, every key written on output.

## ADR-020 (AD-20) — CLI contract and fixed honesty statements
**Status:** Accepted (PRD FR-27 to FR-30, AC-23.6, AC-30.1; spec §6.1 replay form dropped).
**Context.** No AD fixed command signatures; the spec and PRD disagreed on replay's flags; the PRD's honesty statements had no home.
**Decision.** Exact command signatures listed in the spine; `trace replay TRACE_PATH --suite --scenario`; `--output` semantics per command; `junit` rejected until v0.2; fixed statements in `constants.STATEMENTS` shared by CLI, Report, and docs.

---

## Decisions explicitly not made

| Id | Question | Why it waits | Owner |
| --- | --- | --- | --- |
| OQ-1 | Distribution name | PyPI `agentproof` is taken by a same-space package | maintainer |
| OQ-2 | License | contributor-policy and dependency-license review | maintainer |
| OQ-3 | Exit-3 trade-off | PRD default kept; one function to change | maintainer |
| OQ-4 | Replay command name | `trace replay` kept; rename is a one-line change before release | maintainer |
| OQ-5 | Integer `version`, string timestamps, Final Output on `agent_finished` | confirm before EPIC B | maintainer |
| OQ-7 | Argument path syntax | dotted keys avoid a dependency | maintainer |
| OQ-9 | Compact form for structured-output matching | PRD AC-16.2 wording to update | maintainer |
| OQ-12 | 5 MB input limit | pick or measure | maintainer |
| OQ-13 | Minimum Python 3.12 | 3.12 is security-only upstream; 3.14 is the bugfix line | maintainer |
| OQ-16 | `./agentproof-output/` default | adopted | maintainer |
| OQ-18 | OTel GenAI mapping | conventions unstable as of 2026-10 | maintainer, v0.2 |
| ARCH-1 | mypy or pyright | pick once in EPIC A | maintainer |
| ARCH-2 | Sync-only adapters | revisit with the first real adapter | maintainer |
| ARCH-3 | Contiguous `seq` | relax to ascending-only if producers object | maintainer |
| ARCH-4 | Check task runner | any single entry point | EPIC A story |
| ARCH-5 | Fixture Suite surface (`scenario.trace`, `defaults.fixture.deterministic`) | confirm field names | maintainer |
| ARCH-6 | Minimum scrubbed secret length | no floor assumed; PIN-length secrets versus artifact corruption | maintainer |
| ARCH-7 | `pkg.module:ClassName` adapter form | supported assumed | maintainer |

## Upstream conflicts to resolve

- PRD AC-16.2 says structured Final Output is matched against "Canonical form text"; the spine matches against the compact form (AD-11, OQ-9). Update the PRD wording or change AD-11.
- PRD AC-18.2 describes an absent Trace as "the Adapter returns none"; the spine makes adapters raise `TraceMissingError` instead (AD-9). Semantics are unchanged; the PRD wording should follow.
- PRD AC-30.1 says `--adapter NAME`; the spine also accepts a dotted import path (ARCH-7).
