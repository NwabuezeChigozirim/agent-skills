### Refactor

**Behavior must not change. Prove that it did not.**

1. State the structural goal and what stays identical for users. Remove dead code first, then reshape the simpler base.
2. Before touching code, drive every feature the change could affect and seal the run. This is the baseline.
3. Write the stage contract: the acceptance items are "the existing tests pass unchanged" and "each affected feature behaves as in the baseline", with `verifyctl check --fresh` checks. Use `review: independent` unless nothing a user can reach is touched; say why if you choose `none`. Ask the owner to run the freeze command.
4. Refactor in small steps, tests green after each. Do not edit a test to make it pass; a test that needs editing means behavior changed.
5. Drive the same features again and seal the run. Compare against the baseline.
6. Commit. Run `stagectl run-check --all`, get the verdict when required, then `stagectl close`.

**Reply:** what moved and why, what you deleted, the evidence that behavior is unchanged.
