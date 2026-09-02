# Governance Mode Contract

## Required inputs

- repository and canonical worktree path;
- Discovery Packet path, including classed notes about user reality where governance
  collected them;
- canonical root `DECISIONS.md`;
- project slug and authoritative output paths;
- audience profile: internal, client, or both;
- existing CON/FSD/TSD paths when revising;
- for a rebuild: the existing system's location, treated as evidence;
- verified command and dependency context.

Validate all inputs before writing. Reuse discovery evidence and owner answers. Ask only
a newly surfaced blocking specification question.

## Direct outputs

- `docs/<slug>-CON.md` — required for greenfield, substantial rebuild, major new surface,
  or when no ratified user-needs baseline exists; otherwise the FSD names the baseline;
- `docs/<slug>-FSD.md`;
- `docs/<slug>-TSD.md`;
- optional derived files under `docs/exports/`.

Do not create a second decision log, wave plan, milestone plan, handoff log or mutable
status table. Upstream deltas discovered while writing are proposed to governance as
O-IDs with `Raised by` set to the artifact; spec-chain does not ratify them.

## Handoff to planning

Provide `plan-waves-slices` with:

- canonical CON, FSD and TSD paths;
- UR/UN inventory and accepted C-IDs with their evidence classes;
- valid F-IDs and T-IDs with their `Serves` links;
- unresolved non-blocking O-IDs;
- dependency and contract constraints;
- RK-IDs that affect sequencing or acceptance;
- the assumptions most capable of invalidating the product, so early waves can retire
  them.

Wave planning must stop if the validator or `trace_chain.py` reports errors or if a
blocking O-ID remains open.
