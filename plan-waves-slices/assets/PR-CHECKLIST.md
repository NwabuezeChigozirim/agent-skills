# Planning Review Checklist

Apply this checklist to every reviewable slice.

## Scope and authority

- [ ] The change belongs to an approved in-progress wave.
- [ ] The slice maps to one reviewable vertical behavior.
- [ ] Decision, FSD and TSD references are current.
- [ ] No unresolved worktree resolution affects touched paths.

## Tests

- [ ] Required unit tests pass.
- [ ] Required integration or flow tests pass.
- [ ] Coverage gates hold without skipped or deleted tests.
- [ ] Test commands and results are recorded.

## Data and contracts

- [ ] Migrations are reversible and tested in isolation.
- [ ] Generated contracts are updated with source changes.
- [ ] Frozen contracts are unchanged, or a superseding owner decision is cited.
- [ ] No destructive data operation lacks explicit approval.

## Safety and quality

- [ ] Domain vocabulary and project conventions are followed.
- [ ] No credentials, secret values or local environment files are committed.
- [ ] Security-sensitive behavior has appropriate tests.
- [ ] Operational gotchas and unfinished work are recorded.

## Review boundary

- [ ] The slice is one coherent PR-sized review unit.
- [ ] Commit, push, merge and history-rewrite actions were performed only when the
      owner separately authorized them.
