---
document_type: FSD
authority: behavior
status: draft
project: <project-slug>
---

# <Project Name> Functional Specification

## Document control

| Field | Value |
|---|---|
| Code | <PREFIX>-FSD-001 |
| Canonical decisions | [../DECISIONS.md](../DECISIONS.md) |
| Concept input | <CON path, or “concept gate skipped — see User needs baseline”> |

## User needs baseline

<Only when the CON was skipped. Otherwise replace this section's body with
“Not applicable — needs are defined in <CON path>.”>

- **Baseline authority:** <D-ID or named ratified source>

### UR-001 — <Role>

- **Description:** <who they are>
- **Environment:** <where and on what they work>
- **Expertise:** <novice / experienced / mixed>
- **Evidence class:** <class>
- **Evidence or source:** <source>

### UN-001 — <Need name>

- **Roles:** UR-001
- **Context:** <situation>
- **Underlying job:** <what they are actually trying to accomplish>
- **Decision or action:** <what they must decide or do>
- **Desired outcome:** <what is true when the job is done well>
- **Evidence class:** <class>

## Scope baseline

- In scope: <behavior>
- Out: <behavior and reason>
- Deferred: <behavior and enabling constraint>

## Actors and permissions

| Actor | UR-ID | Capability | Allowed behavior | Denied behavior |
|---|---|---|---|---|
| <actor> | UR-001 | <capability> | <behavior> | hidden and server-rejected |

## Domain vocabulary

| Term | Meaning | Forbidden alternatives |
|---|---|---|
| <term> | <meaning> | <alternatives> |

## Functional inventory

| F-ID | Kind | Name | Actor | Serves | Priority | Specification |
|---|---|---|---|---|---|---|
| F-001 | page / endpoint / command / job / event / integration / admin / journey | <name> | <actor> | UN-001, C-001 | must | [F-001](#f-001--name) |
| F-002 | journey | <name> | <actor> | UN-001, C-001 | must | [F-002](#f-002--journey) |

## Functional specifications

### F-001 — <Name>

- **Kind:** <kind>
- **Purpose:** <one observable job the item enables>
- **Serves:** <UN-IDs and accepted C-IDs>
- **Actors and permission:** <who and denial behavior>
- **Context/trigger:** <situation or event that brings the actor here>
- **Inputs/content:** <information shown or accepted>
- **Actions and outcomes:** <action and observable result>
- **States:** <initial, in-progress, empty, success, failure, unavailable, degraded, lifecycle>
- **Rules:** <validation, visibility, limits, deadlines and edge behavior>
- **Errors and recovery:** <visible failure and correction/retry>
- **Dependencies:** <F-IDs, D-IDs and external behavior>
- **Representation:** <for pages, screens, journeys and other material interactions: how the function is presented>
- **Representation rationale:** <why this presentation serves the decision better than the simpler alternatives considered, in this context>
- **Done when:** <one demonstrable acceptance statement>

## Cross-item journeys

### F-002 — <Journey>

- **Kind:** journey
- **Purpose:** <end-to-end job>
- **Serves:** <UN-IDs and accepted C-IDs>
- **Actors and permission:** <actor>
- **Context/trigger:** <what starts the journey>
- **Inputs/content:** <information carried through the journey>
- **Actions and outcomes:** <F-IDs in order and what each yields>
- **States:** <partial completion, interruption, resumption>
- **Rules:** <ordering and skipping rules>
- **Errors and recovery:** <loss of connection, expiry, partial completion>
- **Dependencies:** <F-IDs>
- **Representation:** <how the path is presented: wizard, single page, checklist>
- **Representation rationale:** <why this shape fits the job and its interruptions>
- **Done when:** <end-to-end acceptance>

## Non-functional outcomes

| ID | Outcome | Serves | Measure | Verification |
|---|---|---|---|---|
| F-NFR-001 | <observable quality> | UN-001 | <number and context> | <test or evidence> |

## Operator-configurable behavior

| Behavior | Configurable by | Boundary |
|---|---|---|
| <behavior> | <role> | <what still needs a developer> |

## Blocking open decisions

No blocking O-IDs remain.

## Open non-blocking decisions

| O-ID | Affected F-IDs | Assumption | Expires |
|---|---|---|---|
| O-001 | F-001 | <reversible assumption> | <no later than wave sign-off> |

## Verification register

| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | No external claims in behavioral specification |

## Traceability

| F-ID | Serves (UN / C) | Decisions |
|---|---|---|
| F-001 | UN-001, C-001 | D-001 |
| F-002 | UN-001, C-001 | D-001 |

## Acceptance and sign-off

<Evidence required and approver.>
