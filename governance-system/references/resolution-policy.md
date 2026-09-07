# Worktree Resolution Policy

## Canonical state

Each governance run declares one canonical worktree, branch and HEAD. Other worktrees
may hold unfinished variants, but they are never authoritative until the owner resolves
them into the canonical worktree.

## Inventory

For every local worktree record:

- absolute path, branch and HEAD;
- availability (missing/unreadable is unknown, never clean);
- staged, unstaged and non-ignored untracked paths, raw file states and Git index entries;
- base revision and divergence from canonical HEAD;
- content fingerprint and, after reconciliation, immutable snapshot identifiers.

Agent assignments and test evidence are engineering inputs, not fields inferred by
the current worktree scanner.

## Resolution records

Create one version-bound R-ID for every dirty non-canonical worktree and for every worktree
whose branch is ahead of canonical (committed but unmerged work counts as a variant),
plus records for each overlapping path set. Record all variants, overlap reason,
recommendation, owner choice and status. Non-overlapping unfinished work still requires
an explicit integrate, defer, obsolete, or return-to-agent disposition before closure.

`adopt`, `combine` and `return-to-agent` describe work still to be done; the record
stays `pending` and blocks closure until a later scan finds the variant gone without
a replacement. Committing the variant creates a committed-work review; it does not
prove integration. Superseded records retain their choices, notes and status, with
`retired_at`, `superseded_by` and `supersedes` linking the review history.

Unchanged relevant content retains its R-ID and disposition. Changed content creates
a new `needs-owner` record. An unfinished variant binds its complete working/index
fingerprint and canonical HEAD; committed variants bind both HEADs. Overlap review
binds only the overlapping paths and their index entries, plus both HEADs. Unrelated
dirty files must not reopen a shared-path review. `resolve` rescans before accepting a
choice and rejects stale or retired normal records. Returning to a retired version
does not automatically reinstate its old approval.

`unavailable-worktree` cannot be waived by a choice: restore access to readable,
supported current content and reconcile. `incomplete-recovery` requires an
owner-attested alternative backup before a terminal choice can be recorded. Historical
coverage obligations survive content changes and deletion. A newly complete capture
does not automatically prove coverage of an earlier incomplete or legacy snapshot.
Read [recovery.md](recovery.md) for the recovery boundary and backup procedure.

Allowed owner choices:

- keep canonical;
- adopt a named variant;
- combine selected changes manually;
- defer a variant with a reason and review point;
- mark a variant obsolete after a recoverable snapshot;
- return the conflict to an agent with an explicit reconciliation scope.

The runtime may create snapshots and recommendations. It must not merge, cherry-pick,
reset, stash, delete, or overwrite work automatically.

## Stage closure

A stage cannot close while:

- an R-ID is blocking or awaiting owner resolution;
- a worktree could not be rescanned;
- a snapshot payload or retained base commit is missing/changed;
- incomplete coverage lacks an available, unchanged owner-attested backup;
- canonical HEAD changed after validation;
- required tests or governance validation failed.

The current runtime enforces recovery, disposition and existing artifact-validation
gates. Captured test evidence and stage-specific acceptance contracts remain agent/owner
obligations until the separately gated completion-evidence wave implements them.

## Remote completion manifest

Remote agents must return:

- repository and worktree/branch identity;
- base commit and final commit, or a recoverable patch;
- changed and untracked paths;
- tests run and results;
- unfinished work and known conflicts;
- whether any secrets or generated local configuration were touched.

Local hooks cannot inspect uncommitted remote files. A remote result without a commit,
patch, or equivalent recoverable artifact remains unresolved.
