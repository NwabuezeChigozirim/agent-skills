# Source Conflict Policy

Classify a contradiction before deciding whether work may continue.

## Blocking conflicts

Stop work on the affected scope and obtain an owner decision when the conflict changes:

- product behaviour or acceptance;
- a published or frozen contract;
- schema, migration, retained data or destructive behavior;
- authentication, authorization, secrets or security posture;
- external services, deployment topology or recurring cost;
- domain vocabulary used in identifiers;
- an irreversible or expensive implementation direction;
- product identity versus user utility: when "we are X-first", a design language or a
  legacy screen conflicts with what evidence says users need, utility wins unless the
  owner records a decision stating the strategic reason and its cost.

Record the resolution as a new decision. Existing decisions are superseded, never
silently edited.

## Upstream deltas

Corrections flow against authority: an FSD that finds the CON wrong, a TSD that finds
a product-behavior problem, or an implementation that finds a faulty assumption raises
an O-ID with `Raised by` naming the artifact, and the affected work pauses. Only changes
to product meaning, user-visible behavior, business rules, trust or privacy boundaries,
acceptance semantics, programme scope or major ordering need this; smaller refinements
stay where the work happens. A downstream document never repairs an upstream one
silently, and a technology never creates a requirement.
Use [controlled iteration](controlled-iteration.md) to compare the old agreement and
current artifacts, route affected work back to its owner, and approve a linked stage
revision. An affected ID is a review candidate, not proof that its implementation must
change. Explicitly account for removed obligations; never carry old check evidence or
sign-off into the revised agreement.

## Reversible local assumptions

A small implementation detail may proceed only when it is local, reversible, does not
change observable behaviour or contracts, and does not create a new dependency.

Record:

- the assumption;
- the affected path;
- why it is reversible;
- the review deadline, no later than wave sign-off;
- the open-item ID.

If any condition is uncertain, treat the conflict as blocking.

## Authority order

Ratified decisions override downstream prose. FSD owns behaviour. TSD owns technical
shape. `design.md` owns engineering rules. Code and tests are evidence of current
reality, not automatic proof of intended future behaviour.
