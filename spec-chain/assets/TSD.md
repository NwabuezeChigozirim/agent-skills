---
document_type: TSD
authority: technical-design
status: draft
project: <project-slug>
---

# <Project Name> Technical/System Design

## Document control

| Field | Value |
|---|---|
| Code | <PREFIX>-TSD-001 |
| Functional input | [<project-slug>-FSD.md](<project-slug>-FSD.md) |
| Canonical decisions | [../DECISIONS.md](../DECISIONS.md) |

## Decisions closed since FSD

| D-ID | Decision | Technical consequence |
|---|---|---|
| D-001 | <decision> | <consequence> |

## Architecture

<Components, topology, request/event lifecycle and transaction boundaries. State why
this is the simplest adequate architecture for the accepted F-IDs and which choices
stay reversible while uncertainty remains.>

## Technology selections

| Concern | Selection | Rejected alternative | Rationale | Decision |
|---|---|---|---|---|
| <concern> | <verified selection> | <alternative> | <reason> | D-001 |

## Cost evidence

<Verified tiers, source dates, assumptions, arithmetic, conclusion and fallback, or
“Not applicable — no external cost conclusion.”>

## Repository and module design

<Annotated layout, ownership, import rules and enforcement.>

## Data design

<Entities, constraints, indexes, retention, deletion, migrations and rollback.>

## Contract surfaces

| Contract | Kind | Consumers | Compatibility | Realizes |
|---|---|---|---|---|
| <name and version> | API / event / command / schema | <consumers> | <promise> | F-001 |

## Technical requirements

### T-001 — <Name>

- **Purpose:** <technical outcome>
- **Realizes:** <F-IDs and D-IDs>
- **Design:** <implementation shape>
- **Interfaces/contracts:** <named contracts>
- **Invariants and failure handling:** <constraints and failure posture>
- **Security/data considerations:** <controls and data handling>
- **Verification:** <tests or evidence>
- **Dependencies:** <T-IDs, services and platform constraints>
- **Risks:** <RK-IDs or none>

## State machines and engines

<Transitions, guards, permissions, algorithms and reproducibility.>

## Cross-cutting implementation

<Authentication, authorization, configuration, secrets, storage, background work,
rate limits, concurrency, observability, audit, privacy and performance.>

## Testing and verification

<Layered strategy and required failure/security/performance evidence.>

## Delivery environments and operations

<CI, deployment mechanics, environment differences, backup, restore and recovery.>

## Risks

| ID | Affected F/T IDs | Trigger | Likelihood | Impact | Response and fallback | Owner |
|---|---|---|---|---|---|---|
| RK-001 | F-001, T-001 | <trigger> | <level> | <impact> | <response> | <owner> |

## Blocking open decisions

No blocking O-IDs remain.

## Open non-blocking decisions

| O-ID | Affected T-IDs | Default | Needed by |
|---|---|---|---|
| O-001 | T-001 | <safe reversible default> | <point> |

## Product deltas surfaced

<O-IDs raised against the FSD or CON for product-behavior problems or materially
better product possibilities discovered during design, or “None”. The TSD realizes
accepted F-IDs only; it never absorbs a product change.>

## Verification register

| Claim | Source | Accessed | Calculation or conclusion |
|---|---|---|---|
| <claim> | <URL or authoritative document> | <YYYY-MM-DD> | <result> |

## Traceability

| F-ID | Serves (UN / C) | Implementing T-IDs | Verification |
|---|---|---|---|
| F-001 | UN-001, C-001 | T-001 | <tests or evidence> |
| F-002 | UN-001, C-001 | T-001 | <tests or evidence> |
| F-NFR-001 | UN-001 | T-001 | <measurement or evidence> |

## Planning handoff

<Dependencies, contract candidates, verification tasks, non-blocking O-IDs and RK-IDs.
No milestones, waves, slices or mutable status.>
