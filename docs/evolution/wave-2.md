# Wave 2 — Content-bound recovery and dispositions

Start authority: the owner's “Proceed” in response to the Wave 2 approval request.
At the Wave 2 handoff, owner sign-off had not yet been recorded and Wave 3 was gated.
Subsequent progression authority: the owner's “Proceed” authorized Wave 3; see its
[implementation record](wave-3.md). Results below remain the historical Wave 2 record.

## Contract

Distinct reviewed content must remain recoverable as distinct immutable versions.
Dispositions bind to the relevant content; unchanged scans retain decisions and
changed variants require new review. Missing worktrees and incomplete capture cannot
be reported as clean or backed up.

Preserve all prior snapshots, IDs, owner choices, the three-package layout, read-only
diagnostics, and the existing prohibition on automatically applying or deleting work.
Policy 2 remains unreleased; these recovery safety fixes also apply to legacy policy.

## Implementation

- Raw-content/index fingerprints distinguish versions at the same HEAD, including
  staging-only and mode changes. Unavailable worktrees are unknown (`dirty: null`),
  not clean. Unreadable/unsupported live paths cannot establish a current version.
- Format-2 snapshots preserve tracked working state, non-ignored untracked state and
  staged blobs separately, including modes, links, deletions, renames and merge stages.
  A net patch remains an optional convenience, never the staged-state authority.
- Private temporary staging, create-only publication and a manifest-last boundary
  prevent overwrites. Unchanged captures reuse verified bytes. Payload and metadata
  checksums detect corruption; capture and closure rescans reject detected races.
- Create-only `refs/governance/snapshots/<commit>` retain base commits and reviewed
  committed variants. No user branches move and no commits or pushes are performed.
- New relevant content creates a new R-ID. Unchanged relevant content preserves the
  existing choice, note, timestamps and reviewed snapshots. Supersession links retain
  earlier owner decisions rather than marking changed/committed work integrated.
  Unrelated dirty content does not reopen shared-path reviews.
- `resolve` rejects stale normal reviews, records decision history and leaves repeated
  identical choices unchanged. `adopt`, `combine` and `return-to-agent` remain pending.
- Incomplete recovery is an independent obligation. `--recovery-ref` identifies an
  owner-attested, nonempty regular backup file outside registered worktrees. Its hash
  and continued availability are checked; its semantic coverage is not inferred.
  Historical uncovered versions remain obligations even when work disappears.
- Unavailable/unverifiable live content cannot be waived. Legacy snapshots and choices
  are preserved, but absent staged-state/coverage proof is not silently certified.
  Explicit reconciliation creates the necessary fresh review/recovery records.
- Existing read-only commands remain read-only. Reconciliation reports incomplete
  captures and recovery errors honestly. Session-end snapshot warnings do not claim
  complete recovery when gaps remain; broader adapter enforcement stays in Wave 6.

The skill-creator guidance kept the agent entrypoint focused on the version-review
invariant and routed conditional details to
[the recovery contract](../../governance-system/references/recovery.md). The schema,
operator and resolution references describe the same implemented boundary.

## Verification

Verified locally on 2026-09-06, Linux, Python 3.12.3 and Node 22.22.1. The final
`scripts/check.py` run exited 0:

| Check | Result |
|---|---|
| Governance runtime and suite tests | 41 passed |
| Specification tests | 29 passed |
| Planning tests | 36 passed |
| Wave 1 compatibility/upgrade tests | 22 passed |
| Wave 2 recovery tests | 26 passed |
| Original gap 08 regression | Passed; expected-failure allowance removed |
| Remaining review regressions | 11 expected failures; no unexpected failures/successes |
| Renderer, including PDF/page-image verification | 4 passed |
| Suite structure and all three skill entrypoints | Passed |
| Supplemental generated-artifact JSON Schema checks | Passed, including unavailable/retired states |
| `git diff --check` | Passed |

Total: **155 passing Python tests and 4 passing renderer tests**, with 11 known
later-wave defects explicitly retained as expected failures, not passed checks.
Renderer dependencies were reused through `NODE_PATH` from the existing isolated
review installation; no dependencies were installed into the source checkout.
The hosted Linux/macOS CI matrix and independent agent-behavior evaluations were not
run. These results establish local deterministic behavior, not cross-host or whole-SDLC
acceptance. The supplemental JSON Schema validation used the host's validator; the
runtime and Python regression suite retain their standard-library-only dependency boundary.

Source-content manifest SHA-256 (excluding this self-referential record):
`8bbd05904f507794893d5c89f531092118387598649b662f8b4c41a726c2d325`.
From the repository root:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':(exclude)docs/evolution/wave-2.md' | sort -z | xargs -0 sha256sum | sha256sum
```

The recovery tests exercise same-HEAD edits, unchanged rescans, staged/working binary
differences, renames, deletions, modes, symlinks, unmerged index stages, committed
variants, missing worktrees, limits/exclusions/unreadable data, alternative backups,
capture/closure races, interrupted publication, corruption, legacy history and
read-only diagnostics. A real round trip restores a disposable checkout and compares
its full staged index and raw working fingerprint with the captured source.

The previous `.env` runtime fixture now supplies an explicit backup for its coverage
R-ID instead of accepting a generic owner note. Only gap 08 lost its expected-failure
allowance. No assertions for the other eleven known defects were weakened.

## Boundaries and evolution risks

Recovery is local to the shared Git store, not an off-machine backup. Recognized
secrets are excluded; arbitrary filenames are not a reliable secret classifier.
Ignored/Git-hidden files, ACLs, extended attributes, nested repositories and whole-machine
recovery are outside this capture contract. Unknown live content must become readable
and supported before closure; an owner's historical backup cannot identify it.

The runtime lock does not lock editors or external Git operations. Capture/closure
detect changes between checks, but cannot provide a filesystem-wide transaction;
quiesce writers at those boundaries. Checksums detect corruption, not an attacker who
can rewrite both evidence and checksums. There is no automatic restore or pruning.
Historical checksumming and retained archives may become costly on long-lived large
projects; measure representative histories before introducing caching or retention.

Conservative legacy/incomplete recovery can require additional owner review. This is
intentional: absence of version/coverage proof must not become manufactured assurance.
Later complete recapture does not automatically waive earlier incomplete versions.

Regression signals include changed content retaining approval, unchanged content
reopening reviews, lost staged bytes/modes, rewritten historical snapshots/choices,
unknown content appearing clean, false backup claims, diagnostic writes, and excessive
review or storage cost without a corresponding recovery benefit. Use the fixtures
and real project observations to evaluate refinements, not structural tidiness alone.

## Adoption and next gate

All mutation commands ran only in disposable fixtures. The source repository was not
governance-initialized, upgraded or given hooks/recovery refs. No commit, push or release
was performed. Existing Wave 1 edits remain in the worktree.

At this historical handoff, owner Wave 2 review/sign-off was outstanding and Wave 3
(specification/planning graph enforcement) required a new approval. The subsequent
Wave 3 start authority is recorded above; Waves 4–6 and policy-2 activation remain gated.
