---
id: 3
type: story
title: "compare command with its exit mapping and statement"
parent: epic-07-baseline-comparison
covers: [R3]
after: [2]
hitl: false
risk: low
refined: true
---

# compare command with its exit mapping and statement

## Description

The command and its exit function, completing the three-question workflow in the CLI.

## Requirements

1. **Command** (R3; spine AD-20)
   **Given** `agentproof compare BASELINE_REPORT CURRENT_REPORT [--output FILE]`
   **When** run on two Reports
   **Then** it prints a summary of each difference kind, prints `STATEMENTS.compare_is_saved_data`, and with `--output` writes the Comparison JSON through `write_atomic`.
2. **Exit mapping** (R3; spine AD-6; PRD AC-26.2, AC-26.4)
   **Given** `cli.exit_codes.from_comparison`
   **When** the Comparison has `regressed` true
   **Then** the command exits 1; otherwise 0; identical Reports exit 0 with "no differences".
3. **Invalid input** (R3; PRD AC-25.1)
   **Given** a file that is not a Report, or an unsupported version
   **When** `compare` runs
   **Then** it exits 2 with one line, handled by the app's error handler before `from_comparison`.
4. **Public API only and complete** (R3; spine AD-15; PRD AC-34.3)
   **Given** the command module and `agentproof.__all__`
   **When** inspected after this story
   **Then** the module uses `load_report`, `compare`, `dumps_comparison`, and `io.write_atomic` only, and `__all__` equals the full AD-15 list, with the public-API test updated to assert equality rather than containment; this story is the last to add a public name in v0.1.

## Boundaries

- Must not change: `compare` semantics.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-07-baseline-comparison/epic-07-baseline-comparison.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-15, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-26, AC-26.2, AC-26.4, AC-26.6

## Notes

- Files: `src/agentproof/cli/commands/compare.py`, `src/agentproof/cli/exit_codes.py` (`from_comparison` already exists; wire it).
- Tests: `tests/integration/cli/test_compare.py` (subprocess; 0, 1, 2 paths; statement present; `--output`).
- Depends on: story 2. Risk: low.
- Done when: criteria 1 to 4 pass on both CI platforms.
