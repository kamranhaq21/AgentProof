---
id: 1
type: story
title: "Typer app with the error handler, exit-code module, and version command"
parent: epic-03-scenario-loader-and-cli
covers: [R3, R4]
after: ["2.1", "2.4"]
hitl: false
risk: medium
refined: true
---

# Typer app with the error handler, exit-code module, and version command

## Description

The tracer bullet for the CLI: the one place exits happen, the one place input errors become lines and unexpected errors become exit 4, and the first real command. Everything later plugs into this app.

## Requirements

1. **Single exit site** (R3; spine AD-6, AD-20)
   **Given** `agentproof.cli.app`
   **When** the package is grepped
   **Then** `typer.Exit` and `sys.exit` appear only in `cli/app.py`, verified by a test.
2. **Error handler** (R3; spine AD-7; PRD AC-28.1, AC-2.4)
   **Given** a command that raises `InputError` with two violations
   **When** it runs
   **Then** the process prints two lines `<kind>: <message> (<source>:<field>)` and exits 2 with no traceback; and when a command raises an unexpected exception, it prints one line and exits 4, adding the traceback only with `--verbose`.
3. **Exit-code module** (R3; spine AD-6)
   **Given** `agentproof.cli.exit_codes`
   **When** it is imported
   **Then** it exposes exactly `from_outcome(outcome) -> int` and `from_comparison(comparison) -> int`, implementing the AD-6 mapping with unit tests for each branch.
4. **version command** (R4; spine AD-20; PRD AC-30.2)
   **Given** `agentproof version`
   **When** it runs
   **Then** it prints the package version and `SUPPORTED_VERSIONS` for suite, trace, and report and exits 0; `agentproof --help` lists `version` and the global options `--verbose` and `--no-color`.
5. **Fault injection** (R3; spine AD-17; PRD AC-27.1)
   **Given** `AGENTPROOF_TESTING=1` and `AGENTPROOF_FAULT_INJECT=cli.version`
   **When** `agentproof version` runs
   **Then** it exits 4; without `AGENTPROOF_TESTING=1` the variable is ignored.

## Boundaries

- No other commands; `validate` and `init` come in stories 4 and 6.
- Must not change: `constants`, `errors`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-03-scenario-loader-and-cli/epic-03-scenario-loader-and-cli.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-7, AD-17, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-27, FR-28, FR-30

## Notes

- Files: `src/agentproof/cli/app.py`, `src/agentproof/cli/exit_codes.py`, `src/agentproof/cli/commands/version.py`, `src/agentproof/__init__.py` (`__version__`).
- Tests: `tests/unit/cli/test_exit_codes.py`, `tests/unit/cli/test_single_exit_site.py`, `tests/integration/cli/test_version_and_errors.py` (subprocess, marked `allow_subprocess`).
- Depends on: 2.1 (constants, errors) and 2.4 (`SuiteOutcome` and `Comparison`, the types `from_outcome` and `from_comparison` take). Risk: medium; the fault-injection hook must be unreachable in normal use.
- Done when: criteria 1 to 5 pass on both CI platforms.
