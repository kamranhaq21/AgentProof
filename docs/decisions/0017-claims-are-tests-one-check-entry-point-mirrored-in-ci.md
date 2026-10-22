# ADR-017 (AD-17): Claims are tests; one check entry point mirrored in CI

**Status:** Proposed (`[ASSUMPTION]`: task runner open; mypy over pyright).
**Context.** The version lens showed `--network none` is not supported for Actions container jobs; the reconciliation showed the network guard covered only core tests and docs commands could drift from CI.
**Decision.** Guard active for every test except marked subprocess tests; networkless run via `docker run --network none` from a `run:` step; docs commands extracted from tagged fenced blocks; CI matrix 3.12 to 3.15 on Linux and Windows; actions pinned by SHA.
