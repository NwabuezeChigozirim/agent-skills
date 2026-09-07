# Runtime Contract

Invoke `python3 scripts/governancectl --repo PATH COMMAND`.

## Commands

- `doctor` — verify Git, Python, repository identity, configuration and canonical worktree.
- `status` — print non-secret run, canonical-state and resolution summary.
- `audit` — inspect fresh inventory and existing governed artifacts without writes;
  reports validity but does not establish acceptance or reconcile variants.
- `upgrade --dry-run|--apply [--policy legacy|current]` — preview or explicitly apply
  owned metadata migration. Current-policy adoption is gated until its release.
- `discover` — refresh worktree inventory and Discovery Packet (merges recorded notes).
- `note --kind KIND --text TEXT [--evidence REF] [--provenance P]` — append a Discovery
  Packet finding. Kinds: `observation`, `hypothesis`, `needs-owner`, `blocking`.
  Provenance `code|test|ci|git` requires `--evidence`.
- `phase NAME [--next-action TEXT]` — record the active lifecycle activity, not acceptance.
- `set-canonical --path WORKTREE` — declare which local worktree is authoritative.
- `reconcile` — capture immutable content versions and reconcile version-bound records;
  reports newly created/reused snapshots, incomplete captures and unavailable trees.
- `resolve --id R-### --choice CHOICE --note TEXT [--recovery-ref PATH]` — record the
  owner's disposition of the current reviewed version. A terminal incomplete-recovery
  choice requires an owner-attested backup file outside registered worktrees.
- `validate [--policy auto|legacy|current]` — validate runtime state, generated governance artifacts, and (when present)
  the specification chain and wave plan through their sibling validators.
- `freeze-stage --contract PATH --owner-approved --approval-ref PATH` — explicitly opt
  the active run into an immutable acceptance contract; does not run its checks.
- `run-check --id CHK-###` — execute that frozen command and retain content-bound evidence.
- `check-stage [--policy auto|legacy|current]` — read-only stage readiness, never execution
  or full artifact/recovery acceptance. Current-policy preview remains nonzero.
- `stage-impact [--contract PATH] [--policy auto|legacy|current]` — read-only comparison
  of frozen/current context and proposed scope; potential dependency impact, not approval.
- `revise-stage --contract PATH --review PATH --owner-approved --approval-ref PATH
  --reason TEXT [--reopen]` — create a linked immutable successor after a current impact
  review. Explicit reopening creates a new active run and preserves prior closure.
- `resolve-note --id N-### --decision D-### --note TEXT --owner-approved` — preserve a
  blocking/needs-owner note while binding its resolution to a ratified decision row.
- `cancel-stage --owner-approved --approval-ref PATH --reason TEXT` — retain the cancelled
  contract and history; replacement is required before closure, not a legacy fallback.
- `resume` — return the active phase and next action.
- `close-stage --owner-approved [--approval-ref PATH]` — enforce closure gates and record
  completion. An approval reference is mandatory for explicitly contracted runs.
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
Place the global flag before the subcommand, for example `--repo PATH --json audit`.
For extra read-only Git probes outside the runtime, use `git --no-optional-locks ...`
to avoid index metadata refreshes from commands such as status.

`doctor`, `status`, `audit`, `validate`, `check-stage`, `stage-impact`, `resume` and upgrade previews are read-only,
including when local state is absent or config schema 2 is present. Audit validation
errors use exit 3; blocked upgrades use exit 4. Policy metadata is additive to existing
JSON fields. Read [policy-compatibility.md](policy-compatibility.md) for exact selection
and upgrade behavior; current policy 2 is not yet released.
Stage contract/owner gates use exit 4; failed, stale or timed-out `run-check` results use
exit 3. See [stage-contracts.md](stage-contracts.md) before authorizing command execution.
Read [controlled-iteration.md](controlled-iteration.md) before revising/reopening a
contract. Impact `analysis_valid` means a report was built, never acceptance or complete
graph coverage; uncertainty stays explicit. Stale/missing owner reviews gate revision.

## State

Committed `.governance/config.json` (schema 3) activates governance and identifies the
repository by its root commit(s), so it is valid in every clone. It holds no absolute
paths.

Machine-local state lives at `<git-common-dir>/governance/` and is shared by all local
worktrees of the same repository:

- `canonical.json` — the authoritative worktree and branch on this machine;
- `registry.json`, `discovery.json`, `discovery-notes.json`, `run-state.json`,
  `resolutions.json`, `snapshots/`, `stages/` (frozen contracts and retained check/closure
  evidence), `upgrades/` (exact pre-migration metadata backups).

Mutable state uses atomic temporary-file replacement while holding the runtime lock
(`fcntl`; Linux and macOS only). Recovery payloads instead use create-only publication,
with the manifest published last. Base commits are pinned under create-only
`refs/governance/snapshots/` in the shared Git store. These are not branches or remote
backups; see [recovery.md](recovery.md) for exact scope, retention and restoration.

## Resolution states

- `needs-owner` — awaiting a choice.
- `pending` — `adopt`, `combine` or `return-to-agent` chosen; the variant still exists.
  Blocks closure until a later scan observes it gone without a replacement. A changed
  or committed variant creates a new review and retires, rather than approves, the old one.
- `resolved`, `deferred`, `obsolete` — terminal.

Records are carried forward, never deleted. Retirement is separate from the recorded
owner disposition. Retired ordinary reviews stop gating, but unresolved historical
`incomplete-recovery` obligations still gate. Alternative backup hashes and snapshot
payloads remain checked by read-only validation. See the resolution policy for scope
fingerprints, legacy reviews and unavailable worktrees.

## Stop hook policy

The `stop` event is a turn boundary, not stage closure. It refreshes a stale inventory
if the canonical HEAD moved, then reports validation errors and unresolved R-IDs as a
single non-blocking warning. It never denies. Only `close-stage` gates. When the
platform indicates a follow-up already triggered (`stop_hook_active`), the hook is
silent.
