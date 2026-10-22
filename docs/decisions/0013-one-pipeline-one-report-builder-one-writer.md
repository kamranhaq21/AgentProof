# ADR-013 (AD-13): One pipeline, one Report builder, one writer

**Status:** Accepted.
**Context.** Critical adversarial finding: nobody owned Report construction, and replay written against the public API could skip env-value scrubbing.
**Decision.** `runner.run_suite` and `runner.replay` share one private pipeline; `reports.build_report` is the only Report constructor; `io.write_atomic` the only writer; the CLI never assembles a Report.
