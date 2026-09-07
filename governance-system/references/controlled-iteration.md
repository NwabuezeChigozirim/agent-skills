# Controlled iteration and impact review

Read this when new evidence changes a frozen agreement, downstream work reveals an
upstream defect, or previously completed scope needs to reopen. Do not invoke revision
for every ordinary implementation edit. Local, reversible implementation refinements
that preserve agreed inputs and acceptance need fresh checks, not a new agreement.

## Authority and re-entry

1. Record the discovery as evidence, a hypothesis or an unresolved owner question.
   Product/acceptance/contract changes return upstream as O-IDs with `Raised by`; use
   blocking/needs-owner N-IDs for discovery obligations. A report never ratifies intent.
2. Obtain the necessary owner decision. Preserve stable IDs and explicit supersession;
   do not silently reuse an old ID for an unrelated promise or delete deferred work.
3. Re-enter the earliest affected responsibility: user reality in discovery/CON,
   behavior in FSD, technical contracts in TSD, ordering/dependencies in planning, or
   implementation/verification for local changes. Update the owning artifacts only.
4. Inspect impact against the old agreement, review downstream consumers, and revise
   the stage contract explicitly if its agreed inputs or acceptance must change.
5. Run fresh checks and the existing validators before seeking owner sign-off again.

Governance coordinates and records agreement; spec-chain revises specifications;
plan-waves-slices revises slices/order/status. An affected artifact needs review, not
necessarily an edit. Do not regenerate unrelated files or restart all discovery merely
because one dependency changed. The generation order describes initial construction,
not an irreversible pipeline.

## Read-only impact

```bash
governancectl --repo . stage-impact
governancectl --repo . stage-impact --contract docs/stage-next.json
# Preview still exits nonzero while policy 2 is unreleased:
governancectl --repo . stage-impact --contract docs/stage-next.json --policy current
```

The first command compares current context with the frozen agreement; the second also
compares a proposed successor contract. Inspection neither runs checks nor creates
state, writes artifacts, adopts policy 2, grants approval or marks work incomplete/done.
`analysis_valid` means a report could be constructed, not that specifications or
acceptance are valid. Missing contracts/helpers or unreadable inputs are reported errors.

New freezes retain a compact historical impact baseline: file hashes/modes, definition
fingerprints, dependency edges, finding fingerprints and graph diagnostics. It watches
the configured canonical CON/FSD/TSD, `DECISIONS.md`, `design.md`, wave index/briefs/
checklist and declared stage inputs/outputs. Prior watched paths remain in comparisons
so deletion is visible. It does not copy complete document contents or become a new
mutable source of product authority.

The report includes:

- added/removed/changed files and definitions, including NFRs and compact D-ID rows;
- changed discovery findings without promoting their evidence class;
- potentially affected requirements, technical items, slices and waves, with a first
  propagation link where one exists;
- changes to the proposed scope, acceptance obligations, checks, inputs and outputs;
- retired definitions/obligations requiring explicit rationale;
- re-entry responsibilities, uncertainty and a content-bound `impact_sha256`.

Dependency traversal uses the union of old and current edges. Removing an edge cannot
hide its former consumer. It follows need/response/realization/decision and slice
dependency edges; wave references connect technical context to planning. Containing
waves are reported without automatically authorizing or rewriting their other slices.
Both graph builders remain owned by their existing skills.

This is deliberately conservative file-and-graph impact. A changed file seeds its
defined objects even when only unparsed prose changed; the tool cannot certify that
prose harmless. Graph errors are visible uncertainty, not evidence that missing edges
have no consumers. Unmodeled dependencies and external state still need human review.
Large specification files may therefore produce broad review lists.

Historical Wave 4 contracts have input hashes but no prior impact graph. The runtime
does not fabricate that history: it reports missing-baseline uncertainty, compares
available hashes and requests broad re-entry review. A newly approved successor gains
a baseline. No implicit migration or rewrite of the historical contract occurs.

## Review and revise an active agreement

After updating the proposed contract and upstream artifacts under their proper
authority, prepare a JSON review matching the current report. Review files may be
canonical-relative or external local regular files, subject to the same safety rules
as approval records. For example, a report requesting intent and validation review
with no retirements/uncertainty can be acknowledged as:

