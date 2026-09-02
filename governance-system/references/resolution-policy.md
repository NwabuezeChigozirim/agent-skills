# Worktree Resolution Policy

## Canonical state

Each governance run declares one canonical worktree, branch and HEAD. Other worktrees
may hold unfinished variants, but they are never authoritative until the owner resolves
them into the canonical worktree.

## Inventory

For every local worktree record:

- absolute path, branch and HEAD;
- staged, unstaged and untracked paths;
- assigned agent and scope when known;
- base revision and divergence from canonical HEAD;
- recorded test evidence;
- snapshot identifier.

## Resolution records

Create one stable R-ID for every dirty non-canonical worktree and for every worktree
whose branch is ahead of canonical (committed but unmerged work counts as a variant),
plus records for each overlapping path set. Record all variants, overlap reason,
recommendation, owner choice and status. Non-overlapping unfinished work still requires
an explicit integrate, defer, obsolete, or return-to-agent disposition before closure.

`adopt`, `combine` and `return-to-agent` describe work still to be done; the record
stays `pending` and blocks closure until a later scan finds the variant gone. Records
whose variant disappears are carried forward with an audit note, never deleted.

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
- a dirty variant lacks a recoverable snapshot;
- canonical HEAD changed after validation;
- required tests or governance validation failed.

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
