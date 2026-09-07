---
name: plan-waves-slices
description: >
  Decompose a plan, specification, roadmap, or existing codebase into owner-gated
  waves and reviewable vertical slices. Use when the user asks for waves and slices,
  delivery sequencing, phased implementation, build milestones, MVP ordering, or a
  wave plan. Supports standalone planning and governance-system direct-output mode.
---

# Plan Waves and Slices

Own delivery decomposition only: planning decisions, waves, slices, dependency order,
contract boundaries, tests, and exit criteria. Do not create the surrounding governance
system or duplicate discovery supplied by `governance-system`.

## Select the mode

- **Standalone mode** — no valid Discovery Packet was supplied. Perform the focused
  exploration in [references/standalone-discovery.md](references/standalone-discovery.md).
- **Governance mode** — consume the supplied Discovery Packet, canonical decisions,
  validated FSD/TSD from `spec-chain`, and the design guide. Do not repeat archaeology,
  rewrite specifications, or ask questions already answered by those sources.

Read [references/governance-mode.md](references/governance-mode.md) for the input and
direct-output contract.
For revised inputs in a governed stage, read
[controlled iteration](../governance-system/references/controlled-iteration.md).
Review affected slices, dependencies and exit criteria against the revised validated
specifications. Preserve stable slice IDs and unaffected decisions; send specification
defects upstream. Impact is a review request, not automatic replanning or approval.

## Planning workflow

### 1. Validate inputs

Identify the plan source, repository mode, target outcome, canonical decision source,
test commands, existing contracts, F-ID/T-ID inventories, and unresolved blockers. In
governance mode, stop if the Discovery Packet, canonical decision log, FSD, TSD, or
their validation evidence is missing or structurally invalid.

### 2. Resolve only planning blockers

Ask only questions whose answers change scope, dependency order, contracts, acceptance,
or release risk. Derived facts require no question. Bundle reversible defaults into a
single confirm-or-edit review.

Write accepted planning intent to the canonical decision log. Accepted choices are
binding; provisional recommendations remain open items. Never write “accepted, confirm
in implementation.”

Read [references/decision-intake.md](references/decision-intake.md).

### 3. Design waves

Apply [references/wave-semantics.md](references/wave-semantics.md):

- one demonstrable capability per wave, stated as a user or system outcome;
- `Why this wave`: the outcome and the uncertainty it retires;
- exactly one owner-demoable exit criterion;
- explicit in-scope and deferred scope;
- named published contracts;
- cited UN-IDs for the job, F-IDs for behavior and T-IDs for technical constraints;
- mandatory tests;
- owner approval before starting every wave;
- sequential order unless all shared dependencies are already frozen;
- early waves retire the greatest important product uncertainty per unit of effort.

Split a wave that touches three or more independent subsystems or cannot be demonstrated
through one coherent exit criterion. Do not spend early waves on visual identity while
workflow utility is unproven.

### 4. Design slices

Apply [references/slice-semantics.md](references/slice-semantics.md). A slice is one
reviewable vertical PR-sized unit that proves a meaningful part of the user's workflow
end-to-end. Each slice names Outcome, Serves, Why, Usable when done, Depends on, Tests
and Acceptance evidence. Infrastructure slices are allowed only with `Unlocks` naming
an F-ID. Do not create commits unless the owner separately authorizes Git mutation.

### 5. Write direct output

In governance mode write:

- `docs/waves/README.md` — sole status authority and gating rules;
- `docs/waves/wave-N-<slug>.md` — one complete brief per wave;
- `docs/waves/PR-CHECKLIST.md` — shared review checklist.

In standalone mode write:

- `docs/<plan-name>-DECISIONS.md`;
- `docs/<plan-name>-WAVES.md`;
- `docs/<plan-name>-PR-CHECKLIST.md`.

Use assets from `assets/`. Do not emit a second mutable wave-status table outside the
mode's canonical output. Schedule specification requirements without changing their
meaning; any discovered specification defect returns to `spec-chain`.

### 6. Validate and stop

Keep standalone policy metadata consistent with the existing project. Validation
accepts `--policy auto|legacy|current`; choosing a preview never adopts a new policy.
Read [policy compatibility](../governance-system/references/policy-compatibility.md)
when auditing or updating an existing plan.

For an explicitly requested policy-2 readiness preview, read
[references/graph-validation.md](references/graph-validation.md). Graph checks cover
membership, dependency order and recorded approval references; they never authenticate
owner approval or authorize implementation. Legacy policy remains unchanged.

Run:

```bash
python3 scripts/validate_plan.py --repo <repository> --mode <standalone-or-governance>
```

Repair validation errors, summarize the wave count and open items, and stop. Planning
never authorizes implementation. Wave 1 remains gated until the owner explicitly says
“go.”
On revision, newly proposed or reopened work needs fresh approval; do not reset every
unaffected wave or carry stale sign-off forward merely because its ID is unchanged.

## Failure policy

- Missing intent, conflicting binding decisions, unresolved contract ownership, and
  failed validation are hard planning gates.
- Retry deterministic validation once after correcting reported input; otherwise stop
  with the exact blocker.
- Never infer product intent from abandoned code.
- Never silently drop deferred work; assign it an open-item or backlog reference.
- Never schedule a visually impressive slice that does not satisfy the underlying job,
  or an "MVP" that removes core-job behavior.

## Resources

- [references/governance-mode.md](references/governance-mode.md)
- [references/standalone-discovery.md](references/standalone-discovery.md)
- [references/decision-intake.md](references/decision-intake.md)
- [references/wave-semantics.md](references/wave-semantics.md)
- [references/slice-semantics.md](references/slice-semantics.md)
- [references/graph-validation.md](references/graph-validation.md) — policy-2 readiness previews
- `../spec-chain/references/need-first.md` — what deserves to be scheduled
- `assets/` — copyable planning documents
- `scripts/validate_plan.py` — deterministic structural validator
- `evals/` — trigger and planning scenarios
