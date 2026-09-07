# Wave 4 — Stage contracts and completion evidence

Start authority: the owner's “Proceed to wave 4”, followed by “Resume”. Wave 5 and
policy-2 activation remain gated. Work continues from the uncommitted Waves 1–3 baseline.

## Contract

Phase labels and an owner flag alone must not establish engineering completion.
An explicitly frozen stage names its scope, inputs, outputs, acceptance obligations
and executable checks. Completion requires current successful check evidence, intact
inputs and outputs, resolution of blocking intent, existing validation/recovery gates
and explicit owner sign-off bound to the checked content.

Preserve the three skills, stable engineering IDs, read-only diagnostics, need-first
authority, existing recovery and default policy-1 behavior. Stronger stage contracts
are an explicit per-run opt-in for legacy projects and required by current-policy
previews; policy 2 remains unreleased. Do not initialize, upgrade or install hooks in
the source checkout. Execute mutation tests only in disposable fixtures.

This wave does not implement general change-impact propagation, automatic re-planning,
independent semantic assurance or hook hardening. Cancellation must preserve history
and cannot masquerade as successful completion or silently disable opted-in gates.

## Implementation

- `freeze-stage` accepts an explicit owner-reviewed JSON contract: bounded scope,
  frozen inputs, required outputs, acceptance obligations and executable check IDs.
  The immutable stored copy binds repository/run identity, canonical worktree, input
  hashes and the start-approval reference. Repeated identical freeze is a no-write
  no-op; different scope cannot silently replace the active contract.
- Contracts are explicit per-run opt-in under legacy policy. Existing default closure
  remains unchanged; current-policy inspection requires a contract. This makes the
  implemented gate usable and testable without falsely releasing the unfinished
  policy-2 lifecycle. No config or template default was changed.
- `run-check` executes only a declared argv in canonical, without an implicit shell.
  Attempts, logs and results are retained create-only. Results bind the contract and
  canonical HEAD, raw working/index fingerprint and declared file hashes, including
  Git-ignored inputs/outputs. Both pre- and post-execution subjects must match.
- Required checks must all have a current successful latest attempt. Missing evidence,
  failure, timeout, inability to launch, corrupt results/logs and interrupted attempts
  gate completion. New failure never falls back to an older success. Source/staging
  changes make results stale even at the same HEAD; changed frozen inputs require a
  new owner-reviewed contract, not merely another test run.
- `check-stage` inspects these predicates without running commands or creating state.
  `validate` and `audit` include opted-in stage findings alongside their existing checks.
  Current-policy validation also requests the existing sibling graph previews. JSON
  separates stage readiness, implemented artifact validity and the policy-release gate.
- `resolve-note` binds a blocking/needs-owner finding to a unique active/accepted D-ID
  and the owner's rationale. It preserves the finding, evidence class and resolution
  history. A changed/removed decision row reopens the obligation; incidental citations,
  phases and test results cannot settle intent. Observation/hypothesis notes do not
  become approval obligations merely because they exist.
- Contracted `close-stage` requires actual owner authorization and an approval record,
  in addition to existing artifact, worktree and recovery gates. A create-only receipt
  binds the contract, final checked subject, selected execution receipts and sign-off
  reference/hash. It does not write wave status or authorize the next wave.
- Approval references may be canonical-relative or absolute regular files outside
  registered worktrees. External local records allow actual post-test owner sign-off
  without editing the tested source. No remote records are fetched and symlinks are
  rejected. Closed-stage inspection detects changed/unavailable retained approvals.
- `cancel-stage` preserves contract, evidence and cancellation history and explicitly
  records non-completion. Contract enforcement stays enabled within the run; replacement
  requires new approval. Canonical selection changes gate the old contract but do not
  prevent explicit cancellation. Interrupted cancellation/closure can resume using a
  matching retained record without overwriting it.
- The stage helper and schema remain owned by governance. The suite packaging check
  requires the helper. Existing run/discovery schemas gain additive stage/resolution
  fields. No fourth skill, new global requirements authority or mutable status copy
  was introduced.

Skill-creator guidance kept the governance entrypoint focused on when to freeze and
when to stop, with conditional mechanics in
[the stage contract reference](../../governance-system/references/stage-contracts.md).
Operator, lifecycle, discovery and compatibility references describe the same boundary.
The specification and planning skills' ownership remains unchanged.

## Verification

Verified locally on 2026-09-07, Linux, Python 3.12.3 and Node 22.22.1. The full
`scripts/check.py` run exited 0:

