# Artifact Authority

Each mutable concern has exactly one authoritative owner.

- `DECISIONS.md` — ratified intent, explicit supersession, classed observations and
  open deltas.
- `docs/<name>-CON.md` — Part A user reality (UR, UN, evidence, non-goals) and Part B
  product responses with their Contextual Necessity Test; required unless a ratified
  user-needs baseline exists. Philosophy: `../../spec-chain/references/need-first.md`.
- `docs/<name>-FSD.md` — product behaviour, actors, states and acceptance; every item
  serves UN/C IDs.
- `docs/<name>-TSD.md` — architecture, data model, integrations and contract shape.
- `design.md` — engineering invariants, fixed stack, conventions and Definition of Done.
- `docs/waves/README.md` — wave status and approval evidence.
- `docs/waves/wave-N-<slug>.md` — scope, tests, contracts, slices and exit criterion.
- `Implementations.md` — shipped reality, operational gotchas and handoff notes.
- `AGENTS.md` — platform-neutral cold-start map and session protocol.
- `CLAUDE.md` — thin Claude Code pointer to `AGENTS.md`.
- `.cursor/rules/governance.mdc` — thin Cursor pointer to `AGENTS.md`.
- `README.md` — human onboarding and verified quickstart.
- `docs/exports/` — derived presentation files; never authoritative.

## Generation order

1. Evidence and open questions, each with an evidence class.
2. Ratified decisions.
3. User reality and product responses (CON) through `spec-chain`; the gate is skipped
   only for a ratified user-needs baseline.
4. FSD and TSD baselines through `spec-chain`.
5. Engineering design.
6. Waves and slices through `plan-waves-slices`.
7. Operational map and onboarding.

The order prevents wave briefs from citing specifications that do not yet exist.
It is the initial construction order, not an irreversible lifecycle. New evidence may
re-enter an earlier owning activity; review its downstream consumers without regenerating
unaffected artifacts. Frozen impact baselines and revision receipts preserve historical
agreement, not a competing mutable source. See [controlled-iteration.md](controlled-iteration.md).

## Mutable-state rule

Do not copy the wave status table into `AGENTS.md`, `CLAUDE.md`,
`Implementations.md`, or `README.md`. Those files link to the wave index. Snapshots may
state their date and purpose, but cannot claim canonical status.
