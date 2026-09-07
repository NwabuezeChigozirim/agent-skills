# Governance Suite v2 Operator Guide

`governancectl` is the single operational entry point. It does not merge, reset, stash,
delete or overwrite worktree changes.

## Audit or upgrade an existing project

```bash
governancectl --repo /path/to/repository audit
governancectl --repo /path/to/repository upgrade --dry-run
```

Inspection never initializes state or migrates old config. Policy 2 is not released,
so current-policy adoption remains gated. An explicitly requested metadata-only
upgrade can retain legacy policy with `upgrade --apply --policy legacy`. See
[policy compatibility](references/policy-compatibility.md) for backups, selection and
the difference between storage migration and engineering acceptance.

## Start or resume

```bash
governancectl --repo /path/to/repository doctor
governancectl --repo /path/to/repository status
governancectl --repo /path/to/repository discover
governancectl --repo /path/to/repository reconcile
```

`discover` initializes `.governance/config.json` when absent. The committed config
identifies the repository by its root commit, so it stays valid in every clone. The
canonical worktree is machine-local and defaults to the main worktree; change it with:

```bash
governancectl --repo /path/to/repository set-canonical --path /path/to/worktree
```

Set `project_slug` in `.governance/config.json` when the specification files are not
named after the repository directory (`docs/<project_slug>-FSD.md`).

`reconcile` exits with code 4 when owner resolution is required; this is an expected
gate. It records dirty worktrees and any worktree whose branch is ahead of canonical,
including clean ones whose work is already committed.

## Record discovery and progress

```bash
governancectl --repo /path/to/repository note --kind observation \
  --provenance code --evidence path/to/file --text "What the code shows"
governancectl --repo /path/to/repository phase specification \
  --next-action "Author canonical FSD"
```

Notes are merged into the Discovery Packet on every `discover`; phases are never
rewound by hooks.

## Resolve variants

Inspect the non-secret summary in:

```bash
governancectl --repo /path/to/repository status
```

The runtime stores detailed local records under the repository's Git common directory.
Resolve an R-ID only after reviewing the named worktree snapshots:

```bash
governancectl --repo /path/to/repository resolve \
  --id R-001 \
  --choice keep-canonical \
  --note "Owner selected the canonical variant after reviewing both snapshots."
```

Choices are `keep-canonical`, `adopt`, `combine`, `defer`, `obsolete`, and
`return-to-agent`. The command records the decision; it does not apply code changes.
`adopt`, `combine` and `return-to-agent` leave the record `pending` until a later
`reconcile` or `close-stage` finds the variant gone; until then the stage cannot close.

Dispositions bind the version reviewed. Changed content needs a fresh R-ID; unchanged
scans preserve prior choices. A changed/committed variant supersedes a pending record,
not evidence of completed integration. Earlier snapshots and choices remain intact.

`incomplete-recovery` means excluded or uncaptured data still needs a backup. On that
R-ID only, supply `--recovery-ref /separate-backups/version.enc` with a note explicitly
attesting coverage. The file must exist, be nonempty and outside registered worktrees.
The runtime checks its hash and availability, not its semantic completeness. Do not
use a generic “backed up” note as evidence. An unavailable worktree or unidentifiable
current version cannot be waived; restore access and reconcile. See
[the recovery contract](references/recovery.md) before manual restoration.

## Hooks

```bash
governancectl --repo /path/to/repository install-hooks
```

This merges project-level Cursor and Claude Code entries while preserving unrelated
configuration; re-running it replaces the governance entries instead of duplicating
them. Hooks activate only when `.governance/config.json` enables them. The Stop hook
warns and never blocks; only `close-stage` gates.

## Specification chain

Governance delegates canonical specifications to `spec-chain` after worktree
reconciliation and blocking owner decisions:

1. Run the CON gate. Skip it when viability, actors, scope, budget and product shape
   are already ratified.
