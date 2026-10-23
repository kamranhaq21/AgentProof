# ADR-002 (AD-2): Enforced dependency direction with one written contract

**Status:** Accepted.
**Context.** The first draft had three inconsistent descriptions of the graph (diagram, layer list, registry union). Independent builders would have followed different ones.
**Decision.** The `.importlinter` layer contract is reproduced verbatim in the spine and is the authority; the diagram mirrors it, and `forbidden` contracts cover the modules outside the stack (`io`, `adapters`, `testing`, `cli`). `constants` is a new layer directly above `errors` so `io` and `models` can share scenario-id rules and limits without a cycle. `io` may import `redaction` for the single text scrubber.
**Consequences.** `runner` sits above `reports` and `compare` and is therefore the only place a Report is built and written (AD-13).
