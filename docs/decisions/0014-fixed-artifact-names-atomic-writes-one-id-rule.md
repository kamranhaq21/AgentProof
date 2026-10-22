# ADR-014 (AD-14): Fixed artifact names, atomic writes, one id rule

**Status:** Accepted (PRD FR-29, AC-2.5, AC-19.4, AC-23.6).
**Decision.** Id regex and device-name list in `constants`, validated once in `models.suite`; `io.paths` only asserts. `run`/`replay --output` is a directory; `report --output` is a file; HTML name derives from the JSON name. Temp files via `NamedTemporaryFile` then `os.replace`; atomic on POSIX, best effort on Windows.
