# Review: versions and technology facts — AgentProof v0.1 spine

Reviewed 2026-10-22 against primary sources (PyPI, python.org, pydantic.dev, GitHub Docs, tool docs). Spine not edited.

## Verdict

The Stack table is current to the day: every lower bound exists, every upper bound sits on a shipping major, nothing is deprecated. Python facts are slightly stale (3.15.0 shipped 2026-10-09; 3.12 and 3.13 are security-only) but the floor and matrix remain defensible. Two claims would mislead a builder: a networkless container job cannot be written through GitHub's `container.options` (`--network` is unsupported), and Pydantic `strict=True` rejects RFC 3339 *strings* for `datetime` fields on the YAML/Python path, so AD-3 and the Dates convention conflict unless timestamps are typed `str`. Everything else checked out.

## Verification table

| Item | Spine says | Verified 2026-10-22 | Status | Source |
| --- | --- | --- | --- | --- |
| Python | >=3.12,<4; CI 3.12–3.14 | 3.15.1 latest (3.15.0 on 2026-10-09); 3.14 bugfix; 3.12/3.13 security; 3.12 EOL 2028-10 | stale | https://devguide.python.org/versions/ |
| uv | 0.13.x | 0.13.5 | confirmed | https://pypi.org/pypi/uv/json |
| pydantic | >=2.14,<3 | 2.14.1; 2.14.0 adds 3.15, drops 3.9 | confirmed | https://pypi.org/pypi/pydantic/json |
| typer | >=0.27,<1 | 0.27.3; 0.27.0's only break is metavar printing | confirmed | https://typer.tiangolo.com/release-notes/ |
| rich | >=15,<16 | 15.0.0 | confirmed | https://pypi.org/pypi/rich/json |
| PyYAML | >=6.0.3,<7 | 6.0.3 | confirmed | https://pypi.org/pypi/PyYAML/json |
| pytest | >=9.1 | 9.1.1 | confirmed | https://pypi.org/pypi/pytest/json |
| hypothesis | >=6.170 | 6.170.5; requires >=3.11 | confirmed | https://pypi.org/pypi/hypothesis/json |
| ruff | >=0.17 | 0.17.1 | confirmed | https://pypi.org/pypi/ruff/json |
| mypy | >=2.4 | 2.4.0 | confirmed | https://pypi.org/pypi/mypy/json |
| import-linter | >=2.15 | 2.15 | confirmed | https://pypi.org/pypi/import-linter/json |
| jsonschema | >=4.26 | 4.26.0 | confirmed | https://pypi.org/pypi/jsonschema/json |
| pytest-cov | >=7.1 | 7.1.0 | confirmed | https://pypi.org/pypi/pytest-cov/json |
| pip-audit | >=2.10 | 2.10.1 | confirmed | https://pypi.org/pypi/pip-audit/json |
| 3.15 classifiers | matrix stops at 3.14 | pydantic, pytest, hypothesis, mypy, ruff declare 3.15; typer, rich, import-linter not yet | stale | PyPI classifiers |
| `ConfigDict(frozen, extra="forbid", strict)` | rejects unknown fields, no coercion | all documented; `extra_forbidden` on unknown keys | confirmed | https://pydantic.dev/docs/validation/latest/api/pydantic/config/ |
| strict + RFC 3339 strings | string timestamps; strict models | Python-mode strict accepts only `datetime` instances; `str` is lax-only (JSON mode accepts `str`) | wrong (if typed `datetime`) | https://pydantic.dev/docs/validation/latest/concepts/conversion_table/ |
| `model_json_schema()` dialect | 2020-12 | "compliant with JSON Schema Draft 2020-12" | confirmed | https://pydantic.dev/docs/validation/latest/concepts/json_schema/ |
| Discriminated union on `Literal` `type` | registry-built | `Field(discriminator=...)` with `Literal` tags documented; runtime-built unions undocumented | confirmed / unverifiable (dynamic) | https://pydantic.dev/docs/validation/latest/concepts/unions/ |
| pydantic mypy plugin | mypy --strict | ships with pydantic, "tested against the latest mypy"; no deprecation | confirmed | https://pydantic.dev/docs/validation/latest/integrations/dev-tools/mypy/ |
| import-linter layers | `{a, b}` sets | `type = layers`; siblings via pipe (independent) or `:`; `containers`, `exhaustive` | confirmed | https://import-linter.readthedocs.io/en/stable/contract_types/layers/ |
| Typer groups | `trace validate` | `app.add_typer(sub, name="trace")` is current | confirmed | https://typer.tiangolo.com/tutorial/subcommands/add-typer/ |
| `html.escape(quote=True)` | text and quoted attributes | `& < >` always; `"` `'` when quote=True (default) | confirmed | https://docs.python.org/3/library/html.html |
| `os.replace` | temp-then-replace; Windows lock failures | atomic "is a POSIX requirement"; Windows atomicity undocumented; open/read-only dst raises PermissionError | confirmed (caveat) | https://docs.python.org/3/library/os.html#os.replace ; https://bugs.python.org/issue8828 |
| RefResolver vs Registry | old fetches HTTP; new does not | RefResolver "did automatically retrieve remote references", now "fully deprecated"; Registry "does not" unless `retrieve` given | confirmed | https://python-jsonschema.readthedocs.io/en/stable/referencing/ |
| Trusted publishing | release path | OIDC publishing documented, replaces long-lived tokens | confirmed | https://docs.pypi.org/trusted-publishers/ |
| `--network none` container job | AD-16/17 | "The `--network` and `--entrypoint` options are not supported" | wrong | https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax |
| Actions pinned by SHA | AD-17 | still recommended; a workflow lockfile "supersedes SHA pinning" where adopted | confirmed | https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions |
| `from __future__ import annotations` | required | "will eventually be deprecated and removed" (PEP 649/749); redundant on 3.14+ | stale | https://docs.python.org/3/library/__future__.html |
| PyPI `agentproof` taken | OQ-1 | 0.1.0 published 2026-02-17 | confirmed | https://pypi.org/pypi/agentproof/json |