| Check | Result |
|---|---|
| Governance runtime and suite tests | 42 passed |
| Specification tests | 29 passed |
| Planning tests | 36 passed |
| Wave 1 compatibility/upgrade tests | 22 passed |
| Wave 2 recovery tests | 26 passed |
| Wave 3 graph tests | 27 passed |
| Wave 4 stage-contract tests | 31 passed |
| Original review regressions | 10 passed; 2 expected failures |
| Renderer, including PDF/page-image verification | 4 passed |
| Suite structure and governance skill entrypoint | Passed |
| Supplemental contract/closed-run/resolved-note JSON Schema checks | Passed |
| `git diff --check` | Passed |

Total: **223 passing Python tests and 4 passing renderer tests**, with two known hook
defects explicitly retained as expected failures. Original gaps 06 and 07 now assert
specific current-preview contract and blocking-note findings, not policy refusal alone.
Separate opt-in tests exercise actual successful and rejected `close-stage` operations
under legacy policy, proving that the new gate is functional rather than a preview-only
error. No remaining expected-failure assertion was weakened.

Final supplemental assertions cover 0600 evidence permissions, changed closed-stage
approval records, interrupted cancellation retry and audit's no-write/no-execution
behavior; the three affected tests were rerun after those assertions were added.

The fixtures also cover empty/invalid contracts, unknown IDs, missing outputs, same-HEAD
and staging-only changes, ignored declared output changes, failed/mutating/timed-out
commands, interrupted attempt/contract/closure publication, log/receipt corruption,
owner flags/references, decision changes, canonical changes, conservative cancellation,
external sign-off, unreleased policy rejection, uninitialized read-only previews,
idempotency and preservation of worktree/recovery gates.

Renderer dependencies were reused from the existing isolated review installation via
`NODE_PATH`; no dependencies were installed in the source checkout. Supplemental JSON
Schema checks used the host's existing validator, not a new runtime dependency. Runtime
and Python tests remain standard-library/Git only. Hosted Linux/macOS CI and independent
agent-behavior evaluations were not run; these are local deterministic results.

Source-content manifest SHA-256 (excluding this self-referential record):
`56bb2037cdc2226ed91a7852b753ecfd36a4dc2115ee9f385d86982335836362`.
Reproduce from the repository root:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':(exclude)docs/evolution/wave-4.md' | sort -z | xargs -0 sha256sum | sha256sum
```

## Boundaries and evolution risks

The new mechanism proves declared command execution and content correspondence, not
the semantic adequacy of tests, completeness of input declarations or authenticity of
human approval. Owner flags are attestations, not an identity system. Hashes detect
corruption, not an actor able to replace both data and checksums. A zero-exit command
can still be a poor test; acceptance review remains essential.

The checked subject is conservative but local. It does not seal external service state,
environment values, installed toolchains or Git-hidden undeclared content. All declared
input/output files are hashed even if ignored. Input files are whole-file dependencies;
there is no selective revalidation or changed-assumption propagation yet. Requirements
and slice IDs in acceptance descriptions remain review links, not a new typed graph.

Check argv is not a sandbox or additional side-effect authority. Commands need owner
review; logs can contain secrets and have no automatic size cap, redaction or pruning.
Execution is timeout-bounded and serialized under the runtime lock. Recursive mutating
governance commands would wait on that lock and must not be used as checks. Timeout
cleanup targets the process group, not independently detached services or external
effects. Quiesce writers across final checks/closure; the runtime cannot provide a
filesystem-wide transaction with editors or other Git processes.

Per-run opt-in intentionally does not migrate existing projects. Cancellation retains
gates in that run; after successful closure, a new run requires its own explicit
contract while policy 1 remains the default. This is not yet universal lifecycle
enforcement. Wave 5 can add controlled revision and impact propagation; Wave 6 retains
the known adapter enforcement work. Policy 2 must remain unreleased until all gates pass.

Regression signals include legacy closure changing without opt-in, a phase satisfying
acceptance, stale/failed evidence yielding completion, lost prior attempts or decisions,
cancellation bypassing gates, changed intent silently reusing a contract, validation
executing commands or writing state, forged claims of semantic assurance, and excessive
reruns/context/storage cost without an engineering benefit. Use paired positive/negative
fixtures and actual project observations to evaluate refinements before wider adoption.

## Adoption and next gate

All mutation and execution tests used disposable fixtures. The source checkout was not
governance-initialized, upgraded, given hooks, frozen into a stage or provided recovery
refs. No commit, push or release was performed. All earlier Waves 1–3 edits remain.

Wave 4 implementation is ready for owner review; owner sign-off has not been recorded.
Wave 5 requires fresh progression approval. Waves 5–6 and policy-2 activation remain gated.
