# Wave 5 — Controlled revision and change-impact review

Start authority: “Commit and push then proceed to wave 5”. Waves 1–4 were committed
and pushed to `origin/main` as `d21fb96` before this wave began. The source worktree
was clean at the boundary. Wave 6 and policy-2 activation remain gated.

## Contract

Make changed assumptions visible and support explicit re-entry without erasing prior
agreement. A read-only impact report compares a frozen baseline with current artifacts
and a proposed stage contract, follows known dependency edges through specifications
and slices, and states the limits of that analysis. An owner-reviewed revision links
an immutable successor to its predecessor and invalidates all prior check evidence.

Preserve stable engineering IDs, artifact ownership, legacy defaults, explicit per-run
opt-in, worktree/recovery gates and the distinction between authority and evidence.
Do not rewrite specifications/plans automatically, silently retire obligations, reuse
stale approval, waive tests based on an incomplete graph, or release policy 2.

Mutation tests use disposable fixtures. Wave 5 changes are separate from the already
pushed Waves 1–4 checkpoint. Subsequent owner authority, “You can go ahead and push
now”, authorizes committing and pushing Wave 5; it does not authorize Wave 6.

## Implementation

- `stage-impact [--contract PATH]` compares the frozen agreement with current context
  and, optionally, a proposed contract. It reports changed artifacts, definitions,
  discovery findings, potential consumers, retired obligations, re-entry activities
  and uncertainty. It neither executes checks nor writes state or engineering artifacts.
  `analysis_valid` is separate from acceptance and the policy-release gate.
- New freezes store an immutable compact baseline: hashes/modes, definition
  fingerprints, graph edges and finding fingerprints. Watched sources include the
  configured CON/FSD/TSD, decisions, design, wave index/briefs/checklist and declared
  inputs/outputs. Prior watched paths remain visible after deletion. Historical Wave 4
  envelopes remain readable without mutation; missing historical coverage is explicit
  uncertainty, never an invented baseline.
- Governance reuses the specification and planning skills' graph builders. Propagation
  traverses the union of old and current edges, so removing a relationship cannot hide
  its former consumer. Changed files conservatively seed their defined objects even
  when unparsed prose changed. NFRs, compact decision rows, technical references,
  dependencies and the ratified no-CON baseline participate. Graph errors remain
  visible limits on coverage, not proof of harmlessness.
- `revise-stage` requires an explicit owner flag, approval record, meaningful reason,
  proposed contract and review bound to the current impact digest. Every reported
  re-entry activity and retired definition/input/output/check/acceptance obligation
  needs a rationale. Stale reviews, changed proposals and missing uncertainty responses
  cannot silently authorize new scope. Revision never resolves a blocking N-ID itself.
- Revision publishes a new immutable stage, then atomically changes the run pointer.
  It retains the predecessor, review and prior attempts; subsequent inspection verifies
  the lineage. No previous check receipt transfers. The successor must satisfy every
  required check and all existing closure/recovery/intent gates. Identical successful
  retries are no-write no-ops; unchanged work cannot manufacture revision history.
- `revise-stage --reopen` is explicit for a closed current run. It requires intact
  historical acceptance, creates a new run identity and clears current completion/
  approval state. The old closure receipt remains hash-bound historical evidence.
  Ordinary revision cannot reopen completed work, and `--reopen` cannot reset an
  active run. Fresh checks and owner sign-off are required to close the successor.
- Phase labels remain independent of acceptance. Revision records re-entry in
  `next_action`; it does not rewrite specifications, update wave status, approve the
  next wave or automatically restart all discovery. Cancellation remains abandonment,
  not the normal mechanism for revising a continuing agreement.
- The runtime helper and review schema stay inside governance. Packaging checks
  require the helper. No fourth skill, alternate mutable requirements register or
  new default policy was introduced.

Skill-creator guidance kept entrypoint additions short and conditionally routed to
[controlled iteration](../../governance-system/references/controlled-iteration.md).
Specification and planning retain their artifact ownership; governance owns agreement
revision and reopening. Operator, lifecycle, compatibility and authority references
describe those same boundaries.

## Verification

Verified locally on 2026-09-07, Linux, Python 3.12.3 and Node 22.22.1. The complete
`scripts/check.py` invocation exited 0:

| Check | Result |
|---|---|
| Governance runtime and suite tests | 42 passed |
| Specification tests | 29 passed |
| Planning tests | 36 passed |
| Wave 1 compatibility/upgrade tests | 22 passed |
| Wave 2 recovery tests | 26 passed |
| Wave 3 graph tests | 27 passed |
| Wave 4 stage-contract tests | 31 passed |
| Wave 5 impact/revision/reopening tests | 31 passed |
| Original review regressions | 10 passed; 2 expected failures |
| Renderer, including PDF/page-image verification | 4 passed |
| Suite structure and all three skill entrypoint validators | Passed |
| Supplemental impact-review and reopened/reclosed-run JSON Schemas | Passed |
| `git diff --check` | Passed |

