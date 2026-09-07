# Wave 3 — Specification and planning graph enforcement

Start authority: the owner's “Proceed” after the Wave 2 handoff explicitly requested
permission to begin Wave 3. At that handoff Wave 4 remained gated. The owner's subsequent
“Proceed to wave 4” authorized the next stage; see its [record](wave-4.md). Results below
remain the historical Wave 3 record.

## Contract

Policy-2 previews distinguish definitions from citations, ratification from evidence,
nonempty obligations from labels, and real graph edges from inventory membership.
They cover accepted-response authority, functional acceptance, NFR realization and
verification, trace consistency, wave/slice membership and dependency order, rationale,
and recorded approval/sign-off references.

Preserve the three packages, stable IDs, legacy-policy behavior, need-first reasoning,
vertical slicing, no-write diagnostics and owner-only progression. Policy 2 remains
unreleased: previews expose implemented checks but cannot activate incomplete SDLC
enforcement. Do not modify projects, hooks, commits or releases during this wave.

## Implementation

- A shared, standard-library-only artifact reader recognizes the suite's definitions,
  labeled obligations, sections and table rows. Fenced examples and HTML comments do
  not create definitions. Duplicate definitions and duplicate labels remain visible
  as diagnostics rather than silently collapsing into one item.
- Specification validation owns a derived, typed graph of users, needs, responses,
  functional and non-functional requirements, technical items and recorded decisions.
  Definitions are distinct from incidental citations. Explicit decision references
  must resolve to active or accepted register entries where ratification is required.
- Acceptance and verification obligations require meaningful content, not just a
  label. NFRs require outcomes, measures, verification and technical realization;
  an NFR-only technical item is legitimate. Accepted hypotheses still produce a weak
  evidence warning: owner ratification is not empirical proof.
- TSD trace rows must match the technical items' realization edges and the FSD's
  authoritative need/response links in both directions. Inventories cannot substitute
  for definitions or edges. Optional FSD trace tables, when present, retain functional
  coverage and link-consistency checks.
- Backward tracing includes NFRs, uses the same graph findings and exposes weak-evidence
  warnings in JSON and human output. Its explicit standalone mode uses the standalone
  decision register. Selecting one ID limits the displayed trace, not graph validation.
- Planning validation owns a derived wave/slice graph: index, brief and slice IDs must
  agree; rationale, exit criterion and slice obligations must be meaningful; dependency
  targets must exist and precede their consumers. Duplicate slices, self-dependencies,
  forward dependencies and cycles produce distinct findings. Both existing exit-criterion
  heading and bold-label conventions remain supported.
- Normal slices serve defined functional or non-functional requirements; infrastructure
  slices identify the requirements they unlock. Infrastructure-only waves warn rather
  than forcing artificial restructuring. Standalone planning without specifications
  remains possible and explicitly warns that requirement references are unvalidated.
- In-progress waves require a recorded start-approval reference; completed waves also
  require a sign-off reference. Both separate columns and the existing combined evidence
  column are supported. Referenced decisions must be active/accepted; local referenced
  files must exist, be nonempty and remain inside the repository. External references
  warn that they have not been fetched or authenticated.
- Current-policy JSON distinguishes `graph_valid`, `artifact_valid` and overall `valid`.
  A structurally clean preview still fails the separate unreleased-policy gate. Legacy
  defaults and policy-1 behavior remain unchanged. No template opts projects into policy 2.
- Suite packaging validation now checks that the shared reader and both graph modules
  are distributed with their owning packages. This adds no fourth skill or persisted
  graph authority: Markdown artifacts and existing authority rules remain the inputs.

The skill-creator guidance kept the skill entrypoints brief and routed conditional
details to the [specification graph contract](../../spec-chain/references/graph-validation.md)
and [planning graph contract](../../plan-waves-slices/references/graph-validation.md).
The operator and policy-compatibility references describe the same preview boundary.

## Verification

Verified locally on 2026-09-06, Linux, Python 3.12.3 and Node 22.22.1. The full
`scripts/check.py` run exited 0:

