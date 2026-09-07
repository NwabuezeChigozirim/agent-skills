# FSD — Functional Specification

The FSD answers: what must the system enable the user to accomplish? It owns observable
behavior — what actors can see, submit, trigger, receive and verify — and is the
delivery acceptance source. It derives from the accepted CON; it is not an independent
feature-invention phase. [need-first.md](need-first.md) governs its reasoning.

## Entry gate

An accepted UN inventory exists (CON Part A, or a ratified `User needs baseline` when
the CON was skipped). Actors, scope, core domain concepts and behavior-shaping decisions
are ratified. An O-ID that changes the inventory, permission model, lifecycle or
acceptance blocks the affected section.

## Skipped CON: user needs baseline

When no CON exists, the FSD opens with `## User needs baseline` containing UR and UN
items in the CON schema and a `Baseline authority` line naming the D-ID or ratified
source that makes them binding. Without this section the FSD has no upstream and does
not validate.

## Inventory

Create a complete inventory before writing item specifications. Supported item kinds:

- page or screen;
- endpoint or externally visible API operation;
- command or CLI operation;
- scheduled or background job;
- event and resulting behavior;
- external integration behavior;
- administrative operation;
- cross-item journey.

Every inventory row has a stable F-ID, kind, name, actor, priority and specification
section. Every row appears exactly once as a full item specification.

## Fixed functional item schema

Every item uses every label:

- **F-ID and name**
- **Kind**
- **Purpose** — one observable job the item enables
- **Serves** — the UN-IDs and accepted C-IDs this item realizes
- **Actors and permission** — who may act or observe; denial behavior
- **Context/trigger** — situation or event in which the actor reaches this item
- **Inputs/content** — information shown or accepted, without storage design
- **Actions and outcomes** — actor action and visible/system outcome
- **States** — initial, loading/in-progress, empty, success, failure, unavailable,
  degraded and item-specific lifecycle states
- **Rules** — validation, ordering, visibility, limits, deadlines and edge behavior
- **Errors and recovery** — actor-visible failure and retry/correction path
- **Dependencies** — other F-IDs, D-IDs and external behavior
- **Done when** — one demonstrable acceptance statement

Use “not applicable — reason” only when a label genuinely cannot apply. Never omit it.

## Function, representation, rationale

For material user interactions — every page or screen and every cross-item journey,
and any other item whose interaction model materially shapes the workflow or commits
the product to a significant metaphor — add:

- **Representation** — how the function is presented (list, table, distance text, map,
  calendar, wizard, conversational surface)
- **Representation rationale** — why this presentation serves the decision better than
  the simpler alternatives considered, in this context

Keep the functional requirement independent of the representation:

```
F-014 — Understand supply proximity
- Purpose: the hirer can judge the practical proximity of suitable supply to the project location
- Serves: UN-006, C-011
- Representation: distance and broad area in results, with optional spatial exploration
- Representation rationale: the decision is practical proximity; exact coordinates are
  protected during discovery and distance supports direct comparison
```

is a functional requirement. "The application shall open to a full-screen interactive
map" is an interface commitment and needs its own accepted C showing that spatial
visualization itself materially serves the job. When several presentations satisfy the
same function, preserve the function and do not turn one presentation into product law
unless the presentation is itself required.

Do not demand a rationale for every microscopic element; a label, a button or a
mechanical confirmation needs none.

## Kind-specific additions

### Page or screen

Navigation entry, content order by information hierarchy, empty-region behavior,
accessibility behavior and responsive expectations.

### Endpoint

Actor-visible request purpose, accepted input semantics, success result, expected
failure meanings and authorization behavior. Route shape and wire schemas belong to
the TSD.

### Command

Invocation purpose, actor, accepted arguments, confirmation behavior, observable
output, exit meanings and safe retry.

### Job

Business trigger, affected actors/data, observable result, late/missed-run behavior,
duplicate-run behavior and operator-visible failure.

### Event or integration

Business trigger, recipient/system behavior, failure visibility, retry expectation and
degraded behavior. Provider, transport and adapter design belong to the TSD.

## Roles and capability coverage — required in every FSD

The reader must be able to answer “who uses this system, and what can each of them
do?” without reconstructing the answer from individual specifications. Include
`## Role-capability matrix` near the front, even for a single-role or headless system.
This is the product's role-based functional overview, not merely a login/permissions
table or a commitment to a technical role-based access-control implementation.

