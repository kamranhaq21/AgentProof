# ADR-009 (AD-9): Sync adapter protocol; the runner owns run identity

**Status:** Proposed (`[ASSUMPTION]`: sync-only; dotted-path adapter form).
**Context.** `run_id` and timestamps had three owners in the first draft; the Fixture Agent had no Suite field for its trace file and no base directory.
**Decision.** The runner generates and overwrites `run_id`, `started_at`, `ended_at`, and `environment` after `run` returns; adapters cannot influence them. `RunContext` lives in `adapters/protocol.py` and carries `suite_dir`. `scenario.trace` and `defaults.fixture.deterministic` are the Fixture Agent's Suite surface. Adapters raise `TraceMissingError` when they cannot produce a Trace. `testing.adapter_conformance.check` ships publicly.
**Alternatives.** Async protocol; adapters emitting events through a callback.
**Consequences.** Streaming adapters buffer; revisit with the first real adapter (PRD OQ-15).