2. Write `docs/<project>-FSD.md` with complete F-ID inventory and acceptance.
3. Write `docs/<project>-TSD.md` with T-ID design and F-ID traceability.
4. Validate before invoking `plan-waves-slices`.

```bash
python3 ~/.local/share/agent-skills/spec-chain/scripts/validate_spec.py \
  --repo /path/to/repository \
  --project project-slug \
  --mode governance
```

Markdown is authoritative. Generate a derived Word edition only when requested:

```bash
node ~/.local/share/agent-skills/spec-chain/scripts/render_docx.js \
  --input /path/to/repository/docs/project-slug-FSD.md \
  --profile internal \
  --output /path/to/repository/docs/exports/project-slug-FSD.docx \
  --verify
```

`--verify` produces PDF and page images beside the DOCX. Inspect those images before
delivery. Client profile rejects TSD and obvious implementation detail.

## Validate and close

The commands below preserve the default legacy lifecycle. For stronger completion
gates, explicitly opt the active run into a frozen stage contract after owner review;
read [stage contracts](references/stage-contracts.md) first. This is not policy-2
activation and is not a new specification or plan.

```bash
python3 ~/.local/share/agent-skills/spec-chain/scripts/validate_spec.py \
  --repo /path/to/repository --project project-slug --mode governance
python3 ~/.local/share/agent-skills/plan-waves-slices/scripts/validate_plan.py \
  --repo /path/to/repository --mode governance
governancectl --repo /path/to/repository validate
governancectl --repo /path/to/repository close-stage --owner-approved
```

`--owner-approved` records an approval already given by the owner; it must never be
supplied speculatively.

`governancectl validate` also runs the spec-chain and plan validators itself once
specifications or `docs/waves/` exist, so the last two commands are sufficient after
the documents are in place.

For an explicitly contracted run, the operational sequence is:

```bash
governancectl --repo /path/to/repository freeze-stage --contract docs/stage.json \
  --owner-approved --approval-ref /owner-records/stage-start.txt
governancectl --repo /path/to/repository run-check --id CHK-001
governancectl --repo /path/to/repository check-stage
governancectl --repo /path/to/repository validate
governancectl --repo /path/to/repository close-stage --owner-approved \
  --approval-ref /owner-records/stage-signoff.txt
```

Run every required check, not just the example ID. The last command records actual
owner sign-off after review. Read-only `check-stage --policy current` previews the
required gate without enabling policy 2. Missing/stale/failed evidence and unresolved
blocking/needs-owner findings cannot be waived with an owner flag. An external local
approval record avoids changing the tested repository merely to record sign-off.

## Revise or reopen

For changed frozen inputs, inspect `stage-impact --contract docs/stage-next.json`, review
the affected responsibilities and every retired obligation, then use owner-approved
`revise-stage` with that current review. For a closed stage, add `--reopen` explicitly:
the old acceptance stays historical and the new run needs fresh checks/sign-off.
Do not use a phase change or old test receipts as a revision. Read
[controlled iteration](references/controlled-iteration.md) for the review format,
idempotency, historical-baseline limits and when cancellation remains appropriate.

## State and privacy

- Committed activation: `.governance/config.json` (schema 3; no absolute paths)
- Shared machine-local state: `<git-common-dir>/governance/` including
  `canonical.json` and `discovery-notes.json`
- Snapshot files are mode 0600.
- Stage contracts, attempts, combined command logs and closure receipts are also private
  machine-local records. Command logs may contain secrets; review the commands before
  running them. There is no automatic redaction, pruning or remote evidence backup.
- Recognized sensitive dirty paths are excluded from new payloads and reported as
  incomplete coverage. Arbitrarily named secrets are not detected; raw working/index
  snapshots are private recovery data, not a substitute for secret scanning.
- Base commits are retained under `refs/governance/snapshots/`. There is no automatic
  pruning or remote backup, and the runtime never pushes these refs.
- Remote uncommitted work is invisible locally and requires a commit, patch or
  equivalent recoverable artifact.
