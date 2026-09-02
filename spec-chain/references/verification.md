# Verification

The most expensive errors in a spec are confident sentences about things that changed. Prices, free tiers, version numbers and platform behaviours all go stale, and a wrong one is only discovered when the build hits it.

## Always search before writing

| Category | Why | Examples |
|---|---|---|
| Service pricing and free tiers | Changes several times a year and drives the budget conclusion | Database, object storage, email, hosting plans |
| Platform constraints | Determines whether the architecture is possible at all | Memory ceilings, persistent processes, native modules, schedulers, connection limits |
| Version numbers | Majors change API shape | Framework, ORM, auth library |
| Exchange rates | Needed whenever a foreign-priced service is converted | Any currency conversion, with the date stated |
| Regulatory specifics | Cited in data protection sections | Data protection acts, retention requirements |

Scale to what the document cites. A spec touching four external services needs roughly four to six searches, not twenty. Search per service rather than combining them — a combined query returns shallow results for all of them.

## Turn findings into design, not trivia

A verified figure is only useful once it has been multiplied out against the actual budget or volume. The pattern:

1. Find the real limit.
2. Work out what the system actually consumes.
3. Compare, in a code block, so the sum is checkable.
4. State whether it fits.
5. If it does not, give the recommendation, the mitigation, and the trigger for changing course.

Worked example of the shape:

```
Free allowance:  100 compute-hours per month
Requirement:     always-on, 730 hours in a month at 0.25 units
Consumption:     730 × 0.25 = 182.5 compute-hours
Verdict:         exhausted around day seventeen — not a production option
```

The verdict line is the part people skip. Without it the table is decoration.

## Quotas need a mechanism

Any limit the system will actually meet gets a design response in the document, not a note:

- A daily send cap → a budgeted priority queue that sends what the allowance permits and defers the rest
- A storage ceiling → a measurement job with warning thresholds and a named upgrade trigger
- An idle-pause policy → a keep-alive whose own failure is separately alerted
- A rate limit → backoff and a visible state for the person waiting

## When something cannot be verified

Never write it as fact and never quietly omit it. Convert it into one of three things:

- **A week-one verification task** in the work breakdown, with a "done when"
- **A risk register entry** with likelihood, impact, and a concrete fallback
- **An open decision** with a default that lets work continue

And say so in the chat response: name what was not verified and when it gets checked. A reader who knows which three sentences are uncertain can act; a reader who thinks everything is verified cannot.

## Phrasing

- Verified: state it plainly, with the figure.
- Unverified: "This was not verified while writing. Task 0.1 is to confirm it and record the result."
- Never: "should support", "typically allows", "is generally able to" — these read as verified and are not.

## Provider independence

Use an adapter boundary when provider volatility, budget dependence, compliance,
availability, or contract obligations justify substitution. Record the reason and the
expected change surface. Do not add abstraction automatically when the service is a
ratified fixed dependency and substitution has no funded value.
