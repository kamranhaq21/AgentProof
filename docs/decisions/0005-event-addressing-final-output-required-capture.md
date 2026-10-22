# ADR-005 (AD-5): Event addressing, Final Output, required Capture

**Status:** Proposed (`[ASSUMPTION]`: contiguous `seq`).
**Context.** Evidence must resolve identically everywhere (AC-8.1). The adversarial review found two owners of the capture default (runner and assertion).
**Decision.** `seq` 0-based contiguous; evidence is `list[int]`; Final Output on the last `agent_finished`; `Trace.capture` is required with model default `unknown`, so no shell step exists and the API and CLI agree.
**Alternatives.** Event UUIDs; run-level `final_output`; nullable capture defaulted by the runner.
