# CON — Concept Document

The CON is the discovery artifact of the chain. It answers who we are serving, what
they are trying to accomplish, how they do it today, what makes that hard, and only
then what product responses deserve to exist. It is not an early feature list.
[need-first.md](need-first.md) governs its reasoning.

## Concept gate

A CON is required for a greenfield product, a substantial rebuild, a major new product
surface, or whenever no accepted user-needs baseline exists. Skip it only when a
ratified baseline with equivalent UR/UN content and identifiable authority already
exists; the FSD then names that baseline. Record the evidence supporting a skip.

## Part A — User reality

Establish before any product shape is proposed:

- user and customer types, and the distinctions between roles;
- real-world environments, devices, connectivity;
- existing workflows and current alternatives or workarounds;
- jobs-to-be-done, the decisions made inside them, and the information each decision
  needs and does not need;
- pains, delays, uncertainty, risks;
- trust requirements and commercial sensitivity;
- economic motivations;
- frequency and criticality of each task;
- domain constraints (law, physics, external systems, operating conditions);
- novice versus experienced users where the difference changes the job;
- desired outcomes from the user's perspective;
- evidence, assumptions and hypotheses, each classed;
- unresolved product questions;
- explicit non-goals;
- success criteria stated as user outcomes.

Where several parties take part in one transaction, model the complete workflow and
the differing needs of each participant. Do not optimise one side in isolation.

### UR schema

```
### UR-001 — <Role>
- **Description:** who they are and what they are accountable for
- **Environment:** where and on what they work; connectivity, devices, conditions
- **Expertise:** novice / experienced / mixed, and why it matters
- **Evidence class:** <class>
- **Evidence or source:** <interviews, observation, documents, assumption>
```

### UN schema

Core labels (always present): `Roles`, `Context`, `Underlying job`, `Decision or
action`, `Desired outcome`, `Evidence class`. Include the others when they carry
information; omit them when genuinely irrelevant.

```
### UN-001 — <Need name>
- **Roles:** UR-IDs
- **Context:** the situation in which the need arises
- **Current situation:** how the job is done today; workarounds
- **Stated request:** what users or stakeholders asked for, verbatim where possible
- **Underlying job:** what they are actually trying to accomplish
- **Decision or action:** what they must decide or do
- **Information required:** what they must know to do it confidently
- **Information not required:** what would only add noise
- **Desired outcome:** what is true for them when the job is done well
- **Frequency:** how often the job occurs
- **Criticality:** consequence of getting it wrong
- **Constraints:** environment, trust, commercial, regulatory, device, time
- **Evidence class:** <class>
- **Evidence or source:** <who, what, when>
- **Confidence:** high / medium / low, and what would raise it
```

`Stated request` is evidence about the user. `Underlying job` is derived from context
and must never be a restatement of the request. A user who asks for a map may need to
judge whether supply is economically practical to mobilise; the job admits several
responses.

## Part B — Product responses

Only after Part A, derive responses through:

```
Need → Desired outcome → Candidate response → Possible interaction
```

Keep the links distinct. A response is what we propose to do about a need; it may be a
capability, exposing existing information, removing a step, changing a default,
simplifying a workflow, combining information, changing wording, altering a business
rule, choosing a representation, deliberately doing nothing, or deferring. An
interaction is one way a response might be presented; it is never the need.

### C schema

Every C carries the Contextual Necessity Test. Create a C only for material,
product-shaping responses; trivial mechanical behaviors are specified directly in the
FSD against their UN.

```
### C-001 — <Response name>
- **Kind:** capability / expose-information / remove-step / default-change /
  simplification / rule-change / representation-change / wording / do-nothing / defer
- **Serves:** UN-IDs
- **Status:** accepted / hypothesis / rejected / deferred
- **User:** who specifically
- **Context:** in what situation
- **Underlying job:** what they accomplish
- **Decision or action:** what this lets them decide or do
- **Required information:** what they must know
- **Desired outcome:** what changes for them
- **Proposed response:** what we propose
- **Simplest adequate response:** the least complex response that satisfies the need
- **Alternatives considered:** simpler or different responses weighed, and why not
- **Incremental value:** what the richer response adds beyond the simplest
- **Cost:** cognitive, implementation, maintenance, performance, workflow
- **Trust and privacy:** what it exposes or implies
- **Removal test:** which outcome becomes materially worse without it
- **Evidence class:** <class>
- **Decision references:** D-IDs and O-IDs
```

A response that cannot survive the test keeps status `hypothesis`, `rejected` or
`deferred` and does not feed the FSD. Only `accepted` responses may be served by F
items. Every UN is served by at least one C or is listed under non-goals or deferred
needs with a reason.

## Structure

1. Document control and chain register.
2. Part A — User reality: roles (UR), environments, workflows, needs (UN), trust and
   economics, domain constraints, current alternatives, evidence and assumptions
   register, open questions, non-goals, user-perspective success criteria.
3. Part B — Product responses: derived responses (C) with the Contextual Necessity
   Test, explicit exclusions, deferred responses and what keeps them cheap later.
4. Constraints: budget, time, policy, devices, connectivity, operations.
5. Concept risks using RK-IDs.
6. Open decisions as references to canonical O-IDs.
7. Recommendation: build, build a reduced version, or do not build.

Do not include screens, routes, source paths, schemas, frameworks or build order.

## Budget mechanism

When an envelope exists, state assumptions, show arithmetic and compare the concept
against the envelope. If it does not fit, recommend a smaller coherent product rather
than quietly removing disconnected features.

## Rebuilds

For a rebuild, Part A draws on the existing system as evidence: extract business rules,
invariants, transaction semantics, vocabulary, integrations, trust lessons and
operational constraints, each classed as `observed-behavior`, `domain-constraint` or
`fact` with its source. Existing screens, navigation, workflows, feature hierarchy,
identity and interaction metaphors enter Part B only as candidate responses that must
pass the Contextual Necessity Test like any other.

## Handoff

The owner ratifies accepted responses into `DECISIONS.md`. The FSD consumes accepted
C-IDs and their UN-IDs; the CON itself does not make choices binding.
