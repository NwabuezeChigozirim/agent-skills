# Wave 1 — Regression baseline and explicit project upgrades

Baseline: `2f223ce65792f94fc4a5c47b04e733b7740e0c66`.
Implementation authority: the owner's request, “Implement the proposed plan.”
At the Wave 1 handoff, owner sign-off had not yet been recorded and Wave 2 was gated.
Subsequent progression authority: the owner's “Proceed” authorized Wave 2; see its
[implementation record](wave-2.md). The verification below remains the historical
Wave 1 result, not a claim about the later working tree.

## Outcome and preserved behavior

Inspection is read-only even for legacy config and absent local state. Metadata
migration is explicit and recoverable. Policy selection cannot silently opt an
existing project into incomplete enforcement or downgrade its declared authority.
The three skill responsibilities, legacy specification/planning rules, existing
approval gates, and snapshot/reconciliation semantics remain unchanged.

The one intentionally replaced baseline assertion expected `doctor` to migrate
schema 2. It now proves no migration occurs until explicit application. Fixture paths
are normalized to match Git's physical paths on Linux and macOS.

## Implementation

- `audit` inspects fresh worktree inventory and existing governed artifacts without
  discovery, reconciliation, state creation or acceptance claims.
- Config reading and canonical lookup no longer initialize or migrate state. Git
  reads disable optional index locking; validator imports do not write bytecode.
- `upgrade --dry-run|--apply` exposes the adoption boundary. An explicit
  `--policy legacy` permits schema-2 metadata migration or adding a policy-1 marker.
  Exact pre-migration bytes are backed up privately. Reapplication is a no-write
  no-op; changed metadata, existing recovery material and symlink targets are guarded.
- A shared read-only selector handles config authority, standalone document markers,
  incompatible markers and non-downgradable CLI previews.
- Policy 2 is reserved but unreleased. New config/templates explicitly remain on
  policy 1, and current-policy selection reports a blocking error. This is the
  planned intermediate-release guard, not completed current-policy enforcement.
- CI and `scripts/check.py` cover package tests, suite structure, new acceptance
  tests, the 12 reproduced gaps, and the existing renderer checks.
- Instructions route audit away from the mutating workflow and distinguish storage
  migration from engineering approval. Detailed compatibility guidance has one owner
  in `governance-system/references/policy-compatibility.md`.

## Verification

Verified on 2026-09-05, Linux, Python 3.12.3 and Node 22.22.1:

| Check | Result |
|---|---|
| Governance and suite tests | 41 passed |
| Specification tests | 29 passed |
| Planning tests | 36 passed |
| Wave 1 acceptance tests | 22 passed |
| Known later-wave regressions | 12 expected failures; no unexpected failures/successes |
| Renderer, including PDF/page-image verification | 4 passed |
| Suite structure and all three skill entrypoint validators | Passed |
| Workflow YAML/trigger/permission checks; `git diff --check` | Passed |

The complete `scripts/check.py` invocation exited 0: 128 passing Python tests plus
4 passing renderer tests. Renderer dependencies were reused from the previous
isolated review installation through `NODE_PATH`; its package lock was compared
byte-for-byte with the source lock. No dependencies were installed into this checkout.

Source-content manifest SHA-256 (excluding this self-referential record):
`7ded4f75a7e56efafcec96722416e86c5e97cb2f684db931dc5361efbdb5a862`.
Reproduce from the repository root with:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':(exclude)docs/evolution/wave-1.md' | sort -z | xargs -0 sha256sum | sha256sum
```

The original behavioral evaluation definitions have not been executed as agent
comparisons; that remains part of Wave 6. The hosted Linux/macOS CI matrix has been
configured, not run remotely. These local results do not claim cross-host validation.

The filesystem assertions compare bytes, modes, directory entries and mtimes,
including `.git` and sibling worktrees. Access times are excluded because reading can
update them. Cases cover uninitialized projects, schemas 2/3, staged/unstaged changes,
clones, corrupt state, current-policy refusal, exact backups, idempotency, symlink
targets, preserved restrictive permissions and concurrent metadata changes. An
isolated copy verifies that the three sibling packages work without suite-root
runtime helpers.

The 12 review regressions remain explicitly expected failures, owned by Waves 2–6.
They are known defects, not passed checks. Their assertions describe the intended
invariants; remove each allowance when its owning implementation satisfies them.

## Adoption and remaining work

No live project was upgraded, no hooks were installed, and no release, commit or push
was performed. Only disposable test repositories exercised mutation commands.

After owner review and approval, Wave 2 replaces mutable snapshot/disposition identity
with immutable content-bound identity. Do not enable policy 2 until the remaining
enforcement, iteration, adapter and migration gates are implemented and verified.
