# Architecture

AgentProof v0.1 is a functional core inside an imperative shell: everything that
computes is a pure function over frozen models, and the `adapters`, `runner`, `io`, and
`cli` packages do all of the reading, writing, timing, and process handling. The
dependency direction is enforced by `.importlinter` and a ruff banned-API list, and
`uv run check` in `packages/python` is the single gate that proves it.

## Where the architecture lives

- **Architecture spine** (the authority for every design rule, AD-1 to AD-20, the
  module graph, the stack, and the structural seed):
  [`_bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md`](../_bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md)
- **Decision records** (one file per decision, with context, alternatives, and
  consequences): [`docs/decisions/`](decisions/README.md). ADR-001 to ADR-020 implement
  AD-1 to AD-20 of the spine one to one; the planning-time log they were copied from is
  [`adr-log.md`](../_bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md).
- **Product brief and constraints**: [`PROJECT_SPEC.md`](../PROJECT_SPEC.md).
- **Agent and contributor policy**: [`AGENTS.md`](../AGENTS.md) and
  [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Reading order for a change

1. The spine's AD that binds the module you are touching (the "Binds" line of each AD).
2. The matching ADR under `docs/decisions/` for the reasoning and the rejected
   alternatives.
3. `PROJECT_SPEC.md` sections 4, 6, and 11 before touching trace, report, or CLI code.
