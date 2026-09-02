# Wave <N> — <Capability>

## Objective

<One demonstrable user or system outcome.>

## Why this wave

<The outcome, and the important uncertainty this wave retires.>

## In scope

- <observable delivery scope>

## Deferred

- <item> → <later wave or backlog O-ID>

## References

- Decisions: <D-IDs>
- User needs: <UN-IDs>
- Behaviour: <F-IDs and FSD sections>
- Technical design: <T-IDs and TSD sections>
- Risks/open items: <RK-IDs and non-blocking O-IDs>

## Published contracts frozen at sign-off

- `<ContractName v1>` — <consumers and compatibility promise>

## Mandatory tests

- <test command or named test group>

## Exit criterion

> <Exactly one owner-demoable statement.>

## Slices

### W<N>-S1 — <name>

- **Outcome:** <user or system outcome>
- **Serves:** <F-IDs, and UN-IDs where helpful>
- **Why:** <why this slice exists now>
- **Usable when done:** <what becomes usable or verifiable>
- **Depends on:** <earlier slices or none>
- **Tests:** <unit and integration/flow, or reason none apply>
- **Acceptance evidence:** <what will be recorded>

### W<N>-S2 — <infrastructure name, if any>

- **Kind:** infrastructure
- **Outcome:** <prerequisite capability>
- **Unlocks:** <F-ID this makes possible>
- **Serves:** <F-ID>
- **Why:** <why this must land before the user-facing slice>
- **Usable when done:** <what later slices can now do>
- **Depends on:** <earlier slices or none>
- **Tests:** <tests>
- **Acceptance evidence:** <what will be recorded>

## Sign-off checklist

- [ ] Every slice satisfies the project Definition of Done.
- [ ] Required tests pass.
- [ ] Published contracts are regenerated and recorded.
- [ ] Exit criterion is demonstrated.
- [ ] Owner sign-off is recorded in `docs/waves/README.md`.
- [ ] The next wave remains gated until separately approved.
