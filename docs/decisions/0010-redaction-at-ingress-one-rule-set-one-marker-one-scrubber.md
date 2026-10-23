# ADR-010 (AD-10): Redaction at ingress, one rule set, one marker, one scrubber

**Status:** Accepted (PRD FR-31).
**Context.** Write-time redaction made live and replay evaluate different data; a second scrubber in `io.console` diverged on minimum length and ordering.
**Decision.** `redact` and `scrub_text` are the only two functions; `io` imports `scrub_text`. Redaction state merges across ingresses. The 8-character floor from the first draft was withdrawn into ARCH-6 because it narrows FR-31.
**Consequences.** Assertions see `[REDACTED]`; API equivalence is defined with `redact_trace` in the call.
