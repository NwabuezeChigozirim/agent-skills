---
document_type: CON
policy_version: 1
authority: concept
status: draft
project: <project-slug>
---

# <Project Name> Concept Document

## Document control

| Field | Value |
|---|---|
| Code | <PREFIX>-CON-001 |
| Canonical decisions | [../DECISIONS.md](../DECISIONS.md) |
| Chain | FSD: not started · TSD: not started |
| Philosophy | `need-first.md` — nothing earns its place by identity, possibility, precedent or novelty |

# Part A — User reality

## Problem and current workaround

<Who is affected, what they do today, what it costs them. Evidence classed.>

## User roles

| UR-ID | Role | Environment | Expertise | Evidence class |
|---|---|---|---|---|
| UR-001 | <role> | <where, devices, connectivity> | <novice / experienced / mixed> | <class> |

### UR-001 — <Role>

- **Description:** <who they are and what they are accountable for>
- **Environment:** <where and on what they work; connectivity, devices, conditions>
- **Expertise:** <novice / experienced / mixed, and why it matters>
- **Evidence class:** <class>
- **Evidence or source:** <interviews, observation, documents, assumption>

## Multi-party workflow

<When several roles take part in one transaction: the whole workflow, hand-offs, and
where each party's need diverges. "Not applicable — single role" when it is.>

## User needs

| UN-ID | Roles | Underlying job | Frequency | Criticality | Evidence class |
|---|---|---|---|---|---|
| UN-001 | UR-001 | <job> | <how often> | <consequence of error> | <class> |

### UN-001 — <Need name>

- **Roles:** UR-001
- **Context:** <the situation in which the need arises>
- **Current situation:** <how the job is done today; workarounds>
- **Stated request:** <what users or stakeholders asked for, verbatim where possible>
- **Underlying job:** <what they are actually trying to accomplish; not the request>
- **Decision or action:** <what they must decide or do>
- **Information required:** <what they must know to do it confidently>
- **Information not required:** <what would only add noise>
- **Desired outcome:** <what is true for them when the job is done well>
- **Frequency:** <how often>
- **Criticality:** <consequence of getting it wrong>
- **Constraints:** <environment, trust, commercial, regulatory, device, time>
- **Evidence class:** <class>
- **Evidence or source:** <who, what, when>
- **Confidence:** <high / medium / low, and what would raise it>

## Trust and economics

<What each role must be able to trust; what is commercially sensitive; who pays and why.>

## Domain constraints

| Constraint | Source | Evidence class | Effect on the product |
|---|---|---|---|
| <constraint> | <law, physics, external system, operations> | <class> | <effect> |

## Current alternatives

| Alternative | Who uses it | What it does well | Where it fails |
|---|---|---|---|
| <alternative> | <roles> | <strength> | <gap> |

## Evidence and assumptions register

| ID | Statement | Class | Source | Invalidates | Validation |
|---|---|---|---|---|---|
| E-001 | <statement> | <class> | <source and date> | <UN/C IDs at risk if false> | <how and when it will be checked> |

## Open product questions

<Canonical O-ID references; each with what it blocks.>

## Non-goals

| Non-goal | Reason | Needs affected |
|---|---|---|
| <what we will not do> | <why> | <UN-IDs, if any> |

## Success from the user's perspective

| UN-ID | Success looks like | Measure | Evidence source | Review date |
|---|---|---|---|---|
| UN-001 | <outcome statement> | <number and context> | <where the number comes from> | <date> |

# Part B — Product responses

Derived through Need → Desired outcome → Candidate response → Possible interaction.
A response is what we propose to do about a need; an interaction is one way of
presenting it. Only `accepted` responses feed the FSD.

## Response inventory

| C-ID | Kind | Serves | Status | Evidence class |
|---|---|---|---|---|
| C-001 | <kind> | UN-001 | <accepted / hypothesis / rejected / deferred> | <class> |

### C-001 — <Response name>

- **Kind:** <capability / expose-information / remove-step / default-change / simplification / rule-change / representation-change / wording / do-nothing / defer>
- **Serves:** UN-001
- **Status:** <accepted / hypothesis / rejected / deferred>
- **User:** <who specifically>
- **Context:** <in what situation>
- **Underlying job:** <what they accomplish>
- **Decision or action:** <what this lets them decide or do>
- **Required information:** <what they must know>
- **Desired outcome:** <what changes for them>
- **Proposed response:** <what we propose>
- **Simplest adequate response:** <the least complex response that satisfies the need>
- **Alternatives considered:** <simpler or different responses weighed, and why not>
- **Incremental value:** <what the richer response adds beyond the simplest>
- **Cost:** <cognitive, implementation, maintenance, performance, workflow>
- **Trust and privacy:** <what it exposes or implies>
- **Removal test:** <which outcome becomes materially worse without it>
- **Evidence class:** <class>
- **Decision references:** <D-IDs and O-IDs>

## Deferred needs

| UN-ID | Why deferred | What keeps it cheap later |
|---|---|---|
| <UN-ID or none> | <reason> | <constraint to preserve> |

## Constraints

<Budget, time, policy, devices, connectivity, operations. Show arithmetic when a
conclusion depends on it.>

## Concept risks

| ID | Affected UN/C IDs | Trigger | Likelihood | Impact | Response and fallback | Owner |
|---|---|---|---|---|---|---|
| RK-001 | <IDs> | <trigger> | <level> | <impact> | <response> | <owner> |

## Blocking open decisions

No blocking O-IDs remain.

## Verification register

| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | No external claims in concept |

## Recommendation

<Build, build a reduced version, or do not build — and which accepted responses the
owner is asked to ratify into DECISIONS.md.>
