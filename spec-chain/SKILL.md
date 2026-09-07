---
name: spec-chain
description: >
  Author or revise a Concept Note, Functional Specification, or Technical/System
  Design for software products, modules, APIs, services, jobs, integrations, and user
  interfaces. Use when the user asks for a CON, FSD, TDD, TSD, technical design,
  functional specification, system specification, client specification, product
  discovery, user-needs analysis, or to spec out product behavior or architecture. Do
  not use for delivery sequencing alone; plan-waves-slices owns waves, milestones,
  slices, and implementation order.
---

# Spec Chain

Own the specification chain between governance decisions and delivery planning:

1. CON — user reality first, then product responses that pass the Contextual
   Necessity Test;
2. canonical FSD — what the system must enable users to accomplish;
3. canonical TSD — how accepted behavior is realized;
4. optional client/DOCX exports — derived views, never authority.

Governance owns evidence, decisions, worktree state and stage closure.
`plan-waves-slices` owns delivery order, waves, slices and status.

The philosophy that decides what deserves to become a specification lives in
[references/need-first.md](references/need-first.md). Read it before any CON or FSD
work. Nothing earns its place because it fits the product identity, is technically
possible, already exists, looks impressive or was imagined early.

## Select the mode

- **Governance mode** — consume the supplied Discovery Packet, canonical
  `DECISIONS.md`, output paths and audience profile. Do not repeat archaeology or
  maintain a second decision log.
- **Standalone mode** — inspect the supplied brief and existing chain documents, ask
  only blocking questions, and write a local decision/open-item register until the
  project adopts governance.
- **Revision mode** — preserve stable requirement IDs, state supersession and update
  downstream impact.
- **Export mode** — render canonical Markdown into a derived internal or client DOCX.

Read [references/governance-mode.md](references/governance-mode.md) and
[references/authority.md](references/authority.md) before governance-mode work.
For revisions inside a governed stage, use the supplied impact review and
[controlled-iteration contract](../governance-system/references/controlled-iteration.md).
Re-enter the earliest affected specification responsibility, preserve unaffected
definitions, and revalidate downstream traces. Governance owns contract revision and
reopening; this skill does not approve them or reset delivery status.

## Shared identifiers

- `UR-###` — user or actor in a real context.
- `UN-###` — user need: context, stated request, underlying job, decision, information,
  outcome, evidence class.
- `C-###` — product response proposed for a need, with its Contextual Necessity Test and
  a status of `accepted`, `hypothesis`, `rejected` or `deferred`.
- `D-###` — owner-ratified decisions in canonical `DECISIONS.md`.
- `O-###` — unresolved owner questions and upstream deltas in canonical `DECISIONS.md`.
- `E-###` — non-binding observations.
- `F-###` — functional requirements and acceptance items; each serves UN/C IDs.
- `T-###` — technical design requirements; each realizes F-IDs.
- `RK-###` — specification risks.
- `R-###` — reserved for governance worktree resolutions; never use for risks.

Every UN, C, observation and open item carries one evidence class from
[references/need-first.md](references/need-first.md) §5. Documents display decisions and
risks as referenced views; they do not become independent authorities.

## Workflow

### 1. Read inputs and check authority

Read every supplied source, prior chain document and canonical decision. Identify
scope, audience, budget, constraints, inventory, unresolved O-IDs and superseded
material. Read [references/house-style.md](references/house-style.md).

### 2. Establish user reality

Before proposing any product shape, know who the users are, what they are trying to
accomplish, how they do it today, what makes that hard, what information and actions
matter, which domain constraints apply and which assumptions you are making. Record
stated requests as evidence and derive the underlying job independently. Model
multi-party workflows whole. Tag every finding with an evidence class.

This stage produces CON Part A (UR and UN inventories). For a rebuild, treat the
existing system as evidence, not authority.

### 3. Apply the concept gate

A CON is required for a greenfield product, a substantial rebuild, a major new product
surface, or whenever no accepted user-needs baseline exists. Skip it only when an
equivalent ratified baseline already exists: UR/UN items with context, job and outcome,
plus identifiable authority (a D-ID or a named, ratified source). "Some documentation
exists" does not qualify. When skipped, the FSD carries a `User needs baseline` section
naming that authority.

Read [references/con.md](references/con.md) when the gate opens. CON Part B derives
product responses through Need → Desired outcome → Candidate response → Possible
interaction. Every C passes the Contextual Necessity Test or stays a hypothesis.

### 4. Check blocking decisions

- FSD requires an accepted UN inventory, settled actors, scope and core domain concepts.
- TSD requires every O-ID marked as blocking technical design to be resolved.
- Wave planning requires valid FSD and TSD outputs.

Ask at most two blocking questions per gate, with concrete options and a recommendation.
Record safe reversible assumptions as O-IDs with an expiry; never disguise them as
accepted decisions.

### 5. Write the canonical FSD