Counts: confirmed 24, stale 3, wrong 2, unverifiable 1.

## Findings

- **[high]** `--network none` cannot be set on a GitHub Actions container job (AD-16, AD-17) — `container.options` rejects `--network`; the workflow fails to parse. *Fix:* run the example suite via `docker run --network none ...` (or `unshare -n`) from a `run:` step on `ubuntu-latest`; keep the `conftest` socket guard per test.
- **[high]** `strict=True` rejects RFC 3339 strings for `datetime` fields on the YAML/Python path (AD-3 vs Dates convention) — only JSON-mode strict accepts strings. *Fix:* type timestamps as `str` with an RFC 3339 `AfterValidator`, or load traces with `model_validate_json` and keep suites free of datetime fields; record the choice in AD-3.
- **[low]** Matrix omits 3.15; 3.12/3.13 are security-only (Stack, AD-17, OQ-13). *Fix:* add 3.15 (allow-failure until typer, rich, import-linter classify it); revisit the floor in OQ-13.
- **[low]** `from __future__ import annotations` is slated for removal and redundant on 3.14+ (Typing convention). *Fix:* keep for the 3.12 floor; drop when the floor reaches 3.14.
- **[low]** ADR-013 says "atomic writes"; CPython guarantees atomicity only on POSIX. *Fix:* "atomic on POSIX, best-effort on Windows".
- **[low]** Runtime-built discriminated union from `REGISTRY` (AD-8) is undocumented. *Fix:* build `Annotated[Union[tuple(REGISTRY.values())], Field(discriminator="type")]` once at import; cover in the schema-drift test.
- **[low]** GitHub's workflow lockfile now supersedes SHA pinning where adopted (AD-17). *Fix:* none; note as an alternative.
