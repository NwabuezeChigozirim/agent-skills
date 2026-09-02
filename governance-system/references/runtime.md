# Runtime Contract

Invoke `python3 scripts/governancectl --repo PATH COMMAND`.

## Commands

- `doctor` — verify Git, Python, repository identity, configuration and canonical worktree.
- `status` — print non-secret run, canonical-state and resolution summary.
- `discover` — refresh worktree inventory and Discovery Packet (merges recorded notes).
- `note --kind KIND --text TEXT [--evidence REF] [--provenance P]` — append a Discovery
  Packet finding. Kinds: `observation`, `hypothesis`, `needs-owner`, `blocking`.
  Provenance `code|test|ci|git` requires `--evidence`.
- `phase NAME [--next-action TEXT]` — advance the active run to a lifecycle phase.
- `set-canonical --path WORKTREE` — declare which local worktree is authoritative.
- `reconcile` — create or refresh resolution records and snapshots.
- `resolve --id R-### --choice CHOICE --note TEXT` — record the owner's disposition.
- `validate` — validate runtime state, generated governance artifacts, and (when present)
  the specification chain and wave plan through their sibling validators.
- `resume` — return the active phase and next action.
- `close-stage --owner-approved` — enforce closure gates and record completion.
- `install-hooks` — merge opt-in Cursor and Claude Code project adapters.
- `hook EVENT` — normalized hook dispatcher.

## Exit codes

- `0` — success or disabled no-op.
- `2` — invalid invocation or malformed configuration.
- `3` — governance validation failed.
- `4` — unresolved owner gate or worktree conflict.
- `5` — unsafe operation refused.

Machine-readable commands support `--json`. Human output never includes file contents,
patches, environment values or secret values.

## State

Committed `.governance/config.json` (schema 3) activates governance and identifies the
repository by its root commit(s), so it is valid in every clone. It holds no absolute
paths.

Machine-local state lives at `<git-common-dir>/governance/` and is shared by all local
worktrees of the same repository:

- `canonical.json` — the authoritative worktree and branch on this machine;
- `registry.json`, `discovery.json`, `discovery-notes.json`, `run-state.json`,
  `resolutions.json`, `snapshots/`.

Writes use an atomic temporary file plus rename while holding the runtime lock
(`fcntl`; Linux and macOS only).

## Resolution states

- `needs-owner` — awaiting a choice.
- `pending` — `adopt`, `combine` or `return-to-agent` chosen; the variant still exists.
  Blocks closure until a later `reconcile` or `close-stage` observes it gone, which
  resolves it automatically with an audit note.
- `resolved`, `deferred`, `obsolete` — terminal.

Records whose variant disappears are carried forward, never deleted.

## Stop hook policy

The `stop` event is a turn boundary, not stage closure. It refreshes a stale inventory
if the canonical HEAD moved, then reports validation errors and unresolved R-IDs as a
single non-blocking warning. It never denies. Only `close-stage` gates. When the
platform indicates a follow-up already triggered (`stop_hook_active`), the hook is
silent.
