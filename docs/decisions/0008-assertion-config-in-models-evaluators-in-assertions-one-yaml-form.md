# ADR-008 (AD-8): Assertion config in models, evaluators in assertions, one YAML form

**Status:** Accepted.
**Context.** The first draft built the discriminated union from the registry, which made `models` import `assertions` and inverted the layers. The PRD's prose shorthand (`tool_not_called: approve_expense`) invited a second YAML spelling.
**Decision.** Config models and the static union live in `models.assertions`; pure evaluators live in `assertions/builtin`; `EVALUATORS` maps type to evaluator with a test that its keys equal the union. Flat `type:` mapping is the only YAML form; `tool_call_count` takes exactly one operator key; ids default to `<type>-<index>` assigned in `models.suite`.
**Consequences.** Adding an assertion touches two modules plus the registry; third-party assertion plugins are a later decision.
