# Discovery Packet

The Discovery Packet is the single exploration handoff shared with planning.

## Required fields

- repository identity and canonical worktree;
- greenfield, brownfield, or mixed mode;
- plan/intent sources;
- stack, package tooling, CI, commands, tests, coverage and migrations;
- module boundaries and dependency direction;
- contracts and external integrations;
- current state and target state;
- existing governance artifacts and authority conflicts;
- observations, hypotheses, owner questions and blocking items;
- timestamp and evidence paths.

## Recording findings

`discover` fills the mechanical fields (identity, mode, worktrees, intent sources). Every
other finding is recorded with the runtime so hook-driven rediscovery cannot erase it:

```bash
governancectl --repo . note --kind observation --provenance code \
  --evidence src/app/config.py --evidence-class observed-behavior \
  --text "Settings load from environment only"
governancectl --repo . note --kind hypothesis --evidence-class hypothesis \
  --text "The legacy exporter is unused"
governancectl --repo . note --kind needs-owner --text "Target hosting platform"
governancectl --repo . note --kind blocking --text "Data retention period shapes schema"
```

Notes receive stable `N-###` IDs, live in `<git-common-dir>/governance/discovery-notes.json`,
and are merged into `discovery.json` on every `discover`. Do not hand-edit
`discovery.json`.

Under explicit stage contracts, `blocking` and `needs-owner` notes gate checks and
closure until `resolve-note --id N-### --decision D-### --note TEXT --owner-approved`
records their owner-ratified resolution. This preserves the original finding and its
evidence class, and decision-row changes reopen the obligation. See
[stage-contracts.md](stage-contracts.md); a phase transition or passing test is not a
resolution, and default legacy runs do not silently adopt these new gates.

## Provenance

- `code` — read from source or config; cite a path.
- `test` — demonstrated by a test; cite a path and command.
- `ci` — read from CI configuration; cite a path.
- `git` — derived from history; cite a commit or range.
- `owner` — stated or ratified by the owner.
- `hypothesis` — plausible inference, not binding.
- `needs-owner` — intent cannot be derived.

## Evidence class

Provenance says where a note came from; the evidence class says how much weight it can
bear. Every note carries one of `fact`, `observed-behavior`, `stakeholder-requirement`,
`domain-constraint`, `accepted-decision`, `hypothesis`, `assumption`, `preference`,
`aesthetic-choice` (defined in `../../spec-chain/references/need-first.md` §5). The
class travels into `DECISIONS.md` Observations and into CON/FSD items unchanged;
downstream prose never upgrades it.

Observations describe reality. They do not become binding engineering or product
decisions merely because the current code behaves that way. In a rebuild the existing
system is evidence (`observed-behavior`, `domain-constraint`, `fact`); its screens,
navigation, workflows, identity and architecture are candidates that must re-earn their
place through the CON, not requirements.

## Question budget

Ask individually only when a choice is intent-dependent, irreversible, expensive,
security-sensitive, data-shaping, contract-shaping, or blocks the next artifact.

Group safe reversible defaults by theme and ask the owner to confirm or edit the bundle.
Do not ask the owner to restate evidence already established from the repository.
