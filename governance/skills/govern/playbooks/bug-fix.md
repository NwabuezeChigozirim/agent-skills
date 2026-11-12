### Bug fix

**Be scientific. Every shipped line traces to runtime evidence.** A change that "might help" is a hypothesis, not a fix, and does not ship.

1. Reproduce it yourself on the real app with the `verify-<app>` skill. Record the failing run with `verifyctl record --outcome failed`. If it will not reproduce, tighten conditions or add instrumentation until it does. Ask the owner only after driving it as far as it goes.
2. Find the root cause. Form hypotheses and eliminate them with runtime evidence, taking the split that cuts the most remaining space each pass. Fix the first place the system went wrong, not the symptom.
3. Write the stage contract: the intent is the corrected behavior, the acceptance item is the original repro now passing, with a regression test check and a `verifyctl check --fresh` check, `review: independent`. Ask the owner to run the freeze command.
4. Commit the failing test first, then the smallest fix the evidence justifies.
5. Drive the original repro again on the same surface and seal the passing run. Unit tests show branch behavior, not bug absence.
6. Commit. Run `stagectl run-check --all`, get the independent verdict with the **verify-stage** skill, then `stagectl close`.
7. If this class of bug has happened before, run the **correct** skill so the repo prevents it.

**Reply:** what was broken, the root cause, the fix, and the failing-then-passing repro output verbatim.
