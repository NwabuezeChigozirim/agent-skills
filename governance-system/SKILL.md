---
name: governance-system
description: >
  Install, resume, audit, repair, reconcile, or hand off an agent-governance system
  for a greenfield or brownfield repository. Use when the user asks for governance
  docs, cold handoff, CLAUDE.md or AGENTS.md setup, multi-agent worktree resolution,
  canonical project state, governance hooks, or agent-ready repository onboarding.
---

# Governance System

Operate the repository through one owner-controlled governance lifecycle. The skill
owns discovery, evidence, document authority, canonical worktree state, reconciliation,
hook installation, validation, and handoff. It delegates delivery decomposition to
`plan-waves-slices`; it never re-derives waves or slices.

## Runtime

Locate this skill directory, then use:

```bash
python3 scripts/governancectl --repo <repository> <command>
```

Run `doctor` before installation and `status` before resuming. The runtime uses only
Python's standard library and Git. Read [references/runtime.md](references/runtime.md)
for command and exit-code contracts.

For audit requests, run `audit` and report; do not enter the mutating workflow below.
For upgrades, preview with `upgrade --dry-run` and apply only with explicit project
authorization. Read [references/policy-compatibility.md](references/policy-compatibility.md)
for policy selection, release gates and metadata-only migration.

## Select one lifecycle mode

Detect the mode; ask only when evidence is ambiguous.

- **install** — no governance marker exists.
- **resume** — an active run exists in Git's shared common directory.
- **update** — governance is installed and its version is older.
- **repair** — validators report structural drift or missing artifacts.
- **audit** — inspect and report without modifying repository files.
- **handoff** — reconcile reality, close the active stage, and prepare the next owner.

Read [references/lifecycle.md](references/lifecycle.md) before acting.

For an explicitly opted-in stage contract, read
[references/stage-contracts.md](references/stage-contracts.md) before the bounded work
begins. Freeze the approved scope, inputs and checks first; governance does not re-plan.
`phase` is progress state, not completion. Policy-1 runs without opt-in retain legacy
behavior; policy 2 remains unreleased.

## Mandatory workflow

### 1. Preflight and canonical state

1. For authorized install/resume/repair work, run `doctor`, then `discover`. Audit
   and upgrade previews never run `discover` or `reconcile`.
2. Inventory every local worktree before writing.
3. Confirm the canonical worktree, branch, and HEAD recorded by the runtime. It defaults
   to the main worktree; change it with `set-canonical --path` only on owner instruction.
4. In install mode, set `project_slug` in `.governance/config.json` when the
   specification files will not be named after the repository directory.
5. If another worktree has overlapping dirty paths or is ahead of canonical, run
   `reconcile` and stop at the owner-resolution gate. Never overwrite, stash, reset,
   delete, or merge a variant.

Read [references/resolution-policy.md](references/resolution-policy.md) for conflict
classes and closure rules.

Review is content-bound: an R-ID approves only its captured version. Reconcile after
changes; never reuse a retired choice for new content. Read
[references/recovery.md](references/recovery.md) when recovery is incomplete or needed.
Excluded content requires an explicit owner-attested backup, not a generic “snapshotted”
claim; unknown current worktree contents cannot be waived.

### 2. Build one Discovery Packet

Explore the code, Git history, CI, existing docs, commands, tests, modules, contracts,
integrations, and current-vs-target state once. Record every finding with
`governancectl note --kind ... --evidence-class ... --text ...`; `discover` merges notes
into the packet and hook-driven rediscovery cannot erase them. Record phase transitions
with `governancectl phase NAME`.

- Evidence read from code/config/CI is an observation, not a binding decision.
- Inferences stay hypotheses; every note carries an evidence class.
- Product intent, scope, irreversible choices, and expensive choices require owner
  ratification.
- For product work, user reality (who the users are, their jobs, context and desired
  outcomes) is discovered through `spec-chain`'s "Establish user reality" stage and
  recorded in CON Part A, not reconstructed from feature lists. For a rebuild, the
  existing system is evidence, never product authority.

Read [references/discovery.md](references/discovery.md) for provenance and question
budget rules, and `../spec-chain/references/need-first.md` for the product philosophy
every artifact in this repository enforces.

### 3. Ratify blocking intent

Ask only questions that are blocking, intent-dependent, irreversible, expensive, or
contract-shaping. Bundle safe reversible defaults into one confirm-or-edit review.
Write accepted intent to canonical `DECISIONS.md`; never assign D-IDs to observations
or unratified hypotheses. Product identity ("we are X-first") is a preference or
hypothesis until user evidence or an explicit, costed decision makes it more; it never
justifies functionality on its own.

