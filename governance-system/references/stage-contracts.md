# Stage contracts and completion evidence

Read this when the owner explicitly opts a run into stronger completion gates, or
when inspecting current-policy stage readiness. Governance owns this contract;
spec-chain owns requirements and plan-waves-slices owns delivery decomposition.
Do not regenerate specifications or re-plan inside the stage runtime.

## Adoption boundary

Policy 1 retains its existing closure behavior unless `freeze-stage` explicitly opts
the active run into stage contracts. Once opted in, cancelling a stage does not turn
those gates off. The next run needs its own contract; no contract or owner approval
is inherited from a closed run. Policy 2 remains unreleased: its read-only previews
require these checks, but policy-2 mutation and upgrade commands remain blocked.

The stage contract adds gates; it cannot waive existing document validation, blocking
specification decisions, worktree resolution or recovery obligations. A passing
`check-stage` is only stage readiness, not permission to execute or close anything.
Phase labels and `next_action` remain navigation state, never acceptance evidence.

## Declare and freeze

Author one JSON declaration for the bounded stage. Its acceptance obligations should
cite the agreed requirements or slice outcomes in their descriptions, not invent a
second product specification. Select the upstream files whose change invalidates this
agreement. Inputs are frozen whole-file hashes; outputs must exist and be nonempty at
completion. Paths are canonical-repository-relative files, never directories, `.git`
paths, symlink traversals or external files.

Example shape (adapt the real scope, paths and commands before owner review):

```json
{
  "version": 1,
  "name": "Wave 1 delivery",
  "scope": "The approved W1 owner workflow; no additional product surface",
  "inputs": ["docs/product-FSD.md", "docs/product-TSD.md", "docs/waves/wave-1-delivery.md"],
  "outputs": ["src/app.py"],
  "acceptance": [
    {
      "id": "AC-001",
      "description": "W1's owner workflow meets the FSD acceptance outcomes",
      "checks": ["CHK-001"]
    }
  ],
  "checks": [
    {
      "id": "CHK-001",
      "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"],
      "timeout_seconds": 120
    }
  ]
}
```

`AC-###` and `CHK-###` are stage-local IDs, not replacements for F-, T- or slice IDs.
Every acceptance obligation needs defined checks; every declared check must support
an obligation. IDs and path lists are unique. Blank/placeholder obligations, unknown
fields, malformed command arrays and timeouts outside 1–3600 seconds are rejected.
The [schema](../schemas/stage-contract.schema.json) describes the shape; the runtime
also checks meaning-bearing fields, references, uniqueness and path safety.

```bash
governancectl --repo . freeze-stage --contract docs/stage.json \
  --owner-approved --approval-ref /owner-records/w1-start.txt
```

Supply `--owner-approved` only after the owner approved the scope, obligations and
commands. It records that authorization; it does not authenticate the owner. Approval
references are existing nonempty regular local files: relative to canonical, or
absolute outside all registered worktrees. Symlinks and remote URLs are not accepted.
The start reference must remain available and unchanged throughout the stage.

Freeze stores an immutable copy, input hashes, start-approval reference/hash and the
canonical repository/run identity under the shared Git store. Repeating the same
freeze is a no-write no-op; a different declaration cannot overwrite the active
contract. Editing the authoring JSON does not alter the frozen copy. No new skill,
wave status table, product authority or automatic code-edit permission is created.

## Run checks and inspect

```bash
governancectl --repo . run-check --id CHK-001
governancectl --repo . check-stage
governancectl --repo . validate
# Read-only preview; nonzero while policy 2 is unreleased:
governancectl --repo . check-stage --policy current
governancectl --repo . validate --policy current
```

Only `run-check` executes a command. It runs the frozen argv directly, without an
implicit shell, in the canonical worktree. A command array is not a sandbox: commands
may write files, reach services or invoke an explicitly named shell. Review commands
and obtain any additional authority needed for their side effects before execution.
There is no automatic execution during freeze, inspect, validate, audit or close.

Each attempt is create-only and recorded before execution. A result records exit
status, timestamps, the frozen contract digest, tested subject and a checksum of the
combined stdout/stderr log. A later failure or interrupted attempt supersedes an
earlier pass. Timeout, inability to start, missing/corrupt receipts and changed logs
cannot establish success. Reruns retain all older attempts.

