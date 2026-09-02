# <Project Name> Agent Guide

This is the platform-neutral cold-start map. Engineering rules live in
[design.md](design.md); ratified intent lives in [DECISIONS.md](DECISIONS.md).

## Start every session

1. Run `governancectl status`, then `governancectl discover`.
2. Confirm the canonical worktree, branch, HEAD and active stage.
3. If reconciliation reports unresolved R-IDs, stop and obtain owner resolution.
4. Read `design.md`, `DECISIONS.md`, the FSD and TSD.
5. Read [docs/waves/README.md](docs/waves/README.md). Work only inside a wave whose
   approval is recorded as in progress.
6. Read the active wave brief and the operational notes in `Implementations.md`.
7. Run the verified checks relevant to the requested slice.

## Authority

- `DECISIONS.md` — ratified intent.
- CON — user reality then product responses; recommendations become binding only through decisions.
- FSD — behaviour and acceptance.
- TSD — architecture, data model and contract shape.
- `design.md` — engineering invariants and Definition of Done.
- `docs/waves/README.md` — sole wave-status authority.
- wave briefs — delivery scope, slices, tests and exit criteria.
- `Implementations.md` — shipped reality and operational gotchas.
- `docs/exports/` — derived presentations; never authoritative.

Code, tests, Git and CI are evidence of current reality. They do not silently override
ratified intent.

`spec-chain` owns FSD/TSD authoring. `plan-waves-slices` schedules validated F-IDs and
T-IDs but never rewrites their meaning.

## Worktree rule

Only the worktree declared canonical by `governancectl status` is authoritative at a
stage gate. Other worktrees may contain unfinished variants. Snapshot and resolve them;
never discard, reset, merge or overwrite them automatically.

## Conflict rule

Stop for conflicts affecting behaviour, contracts, schema/data, security, vocabulary,
external services, cost, or irreversible choices. A local reversible assumption may
proceed only when it cannot affect observable behaviour or published contracts, is
recorded as an open item, and expires no later than wave sign-off.

## Product rule

Nothing earns its place because it fits the product identity, is technically possible,
already exists, looks impressive or was imagined early; it earns its place by helping a
real user do a real job in their context (`spec-chain/references/need-first.md`). Every
F serves a UN or accepted C; every T realizes an F; every slice names its outcome. A
downstream discovery that changes product meaning goes upstream as an O-ID, never into
the nearest document. Challenge "I want feature X" with "what job is X for, and is X the
requirement or one response?"

## Handoff

When the owner requests handoff:

1. Reconcile and snapshot every worktree.
2. Verify canonical HEAD and required tests.
3. Update `Implementations.md` with shipped reality and gotchas.
4. Update only the canonical status in `docs/waves/README.md`.
5. Run `governancectl validate`.
6. Close the stage only after explicit owner approval.

## Commands

Record only commands verified safely against the repository or CI:

```bash
<install-command>
<test-command>
<lint-command>
<build-command>
```

Do not run stateful migrations, deployments, service restarts or network publication
merely to prove documentation. Use a dry run or isolated disposable environment.
