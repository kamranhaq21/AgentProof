# 0000. Distribution name

- Status: open (stub for OQ-1; no decision has been made)
- Opened: 2026-10-22
- Owner: maintainer

## Context

The import name is `agentproof` and the console script is `agentproof`; both are
settled by the architecture spine (AD-15, AD-20). The PyPI project `agentproof` is
already taken by another agent-testing package, so the distribution name declared in
`packages/python/pyproject.toml` (`name = "agentproof"`) is provisional. It builds and
installs from a wheel path today, but it cannot be published under that name.

Until this record carries a decision, nothing in the repository publishes to an index
or writes a public install-by-name command; installs come from the built wheel path, as
CI's `smoke` job does (AGENTS.md policy, refreshed 2026-10-23). Publishing is gated in
epic 9.

## Candidates

- `agent-proof` (leading candidate; the import name stays `agentproof`)
- another prefix or suffix on `agentproof`, to be checked against PyPI before adoption

## Decision

Not yet decided.

## Consequences once decided

- Change `name` in `packages/python/pyproject.toml`.
- Change the lookup key in `packages/python/src/agentproof/__init__.py`, which reads
  the version through `importlib.metadata.version(<distribution name>)`.
- Write the README install instructions and the release workflow (epic 9) against the
  chosen name.
