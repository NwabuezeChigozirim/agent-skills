# <Project Name>

<Verified description of the product and its users.>

## Start here

- Agents: [AGENTS.md](AGENTS.md)
- Engineering rules: [design.md](design.md)
- Ratified intent: [DECISIONS.md](DECISIONS.md)
- Concept analysis, when required: [docs/<name>-CON.md](docs/<name>-CON.md)
- Behaviour: [docs/<name>-FSD.md](docs/<name>-FSD.md)
- Technical design: [docs/<name>-TSD.md](docs/<name>-TSD.md)
- Wave status: [docs/waves/README.md](docs/waves/README.md)
- Shipped reality and gotchas: [Implementations.md](Implementations.md)

Files under `docs/exports/` are derived presentation copies. Canonical Markdown wins
when an export disagrees.

## Prerequisites

<Verified runtime, package manager, datastore and local tools.>

## Safe quickstart

List commands proven from repository scripts or CI. Classify stateful commands and do
not execute migrations, deployments or shared-service restarts merely to verify docs.

```bash
<install-command>
<test-command>
<lint-command>
<build-command>
```

Secrets are injected through the approved secret manager. Commit only placeholder key
names in `.env.example`; never put secret values in repository environment files.