Read [references/fsd.md](references/fsd.md). The FSD answers what the system must enable
the user to accomplish. Every FSD includes a role-capability matrix showing all
accepted users/actors and every feature's distinct actions, with access conditions
and F-ID links. Include single-role and headless systems; never invent roles or
permissions to fill the matrix. Keep it consistent with the detailed behavior when
revising requirements. Every item has a stable F-ID, a `Serves` label citing the UN
and accepted C it realizes, and one demonstrable “done when.” Material user
interactions separate the functional requirement from the representation and give a
representation rationale. Do not include topology, frameworks, storage design, source
paths or build order, and do not specify an interaction because it was imagined
upstream: re-test it against the need.

### 6. Write the canonical TSD

Read [references/tdd.md](references/tdd.md). The TSD inherits authority from the FSD and
owns architecture, topology, module boundaries, data models, routes, contracts,
integrations, security implementation, operations, migrations, observability and
technical risks. Prefer the simplest adequate architecture and reversible choices. A
technology cannot create a requirement; a better product possibility discovered here is
surfaced upstream under `Product deltas surfaced`, never absorbed.

### 7. Verify external claims and arithmetic

Read [references/verification.md](references/verification.md) before asserting any
price, tier, version, quota, exchange rate, regulation or platform behavior. Record
source, access date, calculation and conclusion. Convert anything unverified into an
O-ID, RK-ID or named verification task.

### 8. Validate the chain

Keep the generated policy marker consistent with the project's existing authority;
never upgrade an existing project by copying a newer template. See
[policy compatibility](../governance-system/references/policy-compatibility.md).

For an explicitly requested policy-2 readiness preview, read
[references/graph-validation.md](references/graph-validation.md). It explains definition
and edge checks, NFR tracing, and why a clean graph is not release readiness or acceptance.

Run:

```bash
python3 scripts/validate_spec.py --repo <repository> --project <slug> --mode <governance-or-standalone>
python3 scripts/trace_chain.py --repo <repository> --project <slug>
```

The validator enforces structure: role/action matrix coverage, known IDs, required
labels, accepted-only `Serves` references, representation rationale where the
interaction is material, and complete traceability. `trace_chain.py` walks every
accepted F and T backward to a user and an
outcome; a break is an unjustified assumption. Warnings mark accepted responses that
rest on assumptions or preferences. Repair errors before handing the chain to
`plan-waves-slices`.

### 9. Export only when requested

Canonical Markdown remains the Git-reviewable source. Generate DOCX with:

```bash
node scripts/render_docx.js --input <canonical-markdown> --profile <internal-or-client> --output <derived-docx> --verify
```

`--verify` renders the DOCX to PDF and page images. Inspect the result and report
unverified visual behavior. Export failures never change canonical Markdown.

## Quality rules

- Completeness is inventory coverage, not page count.
- Use one fixed schema per item and never silently skip labels.
- Lead with flags that change action; state consequence and recommendation.
- Use requirement strength consistently: must, should, may, deferred.
- Separate the stated request from the underlying job; separate function from
  representation; separate need from response.
- Never promote an assumption, preference or hypothesis into a requirement by writing
  confidently; keep its evidence class visible.
- Product identity may shape presentation, never justify functionality.
- Simplest complete solution: remove unjustified complexity, not required capability.
- Client exports contain no technology, provider, source path or implementation detail.
- Every deferred item states what must remain cheap or possible now.
- Every risk has a concrete response or fallback.
- Every acceptance statement is observable.

## Failure policy

- Missing user reality, missing blocking intent, unresolved TSD gates, WHAT/HOW
  leakage, unknown ID references, F items serving non-accepted responses, broken
  backward traces and failed validation stop downstream planning.
- Downstream discoveries that change product meaning, user-visible behavior, business
  rules, trust boundaries, acceptance or scope return upstream as O-IDs; smaller
  refinements stay where the work happens.
- Retry deterministic validation once after correcting its reported input.
- Current external facts require verification; do not rely on memory.
- Do not install dependencies implicitly during document generation. Run the documented
  dependency preflight and install only with owner authorization.

## Resources

- [references/need-first.md](references/need-first.md) — the product philosophy
- [references/governance-mode.md](references/governance-mode.md)
- [references/authority.md](references/authority.md)
- [references/con.md](references/con.md)
- [references/fsd.md](references/fsd.md)
- [references/tdd.md](references/tdd.md)
- [references/house-style.md](references/house-style.md)
- [references/verification.md](references/verification.md)
- [references/graph-validation.md](references/graph-validation.md) — policy-2 readiness previews
- [OPERATOR.md](OPERATOR.md)
- `assets/` — canonical Markdown templates and export profiles
- `scripts/validate_spec.py` — chain and traceability validator
- `scripts/trace_chain.py` — backward explainability walker
- `scripts/render_docx.js` — derived Word renderer
- `evals/` and `tests/` — behavior and integration coverage
