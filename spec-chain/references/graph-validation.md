# Specification graph preview

Read this when evaluating policy-2 readiness or correcting graph findings. It does not
replace the existing authoring schemas, grant approval or adopt a project policy.

```bash
python3 scripts/validate_spec.py --repo /path/to/project --project sample --mode governance --policy current --json
python3 scripts/trace_chain.py --repo /path/to/project --project sample --mode governance --policy current --json
```

For standalone specifications, pass `--mode standalone` to **both** commands so they
read the same `docs/<project>-DECISIONS.md`. Governance mode reads root `DECISIONS.md`.
Never create a second decision authority to make a trace pass.

## Read the result correctly

Policy 2 remains unreleased until the later lifecycle, evidence, iteration and adapter
waves are verified. These previews therefore still exit 3 with a policy-release error.

- `artifact_valid`: existing structural checks plus implemented graph checks passed,
  excluding policy-selection/release errors. Not engineering acceptance.
- `graph_valid`: only the graph subset passed (`null` when legacy policy is selected).
- `graph_errors` / `graph_warnings`: graph-specific diagnostics, distinct from policy
  refusal. Each finding also has a code, path, line and affected ID in `graph.diagnostics`.
- `valid`: the complete command result, including policy authority and readiness.

A release refusal alone does not demonstrate that a defect was detected. Check the
specific graph finding; a positive preview should have no artifact errors while still
reporting the release gate. Unversioned/policy-1 projects retain their existing checks.

## Enforced relationships

Definitions are UR/UN/C/F/T item headings, F-NFR identity cells in `Non-functional
outcomes`, and D identity cells in the canonical decision register. Prose citations,
comments and fenced examples do not define objects. Duplicate definitions and duplicate
fixed labels are errors, not “last definition wins.” Indented continuation text is
supported for prose obligations; keep ID-bearing fields on their label line.

An accepted C must cite a defined D whose register status is `active` or `accepted`.
The normal header-based register and the established compact `| D-ID | status |
decision |` form are supported. Mere mention of a D-ID does not ratify a response.
Ratification authorizes intent; it does not make a hypothesis empirically true.
Accepted hypotheses, assumptions, preferences and aesthetic choices retain warnings.

F items need a nonempty purpose and `Done when`; T items need a nonempty purpose and
`Verification`. Blank/placeholder-only obligations are not acceptance. The validator
does not judge whether a populated statement is useful, observable or truthful.

F-NFR rows require `Outcome`, `Serves`, `Measure` and `Verification`, with a defined
need/accepted response upstream. Their TSD trace rows and technical realization edges
are checked like functional requirements; a technical item may realize only an NFR.
Backward tracing includes every NFR and reaches its user context through UN/UR.

The TSD `Traceability` table uses `F-ID`, `Serves`, `Implementing T-IDs` and
`Verification` columns. Every requirement has one row. Each row's technical targets
must exactly match the T items whose `Realizes` fields name that requirement. Its
`Serves` set must equal the defining FSD item's set. Matching ID inventories without
matching edges is not traceability. The optional FSD trace table still must cover all
functional items; its `Serves` projection must agree with their definitions.

## Boundaries

The graph is a deterministic, read-only projection, not a new source of authority or
a persisted engineering database. Markdown remains canonical. Fix the owning source,
then regenerate the report; never edit graph output to settle a disagreement.
The parser supports the suite's documented Markdown contracts, not arbitrary Markdown
conventions. Use the existing field names rather than inventing alternate headers.

`trace_chain.py --id` limits displayed backward paths, not full policy-2 graph checking.
It still reports inconsistencies elsewhere in the loaded chain. Selective impact
analysis belongs to the separately gated iteration wave.

These checks cannot authenticate an owner, validate empirical evidence, assess the
quality of requirements, or prove implementation/test completion. They make those
responsibilities explicit and structurally accountable without claiming to replace them.