The tested subject includes canonical path, HEAD, raw working/index fingerprint and
the hashes of declared inputs/outputs, including Git-ignored declared files. Staging
alone can change the subject. A command that changes its subject cannot certify the
post-change content; rerun after the change settles. Any subsequent subject change
invalidates all required checks conservatively. There is no selective impact analysis
yet, and external services, environment values and toolchain versions are not sealed
by this fingerprint. Declare relevant configuration files as inputs where appropriate.

`check-stage` is read-only and reports `stage_valid` separately from overall policy
validity. It does not run the sibling validators or recovery checks. `validate` adds
stage findings to those existing checks; `artifact_valid` excludes policy errors but
is still only the implemented validation boundary. Neither output grants approval.

## Resolve blocking intent

Both `blocking` and `needs-owner` discovery notes remain obligations under stage
contracts. A phase change, rediscovery or a check passing does not resolve them.

After recording the owner's accepted decision in canonical `DECISIONS.md`:

```bash
governancectl --repo . resolve-note --id N-001 --decision D-001 \
  --owner-approved --note "Owner settled the acceptance question in D-001"
```

The D-ID must be a unique active/accepted register definition, not a prose citation.
The resolution preserves the original note, evidence class and earlier resolutions.
It binds the decision row's contents; changing, removing or superseding that row
reopens the obligation. An unrelated decision row change does not. No observation or
hypothesis is upgraded into an accepted decision by this command. The runtime checks
the link and owner attestation, not whether the decision semantically settles the note.

All unresolved notes of these two kinds are conservatively blocking for the active
run. Selective scope, deferrals and generalized change-impact propagation are later
iteration work; do not delete notes to evade this gate.

## Close or cancel

After all required checks pass on the final subject and the owner reviews the results:

```bash
governancectl --repo . close-stage --owner-approved \
  --approval-ref /owner-records/w1-signoff.txt
```

Closure rescans/reconciles worktrees, retains recovery obligations, validates artifacts
and stage evidence, rechecks content and approval, then records the sign-off bound to
the contract, tested subject and specific check receipts. It does not mark a wave done
in `docs/waves/README.md`, authorize the next wave or establish independent assurance.
Updating a committed status/approval file changes the subject; make final repository
edits before the final checks. An external local owner record allows sign-off after
testing without that source change. Never pre-fill or fabricate an owner approval.

A repeated close of an already closed contracted run returns its historical receipt
without writes; it does not assert that later edits remain accepted. Inspect/validate
detect changed evidence, unavailable approval records and stale checked content.
An interrupted closure with a matching retained receipt can finish without replacing
history. Start a fresh run explicitly with `discover` when the next work is authorized.

Changed frozen inputs require an explicit decision, not a check rerun that silently
changes scope. Until versioned revision/impact propagation is implemented, cancel the
old stage and freeze the newly approved contract:

```bash
governancectl --repo . cancel-stage --owner-approved \
  --approval-ref /owner-records/w1-revision.txt --reason "New evidence invalidates the input contract"
```

Cancellation is not completion. It retains the old contract, attempts and cancellation
record; closure stays gated until a replacement contract is frozen and satisfied.
This is a bounded replacement within the same run, not automatic upstream revision or
permission to expand the owner's scope.

## Storage, trust and operational limits

Contracts, attempts, results, logs, closure and cancellation records live under
`<git-common-dir>/governance/stages/ST-.../`. Payloads are private (0600), create-only;
run-state pointers use the existing lock and atomic replacement. A publication failure
can leave retained unreferenced records, never an implicitly active partial contract.
Do not manually delete failed attempts or edit run-state to manufacture acceptance.

Check execution holds the runtime lock. Do not recursively invoke a mutating governance
command from a check; it would wait on the same lock. Inspection commands are read-only
and do not acquire that lock. Timeouts kill the check's process group; detached services
and other external side effects are outside that cleanup boundary. Logs can contain
secrets and are not automatically redacted, size-limited or pruned: use bounded,
non-secret-producing verification commands and the existing private-state trust model.

Checksums detect accidental corruption, not an actor who can rewrite both records
and checksums. No local CLI flag authenticates a human, and a process exiting zero
does not prove that its assertions adequately cover the acceptance obligation.
Owner review, useful tests and later independent assurance remain necessary.
Filesystem writers are not locked; quiesce them across final checks and closure.
