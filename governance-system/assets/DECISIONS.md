# <Project Name> Decisions

This is the canonical log of ratified intent. Downstream specifications, design and
wave briefs cite stable D-IDs. A later decision may supersede an earlier decision; past
entries are never silently rewritten or deleted.

## Rules

1. Only owner-ratified intent or an explicitly authoritative source receives a D-ID.
2. Code, tests, Git and CI observations live under Observations until ratified as future
   constraints.
3. Hypotheses and unanswered questions live under Open items.
4. Supersession creates a new D-ID and marks the old entry superseded.
5. Frozen-contract changes require explicit owner approval.

## Decisions

| ID | Date | Decision | Rationale and source | Status |
|---|---|---|---|---|
| D-001 | <YYYY-MM-DD> | <ratified decision> | <owner statement or authoritative spec section> | active |

## Observations

Observations describe current reality and are non-binding until ratified. `Class` is
one of fact, observed-behavior, stakeholder-requirement, domain-constraint,
accepted-decision, hypothesis, assumption, preference, aesthetic-choice; downstream
documents cite it unchanged.

| ID | Observation | Class | Evidence | Ratification |
|---|---|---|---|---|
| E-001 | <current fact or behavior> | <class> | <path, test, CI file, interview or commit> | not requested / pending |

## Open items

Open items include upstream deltas raised by downstream work; `Raised by` names the
artifact (CON, FSD, TSD, wave, implementation) that surfaced the question.

| ID | Question or hypothesis | Raised by | Why it matters | Blocks | Proposed reversible default |
|---|---|---|---|---|---|
| O-001 | <owner question> | <artifact or owner> | <impact> | <wave or artifact> | <default or none> |
