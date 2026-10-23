# ADR-019 (AD-19): Safe parsing and input limits

**Status:** Proposed (`[ASSUMPTION]`: 5 MB per file, PRD OQ-12).
**Context.** Safe YAML alone still allowed duplicate-key last-wins and alias expansion; limits had no home and "configured" contradicted the no-config convention.
**Decision.** One `SafeLoader` subclass rejecting duplicate keys, aliases, and multi-document streams; stdlib JSON only; size enforced by `io.read_limited` before parse against constants; `null` and absent equivalent on input, every key written on output.