```json
{
  "version": 1,
  "impact_sha256": "COPY_THE_ACTUAL_REPORT_DIGEST",
  "rationale": "The owner reviewed the revised input and retained the existing outcome",
  "activities": {
    "intent": "D-014 records the clarified constraint; downstream scope is unchanged",
    "validation": "Run every required check against the updated contract and content"
  },
  "retirements": {},
  "uncertainty": ""
}
```

Use the actual digest, exact reported activity keys and substantive rationales. An
activity rationale records the owner-reviewed response or re-entry plan; it is not
machine proof that the activity has been completed. `retirements` must name exactly
every retired item, such as `acceptance:AC-002`, `checks:CHK-002`, `inputs:old.txt`,
`outputs:old.txt` or `definitions:F-002`, and explain its disposition. Removing a
definition is not automatically acceptable; follow the owning artifact's supersession
and deferral rules. A nonempty uncertainty response is required when coverage is limited.
The [review schema](../schemas/impact-review.schema.json) describes the shape; runtime
checks also bind the digest and exact obligations.

```bash
governancectl --repo . revise-stage --contract docs/stage-next.json \
  --review /owner-records/stage-impact-review.json \
  --owner-approved --approval-ref /owner-records/stage-revision.txt \
  --reason "New evidence invalidated the earlier input assumption"
```

The owner must approve the revised scope and commands, not just request an analysis.
The runtime recomputes impact and rejects a stale review, missing retirement/re-entry
rationale or changed approval/input during its consistency checks. Do not regenerate a
review digest and assume the old approval applies to the new content.

Revision publishes an immutable successor with a link to the predecessor, exact
review, approval reference and fresh baseline, then atomically changes the run pointer.
The old contract and attempts remain intact; lineage is checked on later inspection.
All required checks start unsatisfied in the successor. There is no selective reuse,
even for apparently unaffected requirements. A successful identical retry is a
no-write no-op; a no-change request cannot manufacture revision history.

The phase label is not silently changed. `next_action` names the reviewed re-entry
responsibilities and fresh-check obligation. A revision does not resolve blocking
N-IDs, settle O-IDs, waive validators/recovery, update wave status or authorize another
wave. Those responsibilities remain with their existing owners and gates.

## Reopen completed work

When the current contracted run is closed, ordinary revision is refused. Before
starting a separate run with `discover`, inspect the closed stage's impact and use
the same reviewed revision command with the explicit `--reopen` flag:

```bash
governancectl --repo . revise-stage --contract docs/stage-next.json \
  --review /owner-records/stage-impact-review.json --reopen \
  --owner-approved --approval-ref /owner-records/stage-reopen.txt \
  --reason "Later evidence requires reconsidering the completed agreement"
```

This creates a new active run and successor contract, clears current completion/
approval state, and requires fresh checks and sign-off. It retains and hash-binds the
old closure receipt as historical acceptance; it does not rewrite the past as never
completed. Missing/corrupt historical closure evidence cannot be bypassed by reopening.
`--reopen` cannot reset an already active run. The command acts on the current recorded
run, not an arbitrary old ST-ID; broader historical navigation is not implemented.

Cancellation remains available for genuinely abandoned work or an unusable canonical
selection. It records non-completion and keeps contract gates enabled. Do not use
cancellation to label the abandoned stage successful or evade review of a continuing
agreement. Ordinary `discover`/fresh-run behavior and legacy defaults remain unchanged.

## Scope and trust limits

Impact context is advisory. Only declared frozen inputs retain their existing hard
change gate; watching more artifacts does not silently broaden a contract's authority.
Declare the authoritative files that must gate the stage. Missing source-to-code
dependencies, O/RK relationships, environment/toolchain/service state and undeclared
files are not a comprehensive engineering graph. File and finding hashes are evidence
of change, not proof of why the change matters.

Review binding covers watched context, findings and the candidate contract, not every
implementation byte. This lets an external or unwatched review file be created after
inspection without a digest loop. New check receipts still bind the full supported
canonical working/index subject before closure. Put review/approval records outside
the watched inputs; including them in their own reviewed context creates a hash loop.

Run-state writes are locked; editors and external Git writers are not. Quiesce them
across approval/publication. A failed pointer write leaves the predecessor active and
may retain an unreferenced successor; it is not accepted or deleted automatically.
Contracts, reviews and lineage are private local records, not authenticated owner
identity, independent assurance or off-machine backups. No policy-2 release or hook
hardening is implied by this wave.
