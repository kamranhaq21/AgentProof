# ADR-007 (AD-7): Error taxonomy

**Status:** Accepted.
**Decision.** `errors.py` is the only module defining exceptions; `InputError` carries a list of violations printed one per line; a malformed Trace named on the command line is input (2) while one read for an adapter during `run` is execution (3).
