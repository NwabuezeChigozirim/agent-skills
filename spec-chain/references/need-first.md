# Need First

The single statement of the suite's product philosophy. Other skills cite this file;
they do not restate it. Before asking whether an implementation matches its
specification, ask whether the thing deserved to become a specification at all.

## Contents
1. The hierarchy and the biases
2. The reasoning questions
3. Request versus job
4. Product responses (C) and the Contextual Necessity Test
5. Evidence classes
6. Product identity is not specification authority
7. Function before form; contextual interfaces
8. Simplest complete solution
9. Rebuilding an existing system
10. Controlled upstream deltas
11. The backward-explainability invariant
12. Anti-patterns as review questions
13. Agent posture

---

## 1. The hierarchy and the biases

Reason in this order, and let each step constrain the next:

```
user need → user job → required information → appropriate interaction
→ business or domain rule → system behavior → interface → visual treatment
```

Bias every exploration toward:

- user need before product identity;
- function before form;
- contextual usefulness before interface convention;
- clarity before novelty;
- the simplest interaction that satisfies the need before a richer one;
- domain reality before generic software or marketplace patterns;
- evidence and explicit reasoning before founder or agent assumptions.

The highest-order test: nothing earns its place in the product because it fits the
product identity, is technically possible, already exists, looks impressive, or was
imagined early. It earns its place by materially helping a user accomplish a real job in
the realities of their context.

## 2. The reasoning questions

Ask these repeatedly while exploring, and record the answers that shape the product:

1. Who is the user in this context?
2. What are they actually trying to accomplish?
3. What decision are they trying to make, or action are they trying to perform?
4. What information do they need to do that confidently?
5. What information do they not need?
6. What constraints exist in their real-world environment?
7. How frequently does this task occur?
8. How consequential is getting it wrong?
9. What is the simplest interaction that lets them accomplish the task well?
10. Would a richer interaction communicate materially more useful information, or merely
    look more sophisticated?
11. What would happen if this proposed capability were removed?
12. Is this solving the user's problem, a business problem, a technical problem, or
    reinforcing the product's identity?
13. Does another role have a materially different need in the same workflow?
14. Could privacy, trust, commercial sensitivity, field conditions, connectivity,
    device constraints, expertise level or operational reality change the appropriate
    interaction?

Challenge a capability before it enters a specification; do not rationalize it
afterwards.

## 3. Request versus job

A stated request is evidence about the user; it is not the need. "I need a map" tells
you the user is thinking about location. The underlying job might be understanding
proximity, estimating mobilisation cost, comparing supply around a project, spotting
geographic concentration, or judging route practicality. Each job admits several
responses: distance, approximate area, travel time, proximity sorting, radius filtering,
a map.

The UN record therefore separates **Stated request** (optional, recorded as evidence)
from **Underlying job**, **Decision or action**, **Information required** and
**Desired outcome**. Derive the job from context; never copy the request into it.
A suite that transcribes requests into requirements is not user-centred, it is
compliant.

## 4. Product responses (C) and the Contextual Necessity Test

`C-###` is a **product response**: what we propose to do about a need. A response may
be a new capability, but it may equally be exposing information that already exists,
removing a step, changing a default, simplifying a workflow, combining information,
changing wording, altering a business rule, choosing a different representation,
deliberately doing nothing, or postponing until evidence improves. `Kind` names which.

Derive responses through `Need → Desired outcome → Candidate response → Possible
interaction`, and never let a later link masquerade as an earlier one.

Every C answers the Contextual Necessity Test:

| Field | Question |
|---|---|
| User | Who specifically needs this? |
| Context | In what situation? |
| Underlying job | What are they trying to accomplish? |
| Decision or action | What does this let them decide or do? |
| Required information | What must they know? |
| Desired outcome | What changes for them because this exists? |
| Proposed response | What are we proposing? |
| Simplest adequate response | The least complex response that satisfies the need |
| Alternatives considered | What simpler or different responses were weighed? |
| Incremental value | What additional useful information or capability does the richer response provide? |
| Cost | Cognitive, implementation, maintenance, performance and workflow complexity |
| Trust and privacy | Does it expose or imply information the system intentionally protects? |
| Removal test | If removed, which user outcome becomes materially worse? |
| Evidence class | See section 5 |

A response that cannot survive the test stays `hypothesis`, `rejected` or `deferred`.
Only an `accepted` response may be served by an FSD requirement. Apply the test to
material, product-shaping responses; trivial mechanical behaviors need no C and cite
their UN directly from the FSD.

## 5. Evidence classes

Every UN, C, observation and open item carries exactly one class:

