# Specification Authority

## Ownership

- CON Part A — user reality: roles, needs, evidence, assumptions, non-goals.
- CON Part B — product responses and their Contextual Necessity Test results.
- `DECISIONS.md` — the only binding record of accepted intent and open deltas.
- FSD — observable behavior and acceptance, each item serving accepted needs/responses.
- TSD — technical design and implementation constraints realizing FSD behavior.
- `docs/waves/README.md` and wave briefs — delivery order and status.
- DOCX/client editions — derived presentation views.

When sources disagree, ratified decisions win over downstream prose. Accepted needs win
on what matters to the user. FSD wins on behavior. TSD wins on technical shape. Wave
documents may schedule requirements but cannot redefine them. A downstream artifact
never introduces material product meaning because it is newer or more detailed.

Product identity is not specification authority. It may influence presentation and
positioning; it cannot justify functionality. When identity and user utility conflict,
utility wins unless an explicit, recorded decision states the strategic reason and its
cost ([need-first.md](need-first.md) §6).

Existing implementations are evidence, not authority ([need-first.md](need-first.md) §9).

## Identifier namespaces

- Users/actors: `UR-###`
- User needs: `UN-###`
- Product responses: `C-###` (status: accepted, hypothesis, rejected, deferred)
- Decisions: `D-###`
- Open questions and upstream deltas: `O-###`
- Evidence observations: `E-###`
- Functional requirements: `F-###` (non-functional outcomes: `F-NFR-###`)
- Technical requirements: `T-###`
- Risks: `RK-###`
- Worktree resolutions: `R-###`

IDs remain stable through revisions. Supersession creates a new decision or requirement
and explicitly names the earlier ID.

## Evidence classes

`fact`, `observed-behavior`, `stakeholder-requirement`, `domain-constraint`,
`accepted-decision`, `hypothesis`, `assumption`, `preference`, `aesthetic-choice`.
Defined in [need-first.md](need-first.md) §5. The class travels with the item; a
downstream document may cite an item but may not change its class.

## Downstream flow and upstream deltas

Authority flows CON → FSD → TSD → plan. Corrections flow upstream through O-IDs when
they affect product meaning, user-visible behavior, business rules, trust or privacy
boundaries, acceptance semantics, programme scope or major ordering. Smaller
refinements are recorded where the work happens and need no governance record.

## Derived registers

Open-decision and risk sections in CON/FSD/TSD are filtered views:

- Open decisions cite canonical O-IDs without changing their status.
- Accepted choices cite canonical D-IDs.
- Risks use RK-IDs and reference affected F-IDs/T-IDs.

No specification silently promotes an assumption into a decision.
