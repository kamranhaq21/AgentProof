---
type: epic
title: "Scenario loader and CLI: a Suite loads safely with every violation reported, and init, validate, and version work on the scaffolded example"
parent: initiative-agentproof-mvp
covers: ["R1", "R2", "R17", "R18", "R19", "R25", "C3", "C6"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: high
---

# Scenario loader and CLI

## Description

The first user-facing surface: the one safe YAML loader, size-limited file reading in the shell, `parse_suite` and `load_suite` returning every violation, the Typer app with its single error handler and exit-code module, the console scrubber and logging filter, and the `init`, `validate`, and `version` commands with the signatures in spine AD-20. The scaffolded example Suite and its fixture Trace files are the data the rest of the initiative demonstrates on.

## Outcome

For a first-time user, `agentproof init` then `agentproof validate` on the result exits 0 with a readable summary, and a broken Suite exits 2 with one line per problem and no traceback (PRD UJ-4, first half).

## Requirements

- R1 (parent R1, R25): `loading.yaml_safe.load` rejects custom tags, duplicate mapping keys naming key and line, aliases and anchors, and a second document; `io.read_limited` rejects files over `MAX_SUITE_BYTES` before parsing and refuses symlinks resolving outside the Suite directory; `parse_suite(text, source=)` returns a Suite or raises `SuiteError` carrying every violation.
- R2 (parent R2): `agentproof init [PATH]` writes the expense-agent example Suite, its fixture Trace files under `traces/`, and nothing else, refuses to overwrite any existing file naming the first conflict, and the result validates.
- R3 (parent R17, C3): `cli/app.py` holds the only exit sites, maps `InputError` to 2 printing one line per violation in the error shape, maps any other escaped exception to 4 with a one-line message and a traceback only under `--verbose`, and `cli.exit_codes` exposes `from_outcome` and `from_comparison`.
- R4 (parent R18): `validate SUITE_PATH`, `version`, and `init [PATH]` exist with exactly the AD-20 signatures; `--help` on each lists arguments, options, and exit codes; `version` prints the package version and the supported Schema Versions.
- R5 (parent C6, initiative R19): `redaction.scrub_text(text, secret_values)` exists with longest-first replacement by `constants.REDACTED`, and `io.console` installs it as a filter on every print and log line, honoring `--no-color`.

## Constraints

- Covered parent constraints: C3 (one fold, one exit module, exact CLI signatures) and C6 (safe loader, constant limits, one text scrubber); the lines below say how.
- Spine AD-19: `yaml_safe` is the only YAML entry point; `json.loads` the only JSON parser.
- Spine AD-20: no command beyond `init`, `validate`, `version` in this epic; `run`, `trace`, `compare`, `report` are registered as stubs that exit 2 with "not implemented" only if the app needs the group, otherwise absent.
- Spine AD-1: `loading` never sees a path; the shell reads and passes text plus `source`.
- Spine AD-10: `scrub_text` is the only text scrubber; epic 5 adds `redact` beside it.

## Done when

- `agentproof init` in an empty directory, then `agentproof validate agentproof.yaml`, exits 0 and prints the Scenario count; the same on Windows CI (R2, R4).
- Each malformed-Suite fixture (custom tag, duplicate key, alias, second document, oversized file, unknown field, unknown type, duplicate id) makes `validate` exit 2 with one line per violation and no traceback (R1, R3).
- `agentproof validate` with `--verbose` on an injected internal error exits 4 and prints a traceback; without it, one line (R3).
- A planted secret value passed through `scrub_text` never appears in captured console output (R5).
- Production delivery: the wheel built in CI exposes the three commands and `agentproof --help` lists them (R4).

## Boundaries

- No evaluation, adapters, or `run` (epic 4); no Trace export or Replay (epic 5); no reports (epic 6).
- Must not change: the models from epic 2; a loader finding they need a change raises a `Source conflict:` in epic 2.
- Touch point: `examples/expense-agent/` as the init template source; owner: this epic.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-7, AD-10, AD-14, AD-19, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-1 to FR-4, FR-27 to FR-30, UJ-4
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-007, ADR-019, ADR-020

## Notes

- Decision (2026-10-22): tracer bullet is story 1, the Typer app with `version` and the error handler, proving the exit-code path 0, 2, and 4 before any loader exists.
- Decision (2026-10-22): `scrub_text` and the console filter are built here (story 5) because the CLI needs them before epic 5's `redact`; both live in `redaction/` per AD-10.
- Decision (2026-10-22): the init template's fixture Trace files are hand-written against the epic 2 Trace model and validated by the init test; the Fixture Agent that reads them is epic 4.
- Assumption: `MAX_SUITE_BYTES` is 5 MB (OQ-12).
