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

### Flow: the stage contract

| Piece | What it does |
|---|---|
| `skills/stage` | The working loop: restate the intent, freeze it with checks after the owner approves, do the work, prove it, close |
| `skills/in-your-own-words`, `skills/principle-sequence-verifiable-units` | Restating the goal, and splitting work into units that each end in a check |
| `scripts/stagectl` | Freezes the contract, runs its checks, and binds each receipt to the exact code tested. `close` needs no owner flag: it succeeds only when every receipt is current |

```bash
scripts/stagectl --repo . freeze --contract stage.json --owner-approved
scripts/stagectl --repo . run-check --all
scripts/stagectl --repo . close
```

### Independent verdict

| Piece | What it does |
|---|---|
| `skills/verify-stage` | A second agent checks out the exact commit in its own worktree, drives the app itself, tries to break it, and records PASS or FAIL |
| `skills/interrogate`, `skills/arena` | pstack's adversarial review: several agents try to break a change, and only findings proven by a run survive |
| `stagectl verify` | Refuses the author's worktree, requires the verifier's checkout to match the author's code exactly, and reruns every frozen check there. A contract with `"review": "independent"` cannot close without a passing verdict on the current code |

```bash
scripts/stagectl --repo ../verifier-worktree verify --stage ST-... --outcome pass --summary "..."
```

This separates checkouts, not identities: it proves the work was committed and passes
in a clean tree, and it cannot prove a different agent ran the command.

Ported from `governance-system/scripts/stage_contracts.py`, without policy versions,
approval-record files, discovery notes or impact review. The owner approves once at
freeze and again only for a revision. There is one stage per worktree, so agents in
separate worktrees run in parallel. `verifyctl check --fresh` ties recorded evidence to
the current code, so a stage cannot close on proof gathered before the last edit.

Limits: `--owner-approved` is an attestation, not authentication. A passing check does
not prove the check covers its acceptance item. Environment, services and toolchain
versions are not part of the fingerprint. Reopening a closed stage is not implemented.
State is local to the machine (`<git-common-dir>/governance-v3/`); Linux and macOS only.

### Entry point, hooks and install

| Piece | What it does |
|---|---|
| `skills/govern` | The starting command. Restates the goal, matches the task to a playbook (feature, bug fix, refactor, investigation), and runs it as a stage. Modeled on pstack's `/poteto-mode` |
| `hooks/guard.py` | Blocks an agent from recording owner approval or touching stage records. While a stage is active, blocks destructive or unclassified Git commands. At the end of a turn, sends the agent back once if the stage is still unproven |
| `hooks/hook_policy.py` | The Git command classifier, copied unchanged from `governance-system` |

Install for Cursor as a local plugin (skills, hooks and scripts together):

```bash
scripts/install.sh        # from the repository root; also links ~/.cursor/plugins/local/governance
```

Then start a task with `/govern <what you want>`.

The hooks follow the layout other Cursor plugins use (`hooks/hooks.json`,
`${CURSOR_PLUGIN_ROOT}`); pstack itself ships none. They are tested by feeding payloads
to the script, not inside a running Cursor, so the exact payload fields and the
`loop_limit` behavior are unconfirmed there. The guard is a guardrail, not a sandbox: a
command that hides `--owner-approved` behind a script or variable is not caught. A
cloud agent with no human at a terminal has no way to obtain the freeze approval yet.

## Planned, in order

1. Trial inside Cursor on a real project
2. Claude Code adapter

## Credit

Nine skills and the feature-map example are taken from
[pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT, commit
`2eaf465`), with additions that wire them to `verifyctl` and `rulectl`. See
`THIRD_PARTY_LICENSE-pstack`.