| Check | Result |
|---|---|
| Governance runtime and suite tests | 42 passed |
| Specification tests | 29 passed |
| Planning tests | 36 passed |
| Wave 1 compatibility/upgrade tests | 22 passed |
| Wave 2 recovery tests | 26 passed |
| Wave 3 graph tests | 27 passed |
| Original review regressions | 8 passed; 4 expected failures |
| Renderer, including PDF/page-image verification | 4 passed |
| Suite structure and all three skill entrypoints | Passed |
| `git diff --check` | Passed |

Total: **190 passing Python tests and 4 passing renderer tests**, with four known
later-wave defects retained as expected failures, not passed checks. The final additive
trace-warning output change was subsequently covered by the 27-test graph suite,
including JSON and human-output CLI assertions; that targeted rerun also passed.

Seven original regressions (01–05 and 09–10) lost their expected-failure allowance.
Their negative fixtures now assert specific graph errors or evidence warnings rather
than treating policy-2 refusal alone as success. Gap 08 remains fixed by Wave 2. The
remaining allowances cover phase completion, blocking findings/test evidence, Git
global-option hook handling and enabled-guard fail-closed behavior; none was weakened.

Positive fixtures establish clean graphs despite the separate release refusal. Negative
fixtures exercise undefined/prose-only authority, duplicate definitions, empty obligations,
edge disagreements, missing NFR realization, examples masquerading as definitions,
invalid slice dependencies, index mismatches and missing approval references. Other
fixtures preserve legacy behavior, standalone operation, infrastructure warnings,
cross-wave dependencies, existing exit syntax, deterministic output and read-only checks.

Renderer dependencies were reused through `NODE_PATH` from the existing isolated review
installation; no dependencies were installed into the source checkout. The hosted
Linux/macOS CI matrix and independent agent-behavior evaluations were not run. Passing
fixtures establish local structural behavior, not whole-SDLC or semantic acceptance.

Source-content manifest SHA-256 (excluding this self-referential record):
`24b005ace9f08de5824c908344d10f2c242b591b5c6e036b3a81a694659a7d9d`.
From the repository root:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':(exclude)docs/evolution/wave-3.md' | sort -z | xargs -0 sha256sum | sha256sum
```

## Boundaries and evolution risks

The reader implements the suite's documented Markdown contracts, not a general Markdown
parser. Indented prose continuations are supported, but ID-bearing fields stay on their
label line for compatibility with existing readers. Additional authoring conventions
should enter through representative fixtures, not silent parser permissiveness.

`graph_valid` describes the graph checks; `artifact_valid` describes the invoking tool's
implemented non-policy checks. Neither proves that requirements are correct, tests ran,
an acceptance claim is true or the full current policy is implemented. Planning does
not replace specification validation. The graphs are derived views, not new mutable
sources of truth.

Approval-reference checks establish recorded structural links only. They do not
authenticate an owner, establish the referenced approval's scope/version/time, inspect
test results or validate anchors within files. External references are not fetched.
These checks neither grant execution authority nor replace the existing owner gate;
stronger stage and completion-evidence contracts belong to Wave 4.

This wave does not introduce frozen-contract state, change-impact propagation,
requirements re-entry orchestration or architectural dependency-cycle analysis.
Only slice execution dependencies receive DAG/order enforcement here. Later iteration
work must preserve stable IDs and distinguish legitimate revision from stale approval.

Regression signals include legacy projects suddenly failing, valid standalone planning
requiring a full specification suite, NFR-only realization being rejected, weak evidence
being treated as proof, a citation satisfying a missing definition, extra trace edges
escaping detection, lost diagnostics, validation writes, false approval claims and
excessive authoring ceremony. Keep positive and negative fixtures paired, and measure
real project false positives and review effort before activating policy 2.

## Adoption and next gate

All mutation tests ran in disposable fixtures. The source repository was not
governance-initialized, upgraded or given hooks/recovery refs. No commit, push or release
was performed. Existing Waves 1–2 edits remain in the worktree.

At this historical handoff, Wave 3 was ready for owner review and Wave 4 required fresh
progression approval. The subsequent Wave 4 start authority is recorded above;
Waves 5–6 and policy-2 activation remain gated.
