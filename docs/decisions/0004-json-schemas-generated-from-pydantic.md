# ADR-004 (AD-4): JSON Schemas generated from Pydantic

**Status:** Accepted.
**Decision.** Generate 2020-12 schemas with `model_json_schema()`, commit, fail CI on drift. `jsonschema` is dev-only.
**Consequences.** Field descriptions on serialized models are required so the published schema is readable.
