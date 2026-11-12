# governance (v3, in progress)

The rebuild of `governance-system` around one equation: good codebase + good environment
+ verification = work that does not need rechecking. Cursor is the first host.

The existing `governance-system` package is untouched and stays the released version
until this one replaces it. This package breaks compatibility with its policy 1 format.

## What is here now

### Verification

| Piece | What it does |
|---|---|
| `skills/create-verification-skill` | Generates a project-local `verify-<app>` skill: launch, doctor, drive, evidence, cleanup, plus a feature map |
| `skills/maintain-verification-skill` | Re-reads and re-drives every mapped feature and ships proven corrections |
| `skills/principle-prove-it-works` | The rule that done means checked against the real artifact |
| `scripts/verifyctl` | Enforces the above: lints the skill and map, seals proof files by hash, and fails when evidence is missing, changed, or does not cover a feature |

```bash
scripts/verifyctl lint   --skill .cursor/skills/verify-<app>
scripts/verifyctl record --skill ... --run .verify/runs/<id> --feature <id> --entry "<entry point>" --outcome verified --artifact <file>
scripts/verifyctl check  --skill ... --run .verify/runs/<id> --all
```

Exit codes: 0 valid, 2 invalid invocation, 3 validation failed. Standard library only.

`verifyctl` proves the evidence exists, is unchanged since it was recorded, and covers
the requested features. It does not judge whether a screenshot shows the right thing,
and it does not yet check that every entry point a feature file lists was driven.

### Environment: the rule table

| Piece | What it does |
|---|---|
| `skills/correct` | Finds mistakes agents repeat and fixes each at the highest level that works: architecture, types, lint, test, docs last |
| `skills/principle-encode-lessons-in-structure` | The rule that a repeated instruction should become a check |
| `scripts/rulectl` | Reads the `## Rules` table in `AGENTS.md` and fails when a rule cites no existing enforcer, a docs-only rule gives no reason, or docs-only rules exceed a limit |

```bash
scripts/rulectl check --repo . --max-docs 3
```

`rulectl` proves a rule points at a real enforcement file. It does not run that
enforcer or confirm it would catch the mistake; `/correct` requires showing each new
check failing on a real past mistake.

## Planned, in order

1. Contract core: restated intent frozen as acceptance, checks that call `verifyctl`, automatic closure on current evidence
2. Independent verifier and adversarial review
3. Claude Code adapter

## Credit

The five skills and the feature-map example are taken from
[pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT, commit
`2eaf465`), with additions that wire them to `verifyctl` and `rulectl`. See
`THIRD_PARTY_LICENSE-pstack`.
