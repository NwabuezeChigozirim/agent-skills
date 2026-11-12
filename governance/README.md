# governance (v3, in progress)

The rebuild of `governance-system` around one equation: good codebase + good environment
+ verification = work that does not need rechecking. Cursor is the first host.

The existing `governance-system` package is untouched and stays the released version
until this one replaces it. This package breaks compatibility with its policy 1 format.

## What is here now: verification

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

## Planned, in order

1. Rule table and correction ladder (each rule paired with what enforces it)
2. Contract core: restated intent frozen as acceptance, checks that call `verifyctl`, automatic closure on current evidence
3. Independent verifier and adversarial review
4. Claude Code adapter

## Credit

The three skills and the feature-map example are taken from
[pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT, commit
`2eaf465`), with additions that wire them to `verifyctl`. See
`THIRD_PARTY_LICENSE-pstack`.
