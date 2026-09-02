# Slice Semantics

A slice is one reviewable, PR-sized vertical increment inside a wave. It is not
required to be one Git commit. Prefer **user-value vertical slices** that prove a
meaningful part of the user's workflow end-to-end.

Each slice uses every label:

- **Outcome** — the user or system outcome this slice delivers
- **Serves** — F-IDs, and UN-IDs where helpful
- **Why** — why this slice exists now
- **Usable when done** — what becomes usable or verifiable
- **Depends on** — earlier slices, or none
- **Tests** — unit and integration/flow, with a reason when none apply
- **Acceptance evidence** — what will be recorded

Infrastructure-only slices are valid when genuinely prerequisite. They carry
`Kind: infrastructure` and **Unlocks** naming the F-ID they make possible. They are
not a substitute for an end-to-end slice when one is possible. A wave whose every
slice is infrastructure demonstrates no end-to-end outcome; `validate_plan.py` warns
rather than fails, because a genuinely foundational wave can be the right call.

Anti-patterns: backend-first, frontend-first, design-system, database or file-by-file
phases when an end-to-end slice is possible; visually demonstrable slices that do not
satisfy the underlying job; an "MVP" slice that removes behavior the primary job
needs ([need-first.md](../../spec-chain/references/need-first.md) §8).

Order work foundation → core → wiring → smoke only inside a vertical outcome, not as
horizontal phases. Establish a minimal test harness first when no runnable harness
exists.

A slice must satisfy the project Definition of Done before landing. Planning may
recommend a PR boundary but never authorizes commits, pushes or merges.
