# Security Policy

## Supported versions

AgentProof is pre-1.0. Only the latest minor release on the `0.x` line receives security
fixes.

| Version | Supported |
| --- | --- |
| latest `0.x` minor | yes |
| earlier `0.x` minors | no |

## Reporting a vulnerability

Report vulnerabilities privately; do not open a public issue.

- Reporting channel: `<security contact to be filled by the maintainer>`
- First response within: `<response window to be filled by the maintainer>`

Include the AgentProof version, the operating system, a minimal Suite or Trace that
reproduces the problem, and what you expected instead. Please redact real secrets from
anything you send; redaction markers (`[REDACTED]`) in a trace are fine.

## What AgentProof does and does not do

AgentProof evaluates recorded traces locally. By design (architecture decisions AD-9,
AD-10, AD-18, and AD-19), replay never calls an agent, a tool, or the network and never
executes anything found in a trace, scenario, or report; those files are data. Secrets
are redacted at ingress and never logged, including in verbose output. These are design
commitments backed by tests as each part of v0.1 lands; until a release ships, treat
them as commitments, not as shipped behavior.

The security limits and threat model are documented in `docs/security.md` (written in
epic 9; until then the policy statements in `AGENTS.md` apply).
