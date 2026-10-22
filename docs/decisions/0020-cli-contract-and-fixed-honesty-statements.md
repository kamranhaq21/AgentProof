# ADR-020 (AD-20): CLI contract and fixed honesty statements

**Status:** Accepted (PRD FR-27 to FR-30, AC-23.6, AC-30.1; spec §6.1 replay form dropped).
**Context.** No AD fixed command signatures; the spec and PRD disagreed on replay's flags; the PRD's honesty statements had no home.
**Decision.** Exact command signatures listed in the spine; `trace replay TRACE_PATH --suite --scenario`; `--output` semantics per command; `junit` rejected until v0.2; fixed statements in `constants.STATEMENTS` shared by CLI, Report, and docs.
