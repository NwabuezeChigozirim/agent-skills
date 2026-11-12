### Feature

**You own the design and the proof.**

1. Read how the affected subsystem works today, from the code and the feature map. Name the data shape the feature needs before any logic.
2. Write the stage contract: your restated intent, one acceptance item per observable outcome, a test check and a `verifyctl check --fresh` check for each touched feature, `review: independent`. Add or update the feature's file in the map now, so the journey exists before the code.
3. Show the owner the contract and ask them to run the freeze command.
4. Build in small units. Each unit ends with its tests passing before the next begins.
5. Drive the real app through every entry point the feature file lists. Seal the evidence with `verifyctl record`.
6. Commit everything. Run `stagectl run-check --all`.
7. Hand the stage ID and commit to a fresh agent with the **verify-stage** skill. On `fail`, fix the root cause and repeat from step 5.
8. Run `stagectl close`. Open the pull request with the intent, the receipt and the verdict in its description.

**Reply:** what you built, what you chose and why, the receipt, the verdict, open decisions.
