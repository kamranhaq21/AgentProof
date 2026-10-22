# ADR-001 (AD-1): Functional core, imperative shell

**Status:** Accepted.
**Context.** The product's central promise is deterministic re-evaluation of a recorded trace (PRD NFR-1; spec principle 11). Determinism fails the moment evaluation code touches a clock, the environment, or the filesystem. The first draft banned only writes; the adversarial review showed a reader in the core produced two incompatible `load_suite` signatures and a second non-atomic writer.
**Decision.** Everything that computes is a pure function over frozen models and never touches files, clocks, ids, or the environment. The shell (`adapters`, `runner`, `io`, `cli`) does all of that and passes values in. Enforced by an import-linter forbidden contract and a ruff banned-API list.
**Alternatives.** Layered services holding state; an actor or pipeline framework.
**Consequences.** Core functions take text or bytes plus a `source` label; the public API has a `parse_*` (core) and `load_*` (shell) pair for every artifact kind.
