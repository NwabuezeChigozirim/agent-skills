# Governance Mode

Governance mode receives canonical inputs and writes final planning paths directly.

## Required inputs

- repository path;
- Discovery Packet;
- canonical root `DECISIONS.md`;
- FSD path;
- TSD path;
- `design.md` path;
- valid F-ID, T-ID, UN-ID and accepted C-ID inventories;
- unresolved non-blocking O-IDs and specification RK-IDs;
- the assumptions most capable of invalidating the product, so early waves can retire them;
- output directory `docs/waves/`.

Validate every path before planning. Reuse discovery evidence and resolved questions.
Require the specification validator to pass. Ask only a newly surfaced planning
blocker.

## Ownership

The planner owns wave boundaries, dependencies, published contract freeze points,
slice order, mandatory tests and exit criteria. It may append ratified planning
decisions to canonical `DECISIONS.md`; it must not rewrite existing decisions.

Wave briefs cite UN-IDs for the job, F-IDs for behavior/acceptance and T-IDs for
implementation constraints. The planner schedules those requirements but never changes
their meaning. Technical dependencies from the TSD are inputs, not a competing work
breakdown. Early waves retire the greatest important product uncertainty per unit of
effort ([need-first.md](../../spec-chain/references/need-first.md)).

The planner writes:

- `docs/waves/README.md`;
- one `docs/waves/wave-N-<slug>.md` per wave;
- `docs/waves/PR-CHECKLIST.md`.

No intermediate WAVES document, duplicate status table, normalization pass or split
step is permitted in governance mode.
