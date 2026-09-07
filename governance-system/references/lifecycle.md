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
Phases are navigation state, not acceptance evidence or a one-way execution gate.
For explicit stage-contract opt-in, freeze the approved scope, inputs and checks before
work; keep the phase independent of contract satisfaction. See
[stage-contracts.md](stage-contracts.md). Changed inputs cannot be repaired by changing
the phase: owner-reviewed cancellation/replacement preserves the earlier record.

### Update

Use when governance exists but its schema or generated-version is older. Run
`upgrade --dry-run` first. Apply metadata changes only through an explicitly requested
`upgrade --apply`; version age is not authorization. Read
[policy-compatibility.md](policy-compatibility.md) for the release gate and the separate
metadata-only legacy upgrade. Preserve project prose and repair artifact findings
separately; do not infer new authority from a migration.

### Repair

Use when validation fails or an owned artifact is missing. Repair from canonical
sources; never regenerate unrelated project prose. A repair does not authorize a wave.

### Audit

Run `audit` for fresh inventory and read-only artifact/runtime validation. Report drift
and stored resolution records. Do not run `discover` or `reconcile`: they write state.
Do not install hooks, create snapshots or edit repository files.

### Handoff

Rescan all worktrees, resolve blocking variants, verify the canonical worktree, update
operational gotchas, validate, snapshot unfinished work, and close the stage only after
owner approval.
Contracted runs also require fresh successful check receipts, resolved blocking intent
and a bound sign-off reference. Closing does not authorize the next wave. Cancellation
does not count as closure and cannot restore legacy acceptance within an opted-in run.

## Idempotency

Every mode starts by reading current state. Re-running a successful command must not
duplicate hook entries, decision IDs, wave rows, or handoff entries. If the current
state already satisfies the requested transition, report that no change is required.
