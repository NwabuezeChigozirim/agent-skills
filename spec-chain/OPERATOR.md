# Spec Chain Operator Guide

## Authority

Canonical outputs are Markdown:

- `docs/<project>-CON.md` — user reality (UR, UN) then product responses (C); required
  for greenfield, substantial rebuild, major new surface, or when no ratified user-needs
  baseline exists;
- `docs/<project>-FSD.md` — behavior; every F serves UN/C IDs;
- `docs/<project>-TSD.md` — realization; every T realizes F IDs.

DOCX, PDF, page images and client editions under `docs/exports/` are derived.

Read `references/need-first.md` once; every other document points at it.

## Validate

Validators and trace walking are read-only. They accept `--policy auto|legacy|current`
and report the effective policy in JSON. Unversioned projects remain legacy;
current-policy previews explicitly report that policy 2 is not yet released. See
[policy compatibility](../governance-system/references/policy-compatibility.md).

Policy-2 previews now check definition-backed ratification, exact realization/Serves
edges and NFR verification. They expose `artifact_valid`, `graph_valid` and specific
graph findings while still refusing unreleased policy-2 activation. See
[graph validation](references/graph-validation.md). Pass `--mode standalone` to the
trace walker as well as the validator when using a standalone decision register.

```bash
python3 scripts/validate_spec.py --repo /path/to/repository --project project-slug --mode governance
python3 scripts/trace_chain.py   --repo /path/to/repository --project project-slug
python3 scripts/trace_chain.py   --repo /path/to/repository --project project-slug --id T-004
```

Every FSD requires a role-capability matrix, including single-role and headless
systems. See [FSD roles and coverage](references/fsd.md#roles-and-capability-coverage--required-in-every-fsd)
for its schema and review duties. This owner-requested completeness check applies
under both policies: older FSDs without the matrix now report a validation error.
Validation does not rewrite them or change project policy. Add the matrix from
accepted UR/F definitions during an authorized revision; do not invent missing
permissions or retroactively claim old acceptance satisfies this new check.

Validation is structural and deterministic: complete role/F matrix coverage and
explicit action dispositions, fixed item schemas, known IDs, `Serves`
citing only accepted C, representation rationale on pages/screens/journeys, CON
structure, UN coverage, F/T traceability, decision references, blocking O-IDs, WHAT/HOW
boundaries, RK-ID use, source dates, `Product deltas surfaced`, and duplicate decision
authority. Warnings (non-blocking) flag accepted responses whose evidence class is
`assumption`, `preference` or `aesthetic-choice`, and F items whose only upstream need
has low confidence.

`trace_chain.py` prints the backward chain for one ID or for every accepted F and T
(T → F → C → UN → UR) and exits 3 on a break. It checks structure; judging whether the
chain is honest remains a review task.

## Render

Dependencies are pinned in `package-lock.json`. Restore Node dependencies with:

```bash
npm ci
```

System rendering requires `soffice` and `pdftoppm`. Generate and verify an export:

```bash
node scripts/render_docx.js \
  --input /path/to/repository/docs/project-slug-FSD.md \
  --profile internal \
  --output /path/to/repository/docs/exports/project-slug-FSD.docx \
  --verify
```

Profiles live under `assets/profiles/`. The output must stay under the input document’s
`exports/` directory. Client profile rejects TSD and obvious implementation material.

Inspect every generated page image. Automated rendering proves file integrity and basic
layout, not visual correctness.