| Class | Meaning |
|---|---|
| `fact` | Independently verifiable and stable (a calling code, a regulation's text) |
| `observed-behavior` | Empirically observed user or system behavior; bounded by sample and date |
| `stakeholder-requirement` | Stated by an accountable stakeholder; authority named |
| `domain-constraint` | Imposed by the domain, law, physics or an external system |
| `accepted-decision` | Ratified through a D-ID |
| `hypothesis` | Plausible and testable; not yet tested |
| `assumption` | Taken as true without evidence; must be surfaced |
| `preference` | Someone would like it this way; not a need |
| `aesthetic-choice` | Visual or stylistic; never a functional justification |

`observed-behavior` is separate from `fact` because three interviewed operators
coordinating handover over WhatsApp photographs is evidence of a kind that ages, varies
by sample and invites follow-up, while a country calling code does not.

Downstream documents never silently promote an assumption, preference or hypothesis
into a fact or a requirement. Confident prose is not evidence. On a greenfield
product, name the assumptions most capable of invalidating it and validate them before
expensive downstream design.

## 6. Product identity is not specification authority

Identity may influence presentation and positioning. It cannot independently justify
functionality. "We are map-first", "we are AI-first", "this is a dashboard product",
"this is a marketplace", "our design language requires this" are hypotheses or
preferences, never requirements. A map does not belong because the product is
map-first; a dashboard does not belong because the product is data-driven; realtime
does not belong because it feels modern; storefronts do not belong because marketplaces
usually have them.

When identity conflicts with user utility, utility wins unless an explicit strategic or
commercial reason justifies the tradeoff, and that tradeoff is recorded as a decision
with its cost, not hidden in branding language.

## 7. Function before form; contextual interfaces

Design an interaction only after the task and its information are understood:

```
task → information hierarchy → actions → states → interaction model → layout → visual treatment
```

Never design a distinctive container and then look for content to fill it. Optimise for
comprehension, decision speed, task completion, error avoidance, confidence,
predictable navigation, relevant density, progressive disclosure, accessibility and
domain familiarity. Boring but immediately understandable beats distinctive but
cognitively expensive. Visual distinction is welcome once functional clarity exists.

Do not seek one paradigm for the whole product. Different jobs deserve different
tools: a table, calendar, map, wizard, feed, search, comparison view or conversational
surface is chosen because it is the best tool for that task, not because another part
of the product uses it. Roles sharing one transaction usually need different
information and controls; model the whole multi-party workflow and give each role its
own surface where their needs differ.

## 8. Simplest complete solution

"Simplest adequate" removes unjustified complexity, not required capability. A simple
solution still covers the real workflow, its important edge cases, its trust
requirements and its acceptance contract. Reject any "MVP", "first slice" or
"keep it simple" that deletes behavior the primary job needs. The target is the
simplest complete solution, not the smallest amount of software.

## 9. Rebuilding an existing system

An existing implementation is domain research and implementation evidence, not
product authority. Extract and keep what earns it: business rules, invariants,
transaction semantics, vocabulary, integrations, trust and security lessons,
concurrency and data-integrity lessons, operational constraints. Require screens,
navigation, workflows, feature hierarchy, visual language, product identity,
interaction metaphors and architecture to re-earn their place from first principles.
That something was built proves it was built, not that it was right.

## 10. Controlled upstream deltas

Authority flows downstream; corrections flow upstream:

- FSD work finds the CON wrong or incomplete → reopen the CON through an O-ID.
- TSD work finds a product-behavior problem or a materially better behavior → surface
  it to the FSD/CON as an O-ID; the TSD does not redefine the product.
- Implementation finds a faulty assumption → surface a controlled delta; do not
  preserve it because "the spec says so".

Raise an O-ID when the change affects product meaning, user-visible behavior, business
rules, trust or privacy boundaries, acceptance semantics, programme scope or major
ordering. Smaller refinements stay implementation decisions recorded where the work
happens. Authority is preserved without process theatre.

A technology cannot create a requirement: PostGIS does not imply a map, realtime
infrastructure does not imply realtime behavior, an AI capability does not imply an AI
interaction, a visualization library does not imply visualization.

## 11. The backward-explainability invariant

Every significant product decision is explainable backward to a real user, a real
context and a real desired outcome. Every significant implementation decision is
explainable backward to an accepted product requirement:

```
implementation → slice → T → F → C → UN → UR → evidence
```

Confronted with a map, a dashboard, a websocket, a database field, a screen, a
notification, a service or a wave, we must be able to answer: whose job does this
materially improve, in what context, and how? If not, an unjustified assumption sits
somewhere in the chain. The invariant applies to meaningful behavior, not to every
line of code. `scripts/trace_chain.py` walks the chain mechanically; judgement decides
whether the chain is honest.

## 12. Anti-patterns as review questions

Ask these of any concept, specification or plan:

- Is the product defined as a list of features rather than jobs?
- Is an "X-first" identity dictating the interaction?
- Is there a screen inventory before the jobs are understood?
- Is there architecture before the behavior it must serve?
- Is a technology looking for a use case?
- Does a map communicate more than distance or area text would?
- Is a dashboard standing where the user needs a direct task flow?
- Is visualization doing work that a sentence or a sorted list would do better?
- Is feature parity with a competitor or a legacy system standing in for evidence?
- Are all roles being treated as if they had the same needs?
- Is a rare workflow being optimised at the cost of a frequent one?
- Is essential information hidden behind an impressive interaction?
- Is an abstraction present because it is elegant rather than needed?
- Is the design shaped by a component library rather than the task?
- Has legacy behavior been carried into a rebuild without revalidation?
- Has a business desire been written down as a user need?
- Has a user request been copied into the job without investigating context?
- Is "MVP" being used to avoid solving the complete core problem?

## 13. Agent posture

Be a constructive challenger, not a transcription engine. When the founder says "I want
feature X", reason: what need is X meant to address; is X the requirement or one
possible response? Use available context first, infer obvious answers, ask only the
questions whose answers change product meaning, and surface important assumptions
explicitly. The goal is better reasoning, not interrogation.
