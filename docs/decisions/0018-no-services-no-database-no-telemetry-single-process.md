# ADR-018 (AD-18): No services, no database, no telemetry, single process

**Status:** Accepted (user instruction, spec §5.1, PRD §5).
**Decision.** Files in the Output Directory are the only state; the runner is sequential and single-threaded; no storage abstraction.
