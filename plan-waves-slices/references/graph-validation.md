# Planning graph preview

Read this when evaluating policy-2 readiness or correcting planning graph findings.
Run the existing validator with `--policy current --json`; add `--plan-name <name>`
in standalone mode. Do not change a project's marker to activate an unreleased policy.

Policy 2 remains gated. The preview can report `artifact_valid: true` while overall
`valid` remains false because the release is not ready. `graph_valid` covers only the
new graph subset; `graph_errors` and structured `graph.diagnostics` identify concrete
defects, separately from policy errors. No command here authorizes implementation.

## Wave and slice contracts

The canonical Status table must have exactly one row for each defined wave. In
governance mode, the Brief cell, `wave-N-*.md` filename and wave heading must identify
the same wave. Standalone mode needs actual wave definitions, not only a status legend.
Both modes require a `Why this wave` rationale, one nonempty exit criterion and slices.
The existing `## Exit criterion` and `**Exit criterion:**` forms are supported.

Slice IDs are unique and belong to their containing wave. Required labels remain in
force; Outcome, Why, Usable when done, Tests and Acceptance evidence need content.
Ordinary slices cite F/F-NFR requirements through Serves. Infrastructure slices cite
what they Unlock, and remain allowed; an all-infrastructure wave warns rather than
fails simply for being infrastructure.

`Depends on` names defined slice IDs or explicitly says `none`. Unknown references,
self-dependencies, cycles and dependencies on later slices are errors. “Earlier” means
the canonical index's wave order, then definition order within the brief—not sorting
stable IDs and renumbering existing work. The graph reports problems; it never silently
reorders a plan or changes an approved dependency.

Definitions in a matching FSD/TSD pair supply known requirement IDs. An ID mentioned
in prose or an example is not a definition. This check does not replace upstream
specification validation or ratify specification changes. If a standalone plan has no
FSD/TSD, it can still be planned: requirement references are explicitly reported as
unvalidated rather than forcing a new specification suite into that assignment.

## Recorded approvals, not inferred approvals

Gated rows (`⏸`) need no approval reference. In-progress rows (`🟡`) need a start
reference. Completed rows (`✅`) need both start and sign-off references. Use either:

- separate `Start approval` and `Sign-off evidence` columns; or
- the existing `Approval or sign-off evidence` column, with
  `start: <reference>; sign-off: <reference>` for a completed wave.

For an in-progress wave the combined column may simply hold its start reference.
References can be active/accepted D-IDs, nonempty local files relative to the index,
Markdown links to those files, or external HTTP(S) records. Local targets must remain
inside the repository. A bare “approved,” “done” or check mark is not a reference.
Local files are checked at file level; heading anchors are not verified. External
references warn that they have not been fetched or authenticated.

The owner/agent must verify that each referenced record actually covers that wave,
action and version. A file's presence or an active D-ID does not prove that an owner
gave that specific approval. These are structural reference checks, not authenticated
authorization, executed-test evidence or independent assurance. Do not mark a wave done
merely to make the validator pass. Wave 4 owns completion-evidence enforcement.

## Boundaries

The returned nodes and edges are a read-only projection of wave/slice membership,
requirements and dependencies. The index remains the sole status authority. This wave
does not implement frozen-contract change detection, stage transitions, test execution,
selective re-entry or automatic scheduling. Existing owner gates and engineering review
remain in force; the new checks do not claim those later capabilities are complete.
