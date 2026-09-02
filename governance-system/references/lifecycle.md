# Lifecycle

## Modes

### Install

Use when `.governance/config.json` is absent. Run `doctor`, inventory worktrees, select
the canonical worktree, create the Discovery Packet, generate artifacts, install hooks
only after opt-in, validate, then leave Wave 1 gated.

### Resume

Use when `<git-common-dir>/governance/run-state.json` records an active run. Confirm the
repository identity and canonical HEAD, rescan worktrees, then continue from
`next_action`. Do not restart discovery unless evidence is stale or missing.

## Phases

`run-state.json` tracks `discovery → resolution → intent → specification → planning →
operations → validation → handoff`. `discover` and `reconcile` manage the first three;
record each later transition explicitly:

```bash
governancectl --repo . phase specification --next-action "Author FSD through spec-chain"
```

Hook-driven rediscovery and reconciliation never rewind a recorded phase.

### Update

Use when governance exists but its schema or generated-version is older. Snapshot
governance files, migrate only owned structures, preserve project-specific content,
validate, and record the migration in `Implementations.md`.

### Repair

Use when validation fails or an owned artifact is missing. Repair from canonical
sources; never regenerate unrelated project prose. A repair does not authorize a wave.

### Audit

Run discovery, inventory, and validation read-only. Report drift and resolution records
without installing hooks or editing repository files.

### Handoff

Rescan all worktrees, resolve blocking variants, verify the canonical worktree, update
operational gotchas, validate, snapshot unfinished work, and close the stage only after
owner approval.

## Idempotency

Every mode starts by reading current state. Re-running a successful command must not
duplicate hook entries, decision IDs, wave rows, or handoff entries. If the current
state already satisfies the requested transition, report that no change is required.
