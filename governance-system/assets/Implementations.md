# <Project Name> Implementation and Handoff Log

This append-only log records shipped reality, operational gotchas and handoff context.
It does not own planned scope, engineering rules, decisions, or wave status.

## Current operational context

**As of:** <YYYY-MM-DD HH:MM>

- Shipped/deployed: <verified reality>
- In flight: <canonical worktree and active review unit>
- Frozen contracts: <names and sign-off waves>
- Required environment keys: <names only; values come from the approved secret manager>
- Local setup constraints: <ports, extensions, fixtures or platform requirements>
- Canonical wave status: [docs/waves/README.md](docs/waves/README.md)

## Entry format

```text
## YYYY-MM-DD HH:MM — <title>
tag: [FEATURE|FIX|CHORE|DECISION|DEPLOY|HANDOFF]
area: <module or path>
summary: <what changed>
reason: <why>
change_ref: <review or commit reference, optional>
tests: <commands and result>
notes: <gotchas or unfinished work, optional>
```

## Log

## <YYYY-MM-DD HH:MM> — Governance Suite v2 installed
tag: CHORE
area: governance
summary: Installed canonical governance artifacts, worktree resolution and opt-in hooks.
reason: Preserve one owner-approved project state across agent worktrees.
tests: governancectl validate
notes: Wave 1 remains gated until owner approval is recorded in docs/waves/README.md.
