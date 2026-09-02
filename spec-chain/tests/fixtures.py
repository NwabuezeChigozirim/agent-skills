"""Minimal valid CON/FSD/TSD fixtures shared by the spec-chain tests."""

from __future__ import annotations


def con(
    *,
    response_status: str = "accepted",
    response_evidence: str = "observed-behavior",
    extra_needs: str = "",
    deferred: str = "",
    kind: str = "capability",
) -> str:
    return f"""---
document_type: CON
authority: concept
---
# Sample Concept Document
# Part A — User reality
## User roles
| UR-ID | Role |
|---|---|
| UR-001 | Hirer |
### UR-001 — Hirer
- **Description:** hires equipment for a project
- **Environment:** site office, laptop, intermittent connectivity
- **Expertise:** experienced
- **Evidence class:** observed-behavior
- **Evidence or source:** three interviews, 2026-08
## User needs
### UN-001 — Judge supply proximity
- **Roles:** UR-001
- **Context:** shortlisting suppliers for a dated project
- **Stated request:** "show me a map"
- **Underlying job:** decide whether suitable supply is practical to mobilise
- **Decision or action:** shortlist or discard a supplier
- **Information required:** distance, availability, specification
- **Desired outcome:** confident shortlist without site visits
- **Evidence class:** observed-behavior
- **Evidence or source:** interviews
- **Confidence:** high
{extra_needs}
## Non-goals
| Non-goal | Reason |
|---|---|
| Route planning | outside the job |
# Part B — Product responses
## Response inventory
| C-ID | Kind | Serves | Status |
|---|---|---|---|
| C-001 | {kind} | UN-001 | {response_status} |
### C-001 — Show distance and area in results
- **Kind:** {kind}
- **Serves:** UN-001
- **Status:** {response_status}
- **User:** hirer
- **Context:** shortlisting
- **Underlying job:** judge practicality of mobilisation
- **Decision or action:** shortlist
- **Required information:** distance and area
- **Desired outcome:** confident shortlist
- **Proposed response:** distance and broad area on each result
- **Simplest adequate response:** distance text
- **Alternatives considered:** full map (rejected: coordinates protected); travel time (deferred)
- **Incremental value:** area adds regional context
- **Cost:** low
- **Trust and privacy:** exact coordinates never shown
- **Removal test:** hirers revert to phone calls
- **Evidence class:** {response_evidence}
- **Decision references:** D-001
## Deferred needs
| UN-ID | Why deferred | What keeps it cheap later |
|---|---|---|
{deferred}
## Blocking open decisions
No blocking O-IDs remain.
## Verification register
| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | no external claims |
## Recommendation
Build.
"""


def f_item(
    f_id: str = "F-001",
    name: str = "Understand supply proximity",
    *,
    kind: str = "endpoint",
    serves: str = "UN-001, C-001",
    representation: bool = False,
    labels: list[str] | None = None,
) -> str:
    required = labels or [
        "Kind",
        "Purpose",
        "Serves",
        "Actors and permission",
        "Context/trigger",
        "Inputs/content",
        "Actions and outcomes",
        "States",
        "Rules",
        "Errors and recovery",
        "Dependencies",
        "Done when",
    ]
    values = {"Kind": kind, "Serves": serves, "Dependencies": "D-001"}
    lines = [f"- **{label}:** {values.get(label, 'value')}" for label in required]
    if representation:
        lines.insert(-1, "- **Representation:** distance and area in a sorted list")
        lines.insert(-1, "- **Representation rationale:** the decision is proximity; coordinates are protected")
    return f"### {f_id} — {name}\n" + "\n".join(lines) + "\n"


def fsd(
    *,
    items: str | None = None,
    inventory_ids: list[str] | None = None,
    baseline: str = "",
    trace: str | None = None,
    extra: str = "",
) -> str:
    """`trace=None` omits the optional FSD traceability table; `trace=""` renders it empty."""
    items = items if items is not None else f_item()
    inventory_ids = inventory_ids or ["F-001"]
    rows = "\n".join(f"| {fid} | endpoint | item |" for fid in inventory_ids)
    traceability = (
        ""
        if trace is None
        else "## Traceability\n| F-ID | Serves (UN / C) | Decisions |\n|---|---|---|\n"
        + (f"{trace}\n" if trace else "")
    )
    return f"""---
document_type: FSD
authority: behavior
---
# Sample Functional Specification
{baseline}
## Functional inventory
| F-ID | Kind | Name |
|---|---|---|
{rows}
## Functional specifications
{items}
## Blocking open decisions
No blocking O-IDs remain.
## Verification register
| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | no external claims |
{traceability}{extra}
"""


def baseline(authority: str = "D-001") -> str:
    return f"""## User needs baseline
- **Baseline authority:** {authority}
### UR-001 — Hirer
- **Description:** hires equipment
- **Environment:** site office
- **Expertise:** experienced
- **Evidence class:** stakeholder-requirement
### UN-001 — Judge supply proximity
- **Roles:** UR-001
- **Context:** shortlisting
- **Underlying job:** decide whether supply is practical to mobilise
- **Decision or action:** shortlist
- **Desired outcome:** confident shortlist
- **Evidence class:** stakeholder-requirement
"""


def tsd(
    *,
    trace: str = "| F-001 | UN-001, C-001 | T-001 | tests |",
    realizes: str = "F-001, D-001",
    deltas: str = "None",
    extra: str = "",
) -> str:
    labels = [
        "Purpose",
        "Realizes",
        "Design",
        "Interfaces/contracts",
        "Invariants and failure handling",
        "Security/data considerations",
        "Verification",
        "Dependencies",
        "Risks",
    ]
    fields = "\n".join(
        f"- **{label}:** {realizes if label == 'Realizes' else 'value'}" for label in labels
    )
    return f"""---
document_type: TSD
authority: technical-design
---
# Sample Technical Design
## Cost evidence
Not applicable — no external cost conclusion.
## Technical requirements
### T-001 — Proximity computation service
{fields}
## Product deltas surfaced
{deltas}
## Blocking open decisions
No blocking O-IDs remain.
## Verification register
| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Runtime behavior | https://example.com/docs | 2026-08-17 | verified |
## Traceability
| F-ID | Serves | Implementing T-IDs | Verification |
|---|---|---|---|
{trace}
{extra}
"""