Total: **254 passing Python tests and 4 passing renderer tests**, with no unexpected
failures or successes. The two known hook regressions remain explicitly expected
failures: Git global-option classification and enabled pre-action fail-closed behavior.
Neither assertion nor hook implementation was changed in this wave.

Paired positive/negative fixtures exercise actual revised/reopened closure, fresh
check requirements, stale review/input/command rejection, explicit retirement and
re-entry rationales, deleted definitions/edges, changed compact decisions and NFRs,
unmodeled prose, historical baseline uncertainty, blocking findings, missing graph
helpers, multi-revision lineage, missing predecessors/closure receipts, publication
failure, consistency races, exact retries and policy-2 refusal. Read-only assertions
compare repository/state bytes, modes, entries and mtimes, excluding access times.
Owned specifications/plans and earlier acceptance are checked for preservation.

Renderer dependencies were reused from the existing isolated review installation
through `NODE_PATH`; its package lock matched the source byte-for-byte. No dependency
was installed in this checkout. Supplemental schema checks used the host's existing
validator, not a runtime dependency. Python runtime/tests remain standard-library/Git
only. Hosted CI results were not inspected and independent agent-behavior evaluations
were not run; local deterministic results do not establish cross-host or behavioral
effectiveness.

Source-content manifest SHA-256 (excluding this self-referential record):
`560daf29c53f54e432ccf83bb6135b12b4e29dbec86c78bd1fc13922ba752338`.
Reproduce from the repository root:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':(exclude)docs/evolution/wave-5.md' | sort -z | xargs -0 sha256sum | sha256sum
```

## Boundaries and evolution risks

Impact is review scope, not proof of semantic effect. The graph is not comprehensive
source-to-code, risk/open-item, external-service or environment traceability. Large
specification files can therefore produce broad review lists. Retaining old watched
paths and verifying predecessor chains incurs cumulative history cost; there is no
automatic pruning or remote backup. Do not weaken conservatism or discard evidence
without measurements and a separately reviewed retention/reuse design.

Watched context remains advisory; only declared frozen inputs retain the existing
hard change gate. This wave does not silently widen a stage's authority to every
observed artifact. Declare the authoritative files that must gate execution/closure.
Impact cannot waive required checks, even when a consumer appears unaffected.

Owner flags and review rationales are attestations, not authenticated identity or
machine proof that re-entry activities were performed. A review can document an
approved response or plan, not just completed work. Proper upstream decisions,
substantive validation and acceptance review still matter. Findings keep their
evidence class; revision approval does not settle unresolved intent.

Review binding covers watched context, findings and the proposed contract, not every
implementation byte. Fresh check receipts still bind the full supported canonical
working/index subject and declared files. Keep review/approval records outside their
own watched inputs to avoid a digest loop. Historical hash-only agreements require
broader review because their old graphs cannot be reconstructed reliably.

State mutations are locked but editors and other Git writers are not. Consistency
checks detect changes during review; quiesce external writers across publication.
A failed pointer write leaves the predecessor active and can retain an orphan
successor; it is neither accepted nor automatically deleted. Reopening operates on
the current recorded contracted run, not an arbitrary historical stage ID.

Regression signals include lost earlier acceptance, a removed edge hiding consumers,
stale review authorizing changed scope, old test evidence satisfying a successor,
revision resolving an owner question, analysis modifying owned artifacts, default
legacy behavior changing without opt-in, and unnecessary broad replanning. Improvement
should show that new evidence reaches the right owner with less lost context and
uncontrolled churn, without increasing review effort beyond its engineering value.
Deterministic fixtures establish mechanics; actual project observations and later
agent-behavior evaluations must establish behavioral effectiveness.

## Adoption and next gate

Waves 1–4 were committed and pushed as
`d21fb96c796fa8988ba754623c0ef4fbe6180581`; `origin/main` was verified to match. Wave 5
was handed off as a separate, uncommitted change set. The owner's subsequent “You can
go ahead and push now” authorizes its own commit and push. Before committing, the
source-content manifest above was rechecked and matched the tested implementation.

All mutation/execution checks use disposable fixtures. The source checkout has no
governance activation, local runtime state or recovery refs; it was not upgraded or
given hooks. Existing policy-1 defaults remain unchanged and policy 2 is unreleased.
Wave 6 requires fresh owner progression approval. Its known hook-adapter gaps and
behavioral/release evaluation work are not claimed complete by this wave.
