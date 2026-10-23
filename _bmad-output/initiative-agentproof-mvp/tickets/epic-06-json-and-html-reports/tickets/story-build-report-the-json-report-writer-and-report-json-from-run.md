---
id: 1
type: story
title: "build_report, the JSON Report writer, and report.json from run and replay"
parent: epic-06-json-and-html-reports
covers: [R1, R3]
after: ["5.3", "5.4"]
hitl: false
risk: medium
refined: true
---

# build_report, the JSON Report writer, and report.json from run and replay

## Description

The tracer bullet of the epic: the one constructor of a Report, the Canonical writer for it, and the pipeline steps that write `report.json` after the Traces for a run and `replay-<id>.report.json` for Replay. The first Report golden file lands here.

## Requirements

1. **build_report** (R1; spine AD-13; PRD AC-22.3, AC-22.4)
   **Given** `reports.build.build_report(outcome, suite=, run_id=, created_at=, package_version=, traces=)`
   **When** called with the run's outcome
   **Then** it returns a Report whose `counts` equal the sum over Assertion Results, whose `defaults` is the Suite's `SuiteDefaults`, whose `schema_versions` names suite and trace version 1, and whose Scenarios embed their redacted Trace or `null`; a grep test asserts no other module constructs `Report`.
2. **Writer** (R1; spine AD-11)
   **Given** `reports.json_report.dumps(report)`
   **When** called
   **Then** it returns `canonical.dumps` of the Report; it is exported as `dumps_report`.
3. **Pipeline writes** (R1; spine AD-13, AD-14; PRD FR-22, AC-19.4)
   **Given** `agentproof run` and `agentproof trace replay`
   **When** they complete
   **Then** `run` writes `report.json` into the Output Directory after the Trace files, `replay` writes `replay-<scenario id>.report.json` and nothing else, both through `write_atomic`, and `report.json` validates against `schemas/report-v1.schema.json`.
4. **Golden** (R3; spine AD-11; PRD AC-22.2)
   **Given** two deterministic runs of the example
   **When** their `report.json` files are stripped of `VOLATILE_PATHS`
   **Then** they are byte-identical and equal `tests/golden/report-example.json` on Linux and Windows CI.

## Boundaries

- No HTML (story 2).
- Must not change: the Report model; a needed field is a `Source conflict:` in epic 2.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-06-json-and-html-reports/epic-06-json-and-html-reports.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-11, AD-13, AD-14
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-22, AC-22.1 to AC-22.4, AC-19.4

## Notes

- Files: `src/agentproof/reports/build.py`, `src/agentproof/reports/json_report.py`, `src/agentproof/runner/pipeline.py` (report steps), `src/agentproof/__init__.py` (`dumps_report`), `tests/golden/report-example.json`.
- Tests: `tests/unit/reports/test_build_report.py`, `tests/unit/reports/test_single_constructor.py`, `tests/integration/test_report_files.py` (run and replay writes, schema validation, golden).
- Depends on: 5.3 and 5.4. Risk: medium.
- Done when: criteria 1 to 4 pass on both CI platforms.
