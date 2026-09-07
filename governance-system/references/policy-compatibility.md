# Policy compatibility and explicit upgrades

Read this when auditing, upgrading, or generating artifacts for an existing project.
Config **schema** describes storage; engineering **policy** describes enforcement.
Changing storage schema does not ratify decisions or establish test evidence.

## Development release boundary

Policy 1 preserves the working baseline. Policy 2 is reserved for the reliability and
iteration program and is **not released**. Until all six waves pass their release
gates, newly initialized configs and generated templates explicitly use policy 1.
Do not publish this intermediate checkout as complete policy-2 enforcement.

Wave 2's recovery safety corrections also apply under policy 1: new captures are
immutable and content-bound, and incomplete or unverifiable recovery blocks closure.
This does not adopt policy 2's future specification, planning or completion gates.
Old snapshots and owner choices are retained; their missing version/coverage proof
is not silently upgraded into an approval. See [recovery.md](recovery.md).

`--policy current` reports the unavailable policy and exits nonzero. Wave 3's
specification, trace and planning validators also run their implemented graph checks
and report specific findings, without adoption. `artifact_valid` excludes policy
errors and reports only implemented artifact checks; `graph_valid` is the graph subset.
Neither is complete engineering acceptance or permission to proceed. Runtime upgrades
and policy-2 execution remain gated. See the
[specification](../../spec-chain/references/graph-validation.md) and
[planning](../../plan-waves-slices/references/graph-validation.md) preview contracts.

Wave 4 adds explicit per-run stage-contract opt-in under policy 1. It does not change
the project policy or silently adopt the other policy-2 gates. Opt-in requires the
owner-approved `freeze-stage` command; cancellation cannot disable it within that run.
`check-stage --policy current` and `validate --policy current` are read-only previews
of required stage contracts and current content-bound check evidence. A clean
`stage_valid` still cannot pass the separate policy-release gate. See
[stage contracts](stage-contracts.md) for owner records, executable checks and limits.

Wave 5 extends those explicit contracts with historical impact baselines and reviewed
successors, including explicit reopening of completed work. Default legacy runs remain
unchanged. Existing Wave 4 envelopes are read without mutation and their missing prior
graph coverage is reported; only a newly approved freeze/revision gains a baseline.
`stage-impact` is read-only; revision/reopening never waives check, recovery or release
gates. See [controlled iteration](controlled-iteration.md).

Wave 6 hardens the opted-in hook surface under policy 1 as a safety correction, not
automatic policy-2 adoption. Enabled pre-action failures deny, live edit ownership is
checked, and host-specific review translation preserves normal permissions. Ordinary
legacy runs without hooks/contracts retain their opt-in boundaries. Hook hardening
and local test success do not release policy 2; see [hook policy](hooks.md) for limits.

## Selection

An explicit post-Wave-6 owner requirement makes the FSD role-capability matrix a
mandatory authoring/validation check under both policies. Existing FSDs without it
now fail specification validation until revised with authorization; their historical
acceptance, contents and policy marker are not rewritten. This is a deliberate
completeness-rule change, not policy-2 activation. See
[FSD coverage](../../spec-chain/references/fsd.md#roles-and-capability-coverage--required-in-every-fsd).

- A project's `.governance/config.json` is authoritative when present.
- Without that config, standalone documents declare `policy_version` in frontmatter.
- An unversioned config or document means legacy policy 1, not automatic adoption.
- Conflicting document markers, invalid values and config/document disagreement are
  errors. A CLI flag cannot downgrade declared authority.
- Specification validation, trace walking, plan validation, runtime validation and
  stage inspection accept
  `--policy auto|legacy|current` (default `auto`) and report the selected policy in JSON.
- All command-line tools use `governance-system/scripts/engineering_policy.py`, the
  one read-only policy selector shipped within the existing three-package layout.

## Inspection is not migration

```bash
governancectl --repo /path/to/repository doctor
governancectl --repo /path/to/repository status
governancectl --repo /path/to/repository audit
governancectl --repo /path/to/repository upgrade --dry-run
```

These commands do not create config, canonical selection, run state, locks, snapshots
or backups. Validation is also read-only. Audit obtains fresh inventory and checks
existing governed artifacts, but neither reconciles variants nor establishes
acceptance. An uninitialized repository has no selected governed artifact set; use
the standalone validators with explicit paths/names for its documents.

Schema-2 config remains readable without rewriting its path-derived identity. Its
canonical selection is respected when the worktree is registered and available;
otherwise the local main worktree is the derived default. `discover` may explicitly
initialize local state but never upgrades an existing config as a side effect.

## Explicit application

The eventual current-policy adoption command is:

```bash
governancectl --repo /path/to/repository upgrade --apply
```

It is gated while policy 2 is unreleased. For an explicitly requested **metadata-only**
upgrade that retains legacy behavior:

```bash
governancectl --repo /path/to/repository upgrade --dry-run --policy legacy
governancectl --repo /path/to/repository upgrade --apply --policy legacy
```

This converts schema 2 to schema 3, preserves or materializes its local canonical
selection, and records policy 1. A schema-3 unversioned config only gains explicit
policy metadata. Unknown project extensions, historical decisions, run state,
specifications, wave status and hook settings are preserved. Artifact problems are
reported but are not silently repaired by a metadata migration. No approvals or
evidence are manufactured.

Before the first write, exact original config/canonical bytes and a manifest are
stored privately under `<git-common-dir>/governance/upgrades/<content-hash>/`.
The returned `backup` path identifies them. A repeated successful application is a
no-write no-op. If a prior incomplete attempt owns that backup, stop and inspect it
instead of overwriting recovery material.

For rollback, compare the current metadata with the migration and backup before
restoring only the affected config/canonical metadata. Never restore an entire Git
directory or delete new records, decisions, evidence or worktree content. An original
absence of canonical state is recorded in the manifest; removing a newly established
selection requires checking that no subsequent owner decision depends on it.
