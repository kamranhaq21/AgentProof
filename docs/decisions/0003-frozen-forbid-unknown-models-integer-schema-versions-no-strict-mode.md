# ADR-003 (AD-3): Frozen, forbid-unknown models; integer schema versions; no strict mode

**Status:** Proposed (`[ASSUMPTION]`: integer version, not the spec example's string `"1"`).
**Context.** PRD AC-2.2 rejects unknown fields; the adversarial review showed `major.minor` tolerance contradicts that. The version lens showed Pydantic `strict=True` accepts RFC 3339 strings for `datetime` in JSON mode but rejects them in Python mode, so the same file would validate differently through the fixture and through `trace validate`.
**Decision.** `frozen=True, extra="forbid"`, no `strict`. Timestamps are validated `str` fields stored as given. One `parse_*` entry point per kind, always Python-mode validation on a dict. Integer versions with `SUPPORTED_VERSIONS` as the single reader allowlist.
**Alternatives.** `datetime` fields with a timezone check (normalizes `Z` to `+00:00` and breaks byte identity); `major.minor` with additive tolerance.
**Consequences.** Frequent integer bumps before 1.0; fixtures archived per version; other-stack producers emit an integer.
