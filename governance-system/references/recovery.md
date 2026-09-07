# Local recovery contract

Use this reference when reconciling variants, responding to incomplete recovery, or
recovering a captured version. No command in this release restores, integrates,
deletes, stashes or resets work automatically.

## What a version contains

Snapshot format 2 retains HEAD, dirty-path raw file states and modes, affected index
entries (including merge stages), and the distinct staged blobs. Its fingerprint
includes the full index and raw dirty content, so changing only the staged version
still changes snapshot identity even when the working file equals HEAD. Timestamps do
not define identity. Ignored files and Git-hidden changes (for example assume-unchanged
or skip-worktree paths) are outside the scanner's scope; use a separate backup for them.

Files live under `<git-common-dir>/governance/snapshots/`:

- `v2-<path-hash>-<capture-hash>.json`: immutable manifest, payload and metadata checksums, capture budget,
  coverage gaps, working file metadata, index entries and retained base ref.
- `.patch`: optional HEAD-to-working convenience diff. **Not** sufficient to restore
  staging. An omitted diff is an empty file with an explicit `patch_status`.
- `-worktree.tar.gz`: affected tracked working bytes/modes and symbolic links.
- `-untracked.tar.gz`: non-ignored untracked working bytes/modes and symbolic links.
- `-index.tar.gz`: staged blobs by object ID; the manifest maps paths, modes and stages.

Raw archives plus the base commit are the recovery authority, not the convenience
diff. Deletions are explicit in the manifest. Symlink targets are recorded as link
text; the scanner never follows them to copy external files. Capture covers regular
files, POSIX permission bits and links, not ACLs, extended attributes, ownership,
timestamps, nested submodule repositories or an entire machine image.

The shared raw-data budget is 200 MiB across working/untracked bytes and staged blobs.
Archive framing and the separately bounded convenience diff are additional storage.
Recognized sensitive paths are excluded from raw archives and staged-blob copying;
the diff is omitted for any incomplete capture. Paths, object IDs and content digests
are metadata, not redacted secrets: keep local state private. Arbitrarily named secret
files cannot be identified reliably by filename rules; this is not a secret scanner.

## Immutability and availability

New snapshots use private staging directories and mode-0600 files, publish payloads
create-only, then publish the manifest. An interrupted attempt may leave orphan
payloads; a retry reuses only byte-identical payloads. It never overwrites conflicting
data. An unchanged rescan verifies and reuses a manifest without rewriting it.

Capture checks raw bytes against the inventory and rescans afterward. A detected
concurrent change aborts publication. Closure checks again after validation. The runtime
lock serializes governance operations, not editors or Git commands: stop concurrent
writers for a stable capture/closure boundary. This is not a filesystem transaction
against arbitrary external processes or protection against deliberate state tampering.

Base commits and reviewed committed variants are retained under create-only
`refs/governance/snapshots/<commit-id>`. No user branch moves, commits or pushes are
performed. Git's ref retention protects these objects from ordinary pruning; see
[Git garbage collection](https://git-scm.com/docs/git-gc) and
[create-only ref updates](https://git-scm.com/docs/git-update-ref).
These refs and snapshot files have no automatic pruning policy. Do not delete them
while any recovery history depends on them. A Git mirror push includes non-branch refs;
review that independently before publishing a mirror.

This is **local same-store recovery**, not off-machine backup. Copy both the recovery
payloads and their base Git objects into a separately managed backup if loss of the Git
store must be survivable. Ordinary clones do not copy the snapshot directory. Archived
absolute paths are origin metadata; locate payloads by their names after a manual move.

## Incomplete or unavailable recovery

Sensitive exclusions, size limits and unsupported/unreadable data create explicit
coverage gaps and an `incomplete-recovery` R-ID. Deferring or obsoleting the associated
variant does not waive that obligation. Older head-only snapshots remain untouched;
their missing staged-state/coverage evidence also requires alternative recovery.

For a terminal coverage disposition, the owner supplies an existing, nonempty regular
backup file outside all registered worktrees:

```bash
governancectl --repo /path/to/repository resolve --id R-004 --choice keep-canonical \
  --note "Owner confirms the encrypted backup covers the excluded files in this snapshot" \
  --recovery-ref /separate-backups/project-version.enc
```

The runtime records and rechecks the resolved file location, byte count and SHA-256;
it rejects symlink backup files. It does **not** validate an encrypted archive's
contents or infer that an arbitrary file is a complete backup. Coverage is explicitly
owner-attested for the named snapshot; never provide the flag speculatively. A changed
or missing backup invalidates the coverage evidence. Restore it or record a fresh
owner-attested reference, retaining decision history.

Missing worktrees are `dirty: null`, not clean. Unreadable/unsupported live paths also
prevent a reliable current-version fingerprint and create an unwaivable
`unavailable-worktree` gate. An alternative backup covers historical gaps; it cannot
prove what unknown live content is now. Restore access/support and rescan before
closure. Even if the owner removes a variant, its unresolved historical recovery
obligation persists. Raising the capture budget or recapturing complete content does
not automatically waive earlier incomplete versions.

## Manual recovery checklist

Recover into a separate disposable checkout first, never over the canonical worktree.

1. Verify payload checksums and the retained base commit. Check coverage gaps and any
   owner-managed alternative backup; a net patch alone is not enough.
2. Check out the recorded base HEAD in the recovery checkout.
3. Import the archived index blobs using `git hash-object -w --stdin`; verify returned
   object IDs. Clear affected index entries and restore saved modes, object IDs and
   merge stages using `git update-index --index-info` (NUL-safe input for unusual paths).
4. Remove paths recorded as deleted; restore affected tracked and untracked files,
   permissions and symbolic links from their raw archives. Validate archive paths and
   link parents before extraction; never blindly extract over existing symlinks.
5. Compare staged entries, raw working bytes, modes and status with the manifest, then
   have the owner choose integration or continued recovery. Automated fixture tests
   exercise this round trip; there is deliberately no automatic restore command yet.
