# Wave Semantics

A wave is an owner-gated unit of demonstrable value. Decomposition serves product
learning, not agent convenience. [need-first.md](../../spec-chain/references/need-first.md)
governs what a wave is allowed to prove.

## Governing rule

Early waves retire the greatest important product uncertainty per unit of
implementation effort. Typical priorities, as guidance not sequence:

1. fundamental user/job uncertainty;
2. dangerous domain assumptions;
3. trust and integrity risks;
4. architecture decisions that are difficult to reverse;
5. the smallest complete workflow capable of validating real utility.

Foundational work is allowed when it is genuinely prerequisite. Visual identity,
animation, elaborate design systems and sophisticated interaction metaphors are not
prioritized before workflow utility is proven. The target is the simplest complete
solution, not the smallest amount of software.

Each wave has:

- one capability objective stated as a user or system outcome;
- explicit in-scope and deferred scope;
- specification and decision references, including UN-IDs;
- named published contracts that freeze at sign-off;
- mandatory tests;
- exactly one owner-demoable exit criterion;
- a sign-off checklist;
- a `Why this wave` statement: the outcome and the uncertainty it retires.

Every wave starts gated. Completion never authorizes the next wave; the owner must
explicitly approve each transition.

Published contracts freeze at wave sign-off. Internal implementation details do not
freeze unless named as consumed contracts. Changing a frozen contract requires owner
approval and a superseding decision.

Waves are sequential by default. Parallel work is safe only when both tracks consume,
but do not modify, a dependency already frozen by an earlier signed-off wave.

Split a proposed wave when it spans three or more independent subsystems, has multiple
demo outcomes, cannot name one exit criterion, or mixes foundation work with an
unrelated product capability.
