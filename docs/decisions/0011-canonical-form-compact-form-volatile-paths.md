# ADR-011 (AD-11): Canonical form, compact form, volatile paths

**Status:** Proposed (`[ASSUMPTION]`: compact form for matching, PRD OQ-9).
**Context.** Assertions could not reach the serializer in `reports`; `VOLATILE_FIELDS` by key name at any depth would strip a tool argument named `cost` and missed event timestamps.
**Decision.** `models.canonical` at the bottom of the core with `dumps` (artifacts) and `dumps_compact` (matching); `VOLATILE_PATHS` as path patterns including event-level timestamps and durations.
**Consequences.** PRD AC-16.2 should read "compact Canonical form"; recorded as a conflict to update upstream.