### 4. Delegate canonical specifications before delivery planning

Generate in this order:

1. `DECISIONS.md`
2. CON through `spec-chain` — required for a greenfield product, a substantial rebuild,
   a major new surface, or whenever no ratified user-needs baseline exists
3. canonical FSD through `spec-chain`
4. canonical TSD through `spec-chain`
5. `design.md`
6. optional Lexicon when domain vocabulary must be enforced

Invoke `spec-chain` in governance mode with the Discovery Packet, canonical decisions,
audience, existing specification paths, and required direct outputs. It owns user
reality, product responses, FSD behavior and TSD technical shape; it does not own
decisions, worktrees, waves, or status. Require its validator and `trace_chain.py` to
pass before planning. Downstream discoveries that change product meaning, user-visible
behavior, business rules, trust boundaries, acceptance or scope come back as O-IDs with
`Raised by` set; do not let a newer document redefine an older authority.

Use governance assets for `design.md` and adapters. Read
[references/artifact-authority.md](references/artifact-authority.md) for role ownership
and [references/conflict-policy.md](references/conflict-policy.md) when sources disagree.

### 5. Delegate planning

Invoke `plan-waves-slices` in **governance mode** with:

- repository path;
- Discovery Packet path;
- canonical `DECISIONS.md`;
- validated CON, FSD, TSD, and design paths;
- UN-IDs and accepted C-IDs, functional F-IDs, technical T-IDs, open non-blocking
  O-IDs, RK-IDs, and the assumptions most capable of invalidating the product;
- required direct-output root: `docs/waves/`.

The planning skill writes the wave index, one brief per wave, and the PR checklist
directly. It schedules requirements but never redefines specifications. Do not
normalize, split, move, or rewrite its output.

### 6. Complete operational artifacts

Generate `Implementations.md`, the canonical agent hub, platform adapter pointers, and
human `README.md`. `docs/waves/README.md` is the only mutable wave-status authority;
other documents link to it instead of copying its table.

### 7. Install hooks only with project opt-in

Run `install-hooks` only when the owner requested hooks or accepted governance
installation. Preserve unrelated Cursor and Claude Code hook configuration.
Hooks are no-ops unless `.governance/config.json` enables them. The Stop hook only
warns; it never blocks a turn. Closure is gated by `close-stage` alone.

Read [references/hooks.md](references/hooks.md) before installation.

### 8. Validate and close

Run `governancectl validate`; it runs the specification and planning validators itself
once their documents exist. Repair all errors. A stage closes only when:

- all local worktrees were rescanned;
- current versions have intact recovery payloads and retained base commits; incomplete
  coverage has an available, unchanged owner-attested backup;
- no blocking or pending resolution remains (adopt/combine/return-to-agent stay
  pending until the variant is actually gone);
- generated governance and planning documents validate;
- canonical FSD/TSD validate and no blocking specification O-ID remains;
- tests required by the stage are recorded;
- the owner explicitly approves closure.

Run `close-stage`; do not simulate closure by editing state files.
Contracted closure additionally requires current successful `run-check` receipts and
`--approval-ref` for the owner's actual sign-off. Resolve blocking/needs-owner N-IDs
through `resolve-note` with a ratified D-ID. Changed frozen inputs require owner review
and explicit cancellation/replacement, never silent reinterpretation of the contract.

## Failure policy

- Retry a deterministic command once only when the failure is transient or the input
  can be corrected from the error.
- Corrupt state, unresolved conflicts, unavailable worktrees, failed validation, or
  missing owner intent are gates, not retry loops.
- Hooks detect and gate. Scripts snapshot and validate. The owner resolves.
- Local tools cannot inspect uncommitted files on remote machines. Require the remote
  completion manifest defined in [references/resolution-policy.md](references/resolution-policy.md).

## Resources

- [references/lifecycle.md](references/lifecycle.md)
- [references/discovery.md](references/discovery.md)
- [references/artifact-authority.md](references/artifact-authority.md)
- [references/conflict-policy.md](references/conflict-policy.md)
- [references/resolution-policy.md](references/resolution-policy.md)
- [references/recovery.md](references/recovery.md)
- [references/stage-contracts.md](references/stage-contracts.md)
- [references/hooks.md](references/hooks.md)
- [references/runtime.md](references/runtime.md)
- [OPERATOR.md](OPERATOR.md) — command-focused operator guide
- [MIGRATION.md](MIGRATION.md) — updating repositories generated by v1
- `assets/` — files copied into governed repositories
- `scripts/` — deterministic runtime and validators
- `hooks/` — Cursor and Claude Code project adapters
- `evals/` — trigger and end-to-end scenarios
