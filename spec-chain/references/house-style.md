# House Style

Governs all three documents and the chat response that delivers them.

## Contents
1. Voice
2. Flagging
3. Numbers and money
4. Requirement strength
5. Naming and codes
6. Callout boxes
7. Tables versus prose
8. Chat response format
9. Phrases to avoid

---

## 1. Voice

Plain, everyday language. Short sentences. Lead with the answer, then the reason.

Give the principle behind a rule, not only the rule. "Applications belong to a cycle, never to a programme" is a rule; adding "this is what lets every report compare one year with another without special work" is why anyone will follow it.

Write to be argued with. A sentence that states a position invites correction; a sentence that hedges everything cannot be checked and so never gets fixed.

Prefer concrete consequence over abstract concern:

- Weak: "Careful consideration should be given to the storage limits."
- Strong: "The free tier suspends the project at 500 MB. The year-one estimate is 409 MB, so the warning threshold is set at 350 MB."

Occasional dry judgement is welcome where it carries information: "A backup nobody has restored is a hope." Never at the expense of clarity, and never more than a few times in a document.

---

## 2. Flagging

Lead with what is weak, missing, or wrong — in the chat response and in the document.

A flag has three parts: what is wrong, what it causes, and what to do instead. Drop any of the three and it reads as complaining.

Place flags next to the material they undermine. A hosting problem belongs in the hosting section, not in a risk appendix nobody opens.

Rank by consequence, not by how uncomfortable they are to raise. The item most likely to cost money or a schedule slip goes first.

If the user's own decision creates the problem, say so plainly and still design against their decision. Their call, stated cost, named fallback.

---

## 3. Numbers and money

In prose, spell out: "twenty-five dollars a month", "eight hundred and forty thousand naira across two years", "sixty out of every hundred applications".

In tables, code blocks and schemas, use figures: `500 MB`, `₦200,000`, `12 characters`.

Always show the arithmetic when a conclusion depends on it. Put it in a code block so it can be checked line by line:

```
730 hours in a month × 0.25 compute units × $0.106 = $19.35 per month
```

When converting currency, state the rate used and the date. Rates move; a figure with no stated rate is unauditable six weeks later.

Never present a cost conclusion without the sum that produced it.

---

## 4. Requirement strength

Define once, near the front, and use consistently:

- **Must** — required for launch; absence is a defect and blocks sign-off
- **Should** — required unless a written reason is logged in the decision register
- **May** — optional; absence is not a defect
- **Deferred** — explicitly excluded from this delivery; designed for, not built

Do not invent additional strengths ("ideally", "where possible", "if time allows"). They mean *may* and they hide it.

---

## 5. Naming and codes

Document codes: `{PROJECT}-{TYPE}-{NNN}`, for example `OLK-FSD-002`, `AS-CON-001`,
`TG-TSD-001`. Three-letter project prefix, three-letter type, zero-padded sequence.

Every document opens with a register of the others in its chain and their status: draft, issued, superseded, not started.

Reference sections by number across documents ("per FSD Section 8.9"), never by page. Pages move.

Use the shared namespaces: `UR-###` users, `UN-###` needs, `C-###` product responses,
`D-###` decisions, `O-###` open questions, `E-###` observations, `F-###` functional
requirements, `T-###` technical requirements and `RK-###` risks. `R-###` is reserved for
governance worktree resolutions.

Names in code are the names to use everywhere. State that explicitly — renaming later is a refactor nobody funds.

## 5a. Needs, requests and evidence

Write the request and the job as two sentences, never one:

- Weak: "Users need a map."
- Strong: "Operators asked for a map (stated request, observed-behavior, three interviews, 2026-08). The job is judging whether suitable supply is practical to mobilise to the project; distance, area, travel time and a map are candidate responses."

Name the evidence class in the sentence or the label, and let the class show. "Users prefer" is a `preference`; "users must" without a source is an `assumption`; write it as one. A hypothesis reads as a hypothesis: "We expect… ; unvalidated."

---

## 6. Callout boxes

Reserved for flags, risks, and decisions that change what someone does. Three or four per document. More than that and they stop being noticed.

Give each one a title that states the finding, not the topic:

- Weak: "Note on hosting"
- Strong: "Flag — the hosting decision is not settled enough to design against"
- Strong: "The arithmetic that breaks the budget"
- Strong: "Verify in week one, not week nine"

Body: two to four short paragraphs. State the problem, the evidence, the options, and the recommendation. End with the register reference so it is tracked, not just noted.

---

## 7. Tables versus prose

Use a table when the same handful of attributes repeats across many items — page inventories, permission matrices, registers, comparisons, job schedules. The regularity is the point.

Use prose for reasoning, trade-offs, and anything where the argument matters more than the fields.

Use bullets for lists of independent facts, and bold the lead-in when each bullet is a term plus its explanation.

Never use a table for a single item, and never let a table carry an argument — a reader skims tables.

---

## 8. Chat response format

The document is the deliverable. The chat response is the briefing on top of it.

1. Flags first — the two or three findings that change what the user does next, each with its consequence and, where relevant, the arithmetic.
2. What is in the document — a short paragraph or a tight list, not a table of contents.
3. What is unverified — the things deliberately not asserted, and when they get checked.

Keep it well under a page. Do not narrate the build process, do not explain the file structure, do not thank anyone.

---

## 9. Phrases to avoid

| Avoid | Use instead |
|---|---|
| "It's worth noting that" | State the thing |
| "Robust", "seamless", "leverage", "utilise" | Plain equivalents |
| "Best practices" | The specific practice and why |
| "Comprehensive solution" | What it actually covers |
| "As discussed" | The specific reference |
| "Simply", "just", "easily" | Nothing — they are never true of the reader |
| "TBD" | An open-decision entry with an owner and a date |
| "Etc." in a requirements list | Finish the list or state the rule that generates it |
| "We are X-first" as a requirement | Record as preference or hypothesis; justify function from a UN |
| "Feature parity" | Name the job that is missing, with evidence |
| "MVP" as a reason to drop core-job behavior | The simplest complete solution; defer with a UN |
| "We are X-first", "our design language requires" | The user job and the evidence; identity is a preference, record it as one |
| "Feature parity with…" | The specific job the legacy or competitor feature served, and whether our users share it |
| "Users need a <interface>" | The job in one sentence, then the candidate responses |
| "Modern", "feels dated" | The comprehension or task-completion problem, if there is one |
