# ADR-015 (AD-15): Public API with a parse/load split and a 0.x policy

**Status:** Accepted (spec §10.3, PRD FR-34).
**Decision.** `parse_*` (core) and `load_*` (shell) for suite, trace, report; `evaluate_*`, `run_suite`, `replay`, `compare`; models; `Adapter`, `RunContext`; `testing`; `SUPPORTED_VERSIONS`; `__version__` from `importlib.metadata`. Minor releases may change the API before 1.0 with a changelog entry; patch releases may not.
