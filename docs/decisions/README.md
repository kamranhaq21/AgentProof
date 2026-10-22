# Decision records

One file per architecture decision. ADR-001 to ADR-020 implement AD-1 to AD-20 of the
[architecture spine](../../_bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md)
one to one and carry the full text of the planning-time
[`adr-log.md`](../../_bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md);
`0000` and `0021` are stubs for open questions (OQ-1 and OQ-2) that hold no decision yet.
How to add a record is in [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

Status values: **Accepted** (settled by the spec, PRD, or the architecture run),
**Proposed** (chosen under an `[ASSUMPTION]`; the maintainer confirms or changes it),
**open** (no decision yet).

| Record | Title | Status |
| --- | --- | --- |
| [0000-distribution-name.md](0000-distribution-name.md) | Distribution name (OQ-1) | open |
| [0001-functional-core-imperative-shell.md](0001-functional-core-imperative-shell.md) | ADR-001 (AD-1): Functional core, imperative shell | Accepted |
| [0002-enforced-dependency-direction-with-one-written-contract.md](0002-enforced-dependency-direction-with-one-written-contract.md) | ADR-002 (AD-2): Enforced dependency direction with one written contract | Accepted |
| [0003-frozen-forbid-unknown-models-integer-schema-versions-no-strict-mode.md](0003-frozen-forbid-unknown-models-integer-schema-versions-no-strict-mode.md) | ADR-003 (AD-3): Frozen, forbid-unknown models; integer schema versions; no strict mode | Proposed |
| [0004-json-schemas-generated-from-pydantic.md](0004-json-schemas-generated-from-pydantic.md) | ADR-004 (AD-4): JSON Schemas generated from Pydantic | Accepted |
| [0005-event-addressing-final-output-required-capture.md](0005-event-addressing-final-output-required-capture.md) | ADR-005 (AD-5): Event addressing, Final Output, required Capture | Proposed |
| [0006-one-fold-one-exit-code-module-skip-and-absence-in-core.md](0006-one-fold-one-exit-code-module-skip-and-absence-in-core.md) | ADR-006 (AD-6): One fold, one exit-code module, skip and absence in core | Accepted |
| [0007-error-taxonomy.md](0007-error-taxonomy.md) | ADR-007 (AD-7): Error taxonomy | Accepted |
| [0008-assertion-config-in-models-evaluators-in-assertions-one-yaml-form.md](0008-assertion-config-in-models-evaluators-in-assertions-one-yaml-form.md) | ADR-008 (AD-8): Assertion config in models, evaluators in assertions, one YAML form | Accepted |
| [0009-sync-adapter-protocol-the-runner-owns-run-identity.md](0009-sync-adapter-protocol-the-runner-owns-run-identity.md) | ADR-009 (AD-9): Sync adapter protocol; the runner owns run identity | Proposed |
| [0010-redaction-at-ingress-one-rule-set-one-marker-one-scrubber.md](0010-redaction-at-ingress-one-rule-set-one-marker-one-scrubber.md) | ADR-010 (AD-10): Redaction at ingress, one rule set, one marker, one scrubber | Accepted |
| [0011-canonical-form-compact-form-volatile-paths.md](0011-canonical-form-compact-form-volatile-paths.md) | ADR-011 (AD-11): Canonical form, compact form, volatile paths | Proposed |
| [0012-stdlib-html-rendering-no-jinja2-no-javascript.md](0012-stdlib-html-rendering-no-jinja2-no-javascript.md) | ADR-012 (AD-12): Stdlib HTML rendering, no Jinja2, no JavaScript | Accepted |
| [0013-one-pipeline-one-report-builder-one-writer.md](0013-one-pipeline-one-report-builder-one-writer.md) | ADR-013 (AD-13): One pipeline, one Report builder, one writer | Accepted |
| [0014-fixed-artifact-names-atomic-writes-one-id-rule.md](0014-fixed-artifact-names-atomic-writes-one-id-rule.md) | ADR-014 (AD-14): Fixed artifact names, atomic writes, one id rule | Accepted |
| [0015-public-api-with-a-parse-load-split-and-a-0-x-policy.md](0015-public-api-with-a-parse-load-split-and-a-0-x-policy.md) | ADR-015 (AD-15): Public API with a parse/load split and a 0.x policy | Accepted |
| [0016-four-runtime-dependencies.md](0016-four-runtime-dependencies.md) | ADR-016 (AD-16): Four runtime dependencies | Accepted |
| [0017-claims-are-tests-one-check-entry-point-mirrored-in-ci.md](0017-claims-are-tests-one-check-entry-point-mirrored-in-ci.md) | ADR-017 (AD-17): Claims are tests; one check entry point mirrored in CI | Proposed |
| [0018-no-services-no-database-no-telemetry-single-process.md](0018-no-services-no-database-no-telemetry-single-process.md) | ADR-018 (AD-18): No services, no database, no telemetry, single process | Accepted |
| [0019-safe-parsing-and-input-limits.md](0019-safe-parsing-and-input-limits.md) | ADR-019 (AD-19): Safe parsing and input limits | Proposed |
| [0020-cli-contract-and-fixed-honesty-statements.md](0020-cli-contract-and-fixed-honesty-statements.md) | ADR-020 (AD-20): CLI contract and fixed honesty statements | Accepted |
| [0021-license.md](0021-license.md) | License (OQ-2) | open |
