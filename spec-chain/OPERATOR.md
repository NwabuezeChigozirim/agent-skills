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

```bash
python3 scripts/validate_spec.py --repo /path/to/repository --project project-slug --mode governance
python3 scripts/trace_chain.py   --repo /path/to/repository --project project-slug
python3 scripts/trace_chain.py   --repo /path/to/repository --project project-slug --id T-004
```

Validation is structural and deterministic: fixed item schemas, known IDs, `Serves`
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
