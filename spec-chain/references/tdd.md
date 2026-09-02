# TSD — Technical/System Design

TDD is accepted as a user-facing synonym, but the canonical governed artifact is TSD.
It owns how validated FSD behavior is realized without owning delivery order. It
inherits its authority from the FSD: technical design exists to satisfy accepted
behavior and non-functional constraints, never to create product requirements.

## Design bias

Prefer, in order: the simplest architecture that satisfies the accepted requirements;
reversible decisions where uncertainty remains; low operational burden; clear trust
boundaries; domain correctness and data integrity; maintainability; explicit
concurrency and integrity requirements where the domain needs them; realistic cost;
progressive complexity only when a cited requirement or risk justifies it.

A technology cannot create a requirement. PostGIS being available does not require a
map; realtime infrastructure does not make a workflow realtime; an AI capability does
not create an AI interaction; a visualization library does not establish a need for
visualization. Every T-ID realizes F-IDs that already exist.

## Entry gate

Every O-ID marked as blocking technical design is resolved. The FSD inventory validates
and every F-ID has acceptance. Open the TSD with decisions closed since the FSD and the
technical consequences of each D-ID.

## Technical requirement schema

Every major technical requirement receives a stable T-ID and all labels:

- **T-ID and name**
- **Purpose**
- **Realizes** — F-IDs and D-IDs
- **Design**
- **Interfaces/contracts**
- **Invariants and failure handling**
- **Security/data considerations**
- **Verification**
- **Dependencies**
- **Risks** — RK-IDs

Technical examples use real names and signatures where they remove ambiguity. Code is
design intent, not final source. Comment reasoning rather than syntax.

## Structure

### 1. Document control and traceability

Inputs, authority, closed decisions, conventions, F-ID coverage and requirement
strength.

### 2. Architecture

Components, topology, request/event lifecycles, transaction boundaries, dependency
direction and enforced module boundaries.

### 3. Technology selections

Selection, verified version policy, alternatives rejected, rationale and D-ID. Do not
lock a technology without ratified intent.

### 4. Infrastructure and cost envelope

When relevant: verified tiers, volume assumptions, arithmetic, fit, thresholds and
fallbacks. Each external assertion records source and access date.

### 5. Repository and module design

Annotated layout, ownership, import rules, generated artifacts and boundary enforcement.

### 6. Data design

Identifiers, time, money, retention, deletion, entities, constraints, indexes,
migrations, rollback meaning, seed data and access controls.

### 7. Contract surfaces

Named APIs, commands, events, schemas and generated client/types. Record consumers,
compatibility, versioning and intended wave-freeze candidates without freezing them;
wave sign-off performs the freeze.

### 8. Services and state machines

Service boundaries, result/error model, state transitions, guards, permissions,
idempotency and single-path mutation invariants.

### 9. Non-obvious engines

Rules, evaluation, scoring, matching, search, compilation or scheduling algorithms.
Specify reproducibility and snapshots where later replay matters.

### 10. Cross-cutting implementation

Authentication, authorization, configuration, secrets, storage, notifications,
background work, caching, rate limiting, concurrency, observability, audit, privacy,
security headers and performance.

### 11. Testing and verification

Layered test strategy, contract tests, migration tests, failure tests, security tests,
performance evidence and explicit tests for the design’s highest-risk failure modes.

### 12. Delivery environment and operations

CI checks, deployment mechanics, environment differences, platform verification,
backup, restore rehearsal, recovery objectives and operator procedures.

### 13. Risk register

RK-ID, affected F/T IDs, likelihood, impact, trigger, concrete response, fallback and
owner. Unverified platform assumptions become risks or verification tasks.

### 14. Open technical decisions

Canonical O-ID references, needed-by point and safe reversible default when one exists.

### 15. Product deltas surfaced

Mandatory section. When technical work exposes a product-behavior problem or a
materially better product possibility, record it here as a reference to the O-ID raised
against the FSD or CON; state "None" when nothing was surfaced. The TSD never absorbs a
product change by realizing behavior no accepted F-ID describes. Refinements that do not
change product meaning, user-visible behavior, rules, trust boundaries or acceptance stay
technical decisions and need no O-ID.

### 16. Traceability

Every F-ID maps to T-IDs, and each row carries the UN/C IDs the F serves so the chain
reads backward to a user and an outcome. Orphan F-IDs and T-IDs are errors.

## No delivery-plan ownership

The TSD may state dependencies, prerequisites, contract boundaries, verification tasks
and stopping constraints. It must not create milestones, waves, slices, schedules,
mutable status or implementation sequence. `plan-waves-slices` derives those from the
validated TSD and FSD.

## Handoff to planning

Provide validated F-ID/T-ID traceability, contract candidates, technical dependencies,
verification tasks, unresolved non-blocking O-IDs and RK-IDs.
