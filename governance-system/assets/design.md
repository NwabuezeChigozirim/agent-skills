# <Project Name> Engineering Guide

This document owns engineering invariants, fixed stack, conventions and Definition of
Done. Behaviour belongs to the FSD, technical shape to the TSD, ratified intent to
`DECISIONS.md`, and mutable wave status to `docs/waves/README.md`.

## Commandments

State only load-bearing invariants. Each invariant names the concrete failure it
prevents and cites a D-ID when owner intent locks it.

1. **<Absolute engineering invariant>.** Prevents: <specific failure>. <D-ID>

## Fixed stack

| Layer | Choice | Substitutable? | Decision |
|---|---|---|---|
| <layer> | <technology> | locked / reviewable | <D-ID or open item> |

## Conventions

### Code and modules

- <naming, dependency direction, typing and error-handling rules>

### Interfaces and contracts

- <versioning, envelope, compatibility and generation rules>

### Product and interface

- Function before form: task → information hierarchy → actions → states → interaction
  model → layout → visual treatment. A representation is chosen per job, not per
  product; the FSD's `Representation rationale` is the authority for material
  interactions.
- A technology or library never creates a behavior; every behavior serves a UN or
  accepted C (`spec-chain/references/need-first.md`).

### Testing

- <runner, test locations, markers, fixtures and coverage gate>

### Git and review

- A slice is one reviewable PR-sized unit; it may contain multiple coherent commits.
- Do not commit, push, merge, rebase or rewrite history without owner authorization.

### Vocabulary

- Enforce approved domain terms in identifiers, interfaces and UI.
- New domain terms require a decision or Lexicon update.

## Definition of Done

- [ ] Required unit, integration and flow tests pass.
- [ ] Coverage gates hold without deleting or skipping tests.
- [ ] Migrations are reversible and verified in an isolated environment.
- [ ] Published contracts are regenerated when changed.
- [ ] Frozen contracts remain unchanged unless a superseding decision authorizes them.
- [ ] Vocabulary and security rules pass.
- [ ] The review unit is reconciled with the canonical worktree.
- [ ] Operational gotchas and test evidence are recorded.

## Conflict policy

Stop for contradictions affecting behaviour, contracts, schema/data, security,
vocabulary, external dependencies, cost, or irreversible choices. Resolve them through
`DECISIONS.md`.

A local assumption may proceed only when it is reversible, cannot alter observable
behaviour or published contracts, introduces no dependency, has an O-ID, and expires
no later than wave sign-off.

## Unsafe attractive ideas

| Tempting idea | Failure caused here | Authority |
|---|---|---|
| <project-specific shortcut> | <concrete failure> | <D-ID or section> |
