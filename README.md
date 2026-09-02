# Agent skills: specification, governance and delivery planning

Three Claude Code / Cursor skills that make **user need** decide what becomes a
specification, and keep every downstream artifact explainable back to a real user in a
real context.

| Skill | Owns |
|---|---|
| [`spec-chain`](spec-chain) | Concept Note, Functional Specification, Technical/System Design, and the traceability between them |
| [`plan-waves-slices`](plan-waves-slices) | Owner-gated waves and reviewable vertical slices |
| [`governance-system`](governance-system) | Discovery, evidence, document authority, canonical worktree state, reconciliation, hooks, validation, handoff |

## The idea

Most specification tooling transcribes requests into requirements. These skills refuse
to. A stated request is treated as *evidence about* a user, never as the requirement
itself: "I need a map" tells you the user is thinking about location, not that a map
belongs in the product.

The philosophy is stated once, in
[`spec-chain/references/need-first.md`](spec-chain/references/need-first.md); the other
two packages cite it rather than restating it. Its central test is that nothing earns
its place in a product because it fits the product identity, is technically possible,
already exists, looks impressive, or was imagined early — only because it materially
helps a user accomplish a real job in the realities of their context.

## The chain

```
evidence -> UR (user) -> UN (need) -> C (product response) -> F (functional contract)
                                                           -> T (technical realization)
                                                           -> slice -> verification
```

- A `UN` separates the **stated request** from the **underlying job**, the decision or
  action it serves, and the information actually required.
- A `C` is a *product response* of any kind — a new capability, exposing information
  that already exists, removing a step, changing a default, changing wording, or
  deliberately doing nothing. Each one must pass a Contextual Necessity Test, and only
  an `accepted` response may be served by a functional requirement.
- Every item carries an evidence class (`fact`, `observed-behavior`,
  `stakeholder-requirement`, `domain-constraint`, `accepted-decision`, `hypothesis`,
  `assumption`, `preference`, `aesthetic-choice`), so a preference can never be
  silently promoted into a requirement.
- Authority flows downstream; corrections flow upstream through recorded deltas.

None of this is enforced by prose alone. It is enforced by validators and behavioral
evals, so the discipline survives contact with an agent in a hurry.

## Install

The three packages must stay siblings — `governancectl` locates the spec-chain and plan
validators relative to its own resolved path.

```bash
git clone https://github.com/NwabuezeChigozirim/agent-skills.git
cd agent-skills
scripts/install.sh                  # symlinks into ~/.cursor/skills and ~/.claude/skills
scripts/install.sh --help           # other layouts, --dry-run, --runtime
```

The DOCX renderer in `spec-chain` needs its dependencies:

```bash
cd spec-chain && npm ci
```

## Verify

```bash
for skill in spec-chain plan-waves-slices governance-system; do
  (cd "$skill" && python3 -m unittest discover -s tests)
done
python3 governance-system/scripts/validate_suite.py --check-symlinks
(cd spec-chain && npm test)
```

105 Python tests and 4 renderer tests. The Python suites and the validators use only the
standard library and Git.

## Validators

| Script | Checks |
|---|---|
| `spec-chain/scripts/validate_spec.py` | CON/FSD/TSD structure, schemas, evidence-class enum, response status, representation rationale, inventory and traceability symmetry. Reports warnings on a separate channel so a structural smell never fails a build |
| `spec-chain/scripts/trace_chain.py` | Walks the backward-explainability invariant and exits non-zero when a chain to a user breaks |
| `plan-waves-slices/scripts/validate_plan.py` | Slice sections and labels, each slice serving an `F` or carrying an infrastructure `Unlocks`, each brief citing a known user need |
| `governance-system/scripts/validate_suite.py` | Package structure, references resolve, the philosophy file exists, each eval file's philosophy pointer resolves |
| `governance-system/scripts/governancectl` | Repository lifecycle, worktree reconciliation, hooks; relays all of the above under `validate` |

Validators are deterministic and structural. Semantic anti-patterns — identity
justifying functionality, technology looking for a use case, form before function,
"MVP" that deletes the core job — are covered by the behavioral eval suites in each
package's `evals/`.