- Take the complete UR inventory from the accepted CON or ratified FSD baseline.
  Column headings identify each UR-ID and its readable role name. Include guests,
  operators, integration callers and automated actors when they actually exist in
  that baseline; do not invent an administrator or login requirement by convention.
- Use columns `F-ID`, `Feature / action`, then one column per role. Each row cites one
  defined F-ID and names a distinct observable action or received outcome. Split
  “manage bookings” into the specified create, view, change, cancel or approve actions
  where their behavior or permissions differ. Several rows may cite the same F-ID.
  Every specified F-ID, including jobs and journeys, must be represented.
- Every role/action cell states `Allowed — explanation`, `Conditional — condition`,
  `Denied — restriction`, or `Not applicable — reason`. Conditions identify relevant
  ownership, tenant, lifecycle, delegation or other domain boundaries. No blank cells,
  ticks, “all access” shorthand or implied administrator inheritance. Draft uncertainty
  is `Unresolved — O-ID and question`; it blocks handoff, not silently becomes access.
- A role with no current system action still appears, with a sourced scope explanation
  in its cells. A background outcome names who receives it or the accepted automated
  actor; lack of a screen is not grounds to omit it. Deferred/out-of-scope capabilities
  remain explicitly identified in the scope baseline, never displayed as delivered.
- Group rows by product area in multiple tables if useful; repeat all role columns.
  Shared actions need not become duplicate F specifications just because several roles
  can perform them. This matrix summarizes the existing functional inventory and
  `Actors and permission`, `Actions and outcomes` and `Rules`; it does not create a
  competing permission authority. Resolve contradictions before handoff.

For example, with these roles and behaviors already accepted:

| F-ID | Feature / action | UR-001 — Requester | UR-002 — Reviewer |
|---|---|---|---|
| F-001 | Submit a request | Conditional — submit for own account | Denied — reviewing does not grant submission |
| F-001 | View a request | Conditional — own requests only | Conditional — assigned requests only |
| F-002 | Approve a request | Denied — cannot approve own submission | Conditional — assigned and awaiting review |

Review every detailed action against the matrix and every matrix entry against its
F specification. Include permitted and denied/conditional examples in acceptance
where access affects the outcome. A role, action or rule change updates both views
and prompts downstream test/design impact review; newly discovered authority gaps
return upstream as O-IDs. Preserve stable UR/F identifiers.

The validator checks mandatory presence, table shape, known UR/F IDs, complete role
and F coverage, distinct action rows and explicit cell dispositions. It cannot prove
that discovery found every real-world role, that prose lists every action, or that a
stated permission agrees semantically with the specification. Those are review duties.

Where roles sharing a workflow need different information or controls, specify separate
items where the behavior differs rather than one generalised surface. Cite the UR
through the UN; do not duplicate an identical behavior solely for matrix layout.

## Document structure

1. Document control, authority and chain register.
2. User needs baseline (only when the CON was skipped).
3. Scope baseline, changes, exclusions and deferred behavior.
4. Required role-capability matrix: all users/actors, features/actions and conditions.
5. Domain vocabulary and behavioral lifecycles.
6. Complete functional inventory.
7. Full item specifications grouped by product area.
8. Cross-item journeys and interruption behavior.
9. Non-functional outcomes with observable verification.
10. What authorized operators can configure without a developer.
11. Acceptance process and sign-off evidence.
12. Open decisions as canonical O-ID references.
13. Assumptions, client dependencies and supplied materials.
14. Traceability: F → UN/C and F → decision. Optional, but a table that exists must
    cover every specified F and cite no F-ID the document does not specify.

## WHAT/HOW boundary

The FSD must not select frameworks, providers, database technology, queues, storage
layout, source directories, internal service classes, deployment topology, rendering
strategy or build order.

URLs may appear only when they are already a ratified external behavior. Otherwise the
TSD owns route and protocol design.

## Upstream deltas

If writing the FSD shows the CON to be wrong or incomplete in a way that changes
product meaning, user-visible behavior, rules, trust boundaries or acceptance, raise an
O-ID against the CON and pause the affected items. Do not repair the concept silently
inside the FSD.

## Client edition

The client edition is derived from the canonical FSD:

- preserve the complete role-capability matrix (readable role/action names and
  conditions), actors, needs, capabilities, rules, journeys, acceptance, dependencies and
  client open decisions;
- remove internal requirement metadata that adds no client value;
- remove all technology, provider, source path and implementation detail;
- never edit the client edition independently.

## Handoff to TSD

The TSD must map every implemented F-ID to one or more T-IDs. Blocking O-IDs are closed
before technical design begins.
