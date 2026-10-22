# ADR-006 (AD-6): One fold, one exit-code module, skip and absence in core

**Status:** Accepted (PRD AC-18.1 to AC-18.5, AC-21.3, AC-27.3, AC-27.4). The exit-3 trade-off stays PRD OQ-3.
**Context.** The first draft's fold ranked `skipped` above `passed`, contradicting AC-18.1, and left `skip`, absent traces, and adapter exceptions to whichever unit got there first.
**Decision.** Fold: `failed` > `error` > all-`skipped` > `passed`. `evaluate_scenario` interprets skip, execution errors, and absence, in that precedence, by fan-out to per-assertion results; an absent Trace under `fail_on_missing_trace: true` sets `execution_error`, so it reaches exit 3 as AC-27.3 requires; `engine.fold` is the only constructor of `SuiteOutcome` and derives `execution_failed` from the per-scenario errors; the runner converts adapter exceptions and continues; `cli/app.py` is the only exit site and maps escaped exceptions to 4. Scenarios require at least one assertion.
**Consequences.** A single adapter raise yields exit 3 for the run while the Report still lists every assertion failure; change `from_outcome` if OQ-3 goes the other way.
