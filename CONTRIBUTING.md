# Contributing to AgentProof

AgentProof is a local-first, framework-neutral testing and regression framework for
tool-using AI agents. The Python package lives in `packages/python`; the architecture
that every change must respect is summarized in `docs/architecture.md`.

## Setup

Everything runs through [uv](https://docs.astral.sh/uv/). From the repository root:

```sh
cd packages/python
uv sync
```

`uv sync` creates `.venv/` with the package, the `dev` dependency group, and the
`agentproof-devtools` workspace member that provides the check command. Never run a bare
`python` or `pytest`; `uv run` selects the interpreter from `requires-python`.

## The one check

```sh
cd packages/python
uv run check
```

This is the whole quality gate and the only one. It runs, in order, `ruff check` (plus
the AST purity checker for the core packages), `ruff format --check`, `mypy --strict`,
`lint-imports`, and `pytest`, and stops at the first failure. CI
(`.github/workflows/ci.yml`) calls the same entry point and nothing else for its check
stage, on Linux and Windows across Python 3.12 to 3.15, so a change that passes
`uv run check` locally is a change CI accepts.

Optional: `uvx pre-commit install` installs the ruff hooks from `.pre-commit-config.yaml`
as a fast pre-commit subset of the gate. They never replace `uv run check`.

## Branches and pull requests

The rules come from `PROJECT_SPEC.md` section 13.2:

- `main` stays releasable at all times. It is protected: changes land through a pull
  request that merges only when the CI workflow's eight `check` jobs (two runners by
  four Python versions) are green. The rule requires no approvals and is not enforced
  on administrators, so the repository administrator can bypass it in an emergency; for
  everyone else the CI check cannot be skipped.
- `backlog` is the integration branch. Story branches (`story/<n>-<slug>`) open their
  pull request against `backlog`; `backlog` lands on `main` through a pull request.
  (The protection details and the `backlog` convention come from the maintainer's
  2026-10-22 decisions recorded in the planning tickets, not from the spec.)
- Work on short-lived feature branches.
- Open a pull request even when working alone; the PR is the review history.
- Keep commits small and descriptive.
- Never commit secrets, local traces, virtual environments, build artifacts, or private
  datasets. `.gitignore` covers the usual suspects; `examples/**/traces/` is tracked on
  purpose because the documented quick start replays those traces.
- If a push to an open pull request's branch gets no CI run at all (not even a failing
  one), check that PR's merge state (`gh pr view <n> --json mergeable,mergeStateStatus`).
  A PR sitting at `CONFLICTING` or `UNKNOWN` against the current base can silently stop
  receiving `pull_request`-triggered runs; merging the base branch into the PR's branch
  and pushing again resolves both the merge state and the missing runs. A brand-new,
  unrelated PR still dispatches normally in this situation, which is the fastest way to
  tell "stuck PR" apart from an account-wide Actions outage.

## Versioning policy

The package is pre-1.0 and follows semantic versioning on the `0.x` line (architecture
AD-15):

- A **minor** release (`0.x` to `0.x+1`) may change the public API, and every such change
  needs a changelog entry.
- A **patch** release (`0.x.y` to `0.x.y+1`) may not change the public API.
- The public API is exactly `agentproof.__all__`; subpackages are internal before 1.0.

Artifact schema versions are separate from the package version (AD-3): every serialized
Suite, Trace, and Report carries an integer `version`, and adding or renaming a field in a
serialized model is a new integer version, whatever the package version does.

## Dependency policy

The runtime dependencies are exactly four: `pydantic`, `typer`, `rich`, and `pyyaml`
(architecture AD-16). Anything else is a dev dependency or an optional extra. Adding a
runtime dependency requires a new decision record under `docs/decisions/` that states the
reason, the alternatives, and the install-footprint cost; a PR that adds one without an
ADR is not merged.

## Decision records

Architecture decisions live in `docs/decisions/`, one file per decision, numbered in
order. To add one:

1. Take the next number (`docs/decisions/README.md` lists them) and name the file
   `NNNN-<short-slug>.md`.
2. Start with a title line `# ADR-NNN (AD-N): <title>` when the record implements an
   architecture decision from the spine, or `# NNNN. <title>` for a stub or an open
   question, then a **Status** line (`Accepted`, `Proposed`, or `open`), then Context,
   Decision, Alternatives, and Consequences.
3. Add the row to the index table in `docs/decisions/README.md`.
4. Reference the record from the code or the PR that acts on it.

An Accepted decision is changed by a new record that supersedes it, never by rewriting
it in place. A Proposed record, or an open stub such as `0000` and `0021`, is completed in
place when the maintainer decides, with the date of the decision.

## Security

Report vulnerabilities privately through the channel named in `SECURITY.md`; do not open
a public issue for them. Contributions are expected to follow `CODE_OF_CONDUCT.md`.
