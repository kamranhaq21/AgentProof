# 0021. License

- Status: open (stub for OQ-2; no decision has been made)
- Opened: 2026-10-23
- Owner: maintainer

## Context

The repository has no `LICENSE` file and `packages/python/pyproject.toml` declares no
`license` field or license classifier. The architecture's open-question table (OQ-2)
holds the decision until the contributor policy and a license review of the four
runtime dependencies (`pydantic`, `typer`, `rich`, `pyyaml`, all permissively licensed)
are done. Until this record carries a decision, nothing in the repository states a
license, and the package cannot be published (publishing is gated in epic 9).

## Candidates

- Apache-2.0 (leading candidate: explicit patent grant, common for developer tooling)
- MIT (simpler text; no patent grant)

## Decision

Not yet decided.

## Consequences once decided

- Add the `LICENSE` file at the repository root with the full license text.
- Set `license` in `packages/python/pyproject.toml` (SPDX expression) and add the
  matching `License ::` classifier so the wheel metadata carries it.
- Add a contribution-terms paragraph to `CONTRIBUTING.md` stating that contributions
  are made under the project license.
- Repoint epic 9 story 4, which currently names this record `0001-license.md`, to
  `0021-license.md` (numbering decision delegated by the maintainer on 2026-10-22).
