#!/usr/bin/env python3
"""Validate CON/FSD/TSD authority, completeness, and traceability.

Deterministic structural rules only. Semantic anti-patterns (identity-first reasoning,
technology push, form before function) are covered by references/need-first.md and the
behavioral evals, not by vocabulary checks here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


# Em dash is the house style; en dash and hyphen are accepted so a typo does not make
# every requirement vanish from the inventory check.
DASH = r"[—–-]"
F_HEADING = re.compile(rf"^###\s+(F-\d{{3,}})\s+{DASH}\s+(.+)$", re.MULTILINE)
T_HEADING = re.compile(rf"^###\s+(T-\d{{3,}})\s+{DASH}\s+(.+)$", re.MULTILINE)
UR_HEADING = re.compile(rf"^###\s+(UR-\d{{3,}})\s+{DASH}\s+(.+)$", re.MULTILINE)
UN_HEADING = re.compile(rf"^###\s+(UN-\d{{3,}})\s+{DASH}\s+(.+)$", re.MULTILINE)
C_HEADING = re.compile(rf"^###\s+(C-\d{{3,}})\s+{DASH}\s+(.+)$", re.MULTILINE)
NFR_ID = re.compile(r"\bF-NFR-\d{3,}\b")
HEADING_NUMBER = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
ANY_F = re.compile(r"\bF-\d{3,}\b")
ANY_T = re.compile(r"\bT-\d{3,}\b")
ANY_D = re.compile(r"\bD-\d{3,}\b")
ANY_O = re.compile(r"\bO-\d{3,}\b")
ANY_UR = re.compile(r"\bUR-\d{3,}\b")
ANY_UN = re.compile(r"\bUN-\d{3,}\b")
ANY_C = re.compile(r"\bC-\d{3,}\b")
ANY_RISK = re.compile(r"\bRK-\d{3,}\b")
WRONG_RISK = re.compile(r"(?i)\brisk\b[^\n|]*\bR-\d{2,}\b")
ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")

# Shared template-placeholder detector. Keep byte-identical with the copies in
# governance-system/scripts/governancectl and plan-waves-slices/scripts/validate_plan.py.
# Matches <Project Name>, <install-command>, <YYYY-MM-DD>, <N>; ignores HTML tags,
# generics such as Vec<T>, autolinks <https://...> and <user@host> addresses.
PLACEHOLDER_RE = re.compile(r"(?<!\w)<(?!\w+://)([A-Za-z][^<>\n@]{0,120})>")
HTML_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "dd", "del", "details", "div", "dl", "dt", "em",
    "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "li",
    "mark", "ol", "p", "pre", "s", "samp", "small", "span", "strong", "sub", "summary", "sup", "table",
    "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul", "var",
}

EVIDENCE_CLASSES = {
    "fact",
    "observed-behavior",
    "stakeholder-requirement",
    "domain-constraint",
    "accepted-decision",
    "hypothesis",
    "assumption",
    "preference",
    "aesthetic-choice",
}
WEAK_EVIDENCE = {"assumption", "preference", "aesthetic-choice"}
C_STATUSES = {"accepted", "hypothesis", "rejected", "deferred"}
C_KINDS = {
    "capability",
    "expose-information",
    "remove-step",
    "default-change",
    "simplification",
    "rule-change",
    "representation-change",
    "wording",
    "do-nothing",
    "defer",
}
# Kinds whose interaction model materially shapes the workflow; these require a stated
# representation and its rationale. Decided by the declared Kind, never by prose.
REPRESENTATION_KINDS = ("page", "screen", "journey")

UR_LABELS = ["Description", "Environment", "Expertise", "Evidence class"]
UN_CORE_LABELS = [
    "Roles",
    "Context",
    "Underlying job",
    "Decision or action",
    "Desired outcome",
    "Evidence class",
]
C_LABELS = [
    "Kind",
    "Serves",
    "Status",
    "User",
    "Context",
    "Underlying job",
    "Decision or action",
    "Required information",
    "Desired outcome",
    "Proposed response",
    "Simplest adequate response",
    "Alternatives considered",
    "Incremental value",
    "Cost",
    "Trust and privacy",
    "Removal test",
    "Evidence class",
    "Decision references",
]
F_LABELS = [
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
T_LABELS = [
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

CON_REQUIRED_SECTIONS = [
    "User roles",
    "User needs",
    "Non-goals",
    "Response inventory",
    "Recommendation",
]

FORBIDDEN_FSD_HEADINGS = {
    "architecture",
    "technology selections",
    "repository layout",
    "repository and module design",
    "data schema",
    "deployment topology",
    "build order",
    "work breakdown",
    "waves",
    "slices",
}

FORBIDDEN_TSD_HEADINGS = {
    "delivery plan",
    "milestones",
    "waves",
    "slices",
    "implementation sequence",
    "work breakdown",
}


# --- generic helpers ---------------------------------------------------------------


def find_placeholders(text: str) -> list[str]:
    found = {
        match.group(0)
        for match in PLACEHOLDER_RE.finditer(text)
        if match.group(1).split()[0].lower().rstrip("/") not in HTML_TAGS
    }
    return sorted(found)


def validate_placeholders(text: str, path: Path, errors: list[str]) -> None:
    placeholders = find_placeholders(text)
    if placeholders:
        preview = ", ".join(placeholders[:5]) + (" ..." if len(placeholders) > 5 else "")
        errors.append(f"{path.name}: unresolved template placeholders: {preview}")


def read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"Missing {path}")
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def requirement_sections(text: str, pattern: re.Pattern[str]) -> list[tuple[str, str]]:
    matches = list(pattern.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        # Stop at the next heading of level 1-3 so item bodies never swallow later sections.
        cut = re.search(r"^#{1,3}\s", body, re.MULTILINE)
        if cut:
            body = body[: cut.start()]
        sections.append((match.group(1), body))
    return sections


def label_value(body: str, label: str) -> str | None:
    # Horizontal whitespace only: an empty label must not capture the following line.
    match = re.search(rf"^[ \t]*-[ \t]+\*\*{re.escape(label)}:\*\*[ \t]*(.*)$", body, re.MULTILINE)
    return match.group(1).strip() if match else None


def table_ids(text: str, prefix: str) -> set[str]:
    pattern = re.compile(rf"^\|\s*({re.escape(prefix)}-\d{{3,}})\s*\|", re.MULTILINE)
    return set(pattern.findall(text))


def strip_heading_number(title: str) -> str:
    return HEADING_NUMBER.sub("", title.strip(), count=1)


def headings(text: str) -> set[str]:
    return {
        strip_heading_number(match.group(1)).lower()
        for match in re.finditer(r"^#{2,4}\s+(.+)$", text, re.MULTILINE)
    }


def section_body(text: str, title: str) -> str:
    # Accept an optional section number ("## 11. Title") because house style tells
    # authors to reference sections by number.
    pattern = re.compile(
        rf"^##\s+(?:\d+(?:\.\d+)*\.?\s+)?{re.escape(title)}\s*$\n(.*?)(?=^##?\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def validate_frontmatter(text: str, expected_type: str, path: Path, errors: list[str]) -> None:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append(f"{path.name}: missing YAML frontmatter")
        return
    frontmatter = match.group(1)
    if not re.search(
        rf"^document_type:\s*{re.escape(expected_type)}\s*$",
        frontmatter,
        re.MULTILINE | re.IGNORECASE,
    ):
        errors.append(f"{path.name}: document_type must be {expected_type}")


def validate_requirement_labels(
    sections: list[tuple[str, str]],
    labels: list[str],
    path: Path,
    errors: list[str],
) -> None:
    seen: set[str] = set()
    for requirement_id, body in sections:
        if requirement_id in seen:
            errors.append(f"{path.name}: duplicate requirement {requirement_id}")
        seen.add(requirement_id)
        for label in labels:
            if label_value(body, label) is None:
                errors.append(f"{path.name}: {requirement_id} missing label '{label}'")


def validate_evidence_class(item_id: str, body: str, path: Path, errors: list[str]) -> str | None:
    value = label_value(body, "Evidence class")
    if value is None:
        return None
    normalized = value.strip().strip("`").lower()
    if normalized not in EVIDENCE_CLASSES:
        errors.append(
            f"{path.name}: {item_id} evidence class '{value}' is not one of "
            + ", ".join(sorted(EVIDENCE_CLASSES))
        )
        return None
    return normalized


def validate_blocking_section(text: str, path: Path, errors: list[str]) -> None:
    body = section_body(text, "Blocking open decisions")
    if not body:
        errors.append(f"{path.name}: missing Blocking open decisions section")
        return
    if ANY_O.search(body):
        errors.append(f"{path.name}: blocking O-ID remains open")
    if "no blocking o-ids remain" not in body.lower():
        errors.append(f"{path.name}: blocking section must explicitly confirm no blocking O-IDs remain")


def validate_verification(text: str, path: Path, errors: list[str]) -> None:
    body = section_body(text, "Verification register")
    if not body:
        errors.append(f"{path.name}: missing Verification register")
        return
    for line in body.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        lowered = line.lower()
        if "http://" in lowered or "https://" in lowered:
            if not ISO_DATE.search(line):
                errors.append(f"{path.name}: sourced verification row lacks ISO access date")


def validate_decision_references(
    specs: list[tuple[Path, str]],
    decisions_text: str,
    errors: list[str],
) -> None:
    known_d = set(ANY_D.findall(decisions_text))
    known_o = set(ANY_O.findall(decisions_text))
    for path, text in specs:
        unknown_d = sorted(set(ANY_D.findall(text)) - known_d)
        unknown_o = sorted(set(ANY_O.findall(text)) - known_o)
        if unknown_d:
            errors.append(f"{path.name}: unknown decision IDs: {', '.join(unknown_d)}")
        if unknown_o:
            errors.append(f"{path.name}: unknown open-item IDs: {', '.join(unknown_o)}")


# --- need model ----------------------------------------------------------------------


class NeedModel:
    """UR / UN / C inventory shared by CON validation, FSD validation and tracing."""

    def __init__(self) -> None:
        self.users: dict[str, str] = {}
        self.needs: dict[str, str] = {}
        self.responses: dict[str, str] = {}
        self.response_status: dict[str, str] = {}
        self.response_serves: dict[str, set[str]] = {}
        self.need_roles: dict[str, set[str]] = {}
        self.need_confidence: dict[str, str] = {}
        self.source: str = "none"

    @property
    def accepted_responses(self) -> set[str]:
        return {cid for cid, status in self.response_status.items() if status == "accepted"}


def parse_need_model(text: str, source: str) -> NeedModel:
    model = NeedModel()
    model.source = source
    for user_id, body in requirement_sections(text, UR_HEADING):
        model.users[user_id] = body
    for need_id, body in requirement_sections(text, UN_HEADING):
        model.needs[need_id] = body
        model.need_roles[need_id] = set(ANY_UR.findall(label_value(body, "Roles") or ""))
        confidence = (label_value(body, "Confidence") or "").lower()
        model.need_confidence[need_id] = confidence.split()[0].rstrip(",;") if confidence else ""
    for response_id, body in requirement_sections(text, C_HEADING):
        model.responses[response_id] = body
        model.response_status[response_id] = (label_value(body, "Status") or "").strip().strip("`").lower()
        model.response_serves[response_id] = set(ANY_UN.findall(label_value(body, "Serves") or ""))
    return model


def validate_need_items(model: NeedModel, path: Path, errors: list[str], warnings: list[str]) -> None:
    validate_requirement_labels(list(model.users.items()), UR_LABELS, path, errors)
    validate_requirement_labels(list(model.needs.items()), UN_CORE_LABELS, path, errors)
    for user_id, body in model.users.items():
        validate_evidence_class(user_id, body, path, errors)
    for need_id, body in model.needs.items():
        validate_evidence_class(need_id, body, path, errors)
        unknown_roles = sorted(model.need_roles[need_id] - set(model.users))
        if unknown_roles:
            errors.append(f"{path.name}: {need_id} cites unknown user roles: {', '.join(unknown_roles)}")
        if not model.need_roles[need_id]:
            errors.append(f"{path.name}: {need_id} 'Roles' cites no UR-ID")


def validate_responses(model: NeedModel, text: str, path: Path, errors: list[str], warnings: list[str]) -> None:
    validate_requirement_labels(list(model.responses.items()), C_LABELS, path, errors)
    for response_id, body in model.responses.items():
        kind = (label_value(body, "Kind") or "").strip().strip("`").lower()
        if kind and kind not in C_KINDS:
            errors.append(
                f"{path.name}: {response_id} kind '{kind}' is not one of " + ", ".join(sorted(C_KINDS))
            )
        status = model.response_status[response_id]
        if status not in C_STATUSES:
            errors.append(
                f"{path.name}: {response_id} status '{status}' is not one of " + ", ".join(sorted(C_STATUSES))
            )
        serves = model.response_serves[response_id]
        if not serves:
            errors.append(f"{path.name}: {response_id} 'Serves' cites no UN-ID")
        unknown = sorted(serves - set(model.needs))
        if unknown:
            errors.append(f"{path.name}: {response_id} serves unknown needs: {', '.join(unknown)}")
        evidence = validate_evidence_class(response_id, body, path, errors)
        if status == "accepted" and evidence in WEAK_EVIDENCE:
            warnings.append(
                f"{path.name}: accepted response {response_id} rests on evidence class '{evidence}'; "
                "validate or record the tradeoff as a decision"
            )

    served = set().union(*model.response_serves.values()) if model.response_serves else set()
    excused = set(ANY_UN.findall(section_body(text, "Deferred needs"))) | set(
        ANY_UN.findall(section_body(text, "Non-goals"))
    )
    orphan_needs = sorted(set(model.needs) - served - excused)
    if orphan_needs:
        errors.append(
            f"{path.name}: needs without a product response, deferral or non-goal entry: "
            + ", ".join(orphan_needs)
        )


def validate_con(text: str, path: Path, errors: list[str], warnings: list[str]) -> NeedModel:
    validate_frontmatter(text, "CON", path, errors)
    present = headings(text)
    for title in CON_REQUIRED_SECTIONS:
        if title.lower() not in present:
            errors.append(f"{path.name}: missing section '{title}'")
    model = parse_need_model(text, "con")
    if not model.users:
        errors.append(f"{path.name}: no UR items found")
    if not model.needs:
        errors.append(f"{path.name}: no UN items found")
    validate_need_items(model, path, errors, warnings)
    validate_responses(model, text, path, errors, warnings)
    inventory = table_ids(section_body(text, "Response inventory"), "C")
    if inventory and inventory != set(model.responses):
        missing_specs = sorted(inventory - set(model.responses))
        missing_rows = sorted(set(model.responses) - inventory)
        if missing_specs:
            errors.append(f"{path.name}: inventory C-IDs missing specifications: {', '.join(missing_specs)}")
        if missing_rows:
            errors.append(f"{path.name}: response C-IDs missing inventory rows: {', '.join(missing_rows)}")
    validate_blocking_section(text, path, errors)
    validate_verification(text, path, errors)
    return model


def validate_fsd_baseline(
    fsd_text: str,
    fsd_path: Path,
    con_model: NeedModel | None,
    errors: list[str],
    warnings: list[str],
) -> NeedModel:
    baseline_body = section_body(fsd_text, "User needs baseline")
    baseline = parse_need_model(baseline_body, "fsd-baseline")
    if con_model is not None:
        if baseline.needs or baseline.users:
            errors.append(
                f"{fsd_path.name}: duplicate need authority: User needs baseline defines UR/UN items "
                "while a CON exists"
            )
        return con_model
    if not baseline.needs:
        errors.append(
            f"{fsd_path.name}: no CON and no 'User needs baseline' with UN items; the FSD has no upstream"
        )
        return baseline
    authority = label_value(baseline_body, "Baseline authority") or ""
    if not authority.strip() or find_placeholders(authority):
        errors.append(f"{fsd_path.name}: User needs baseline must name its 'Baseline authority' (D-ID or ratified source)")
    validate_need_items(baseline, fsd_path, errors, warnings)
    return baseline


def validate_f_items(
    f_sections: list[tuple[str, str]],
    model: NeedModel,
    fsd_path: Path,
    errors: list[str],
    warnings: list[str],
) -> dict[str, set[str]]:
    served_needs: dict[str, set[str]] = {}
    for f_id, body in f_sections:
        serves_text = label_value(body, "Serves") or ""
        needs = set(ANY_UN.findall(serves_text))
        responses = set(ANY_C.findall(serves_text))
        if label_value(body, "Serves") is not None and not (needs or responses):
            errors.append(f"{fsd_path.name}: {f_id} 'Serves' cites no UN-ID or C-ID")
        unknown_needs = sorted(needs - set(model.needs))
        unknown_responses = sorted(responses - set(model.responses))
        if unknown_needs:
            errors.append(f"{fsd_path.name}: {f_id} serves unknown needs: {', '.join(unknown_needs)}")
        if unknown_responses:
            errors.append(f"{fsd_path.name}: {f_id} serves unknown responses: {', '.join(unknown_responses)}")
        not_accepted = sorted(
            cid for cid in responses if cid in model.responses and model.response_status.get(cid) != "accepted"
        )
        if not_accepted:
            errors.append(
                f"{fsd_path.name}: {f_id} serves responses that are not accepted: "
                + ", ".join(f"{cid} ({model.response_status.get(cid) or 'unknown'})" for cid in not_accepted)
            )
        reachable = set(needs)
        for cid in responses:
            reachable |= model.response_serves.get(cid, set())
        served_needs[f_id] = reachable
        kind = (label_value(body, "Kind") or "").lower()
        if any(token in kind for token in REPRESENTATION_KINDS):
            for label in ("Representation", "Representation rationale"):
                value = label_value(body, label)
                if value is None or not value.strip():
                    errors.append(
                        f"{fsd_path.name}: {f_id} (kind '{kind}') is a material interaction and needs '{label}'"
                    )
        if reachable and all(model.need_confidence.get(uid) == "low" for uid in reachable):
            warnings.append(
                f"{fsd_path.name}: {f_id} rests only on low-confidence needs ({', '.join(sorted(reachable))})"
            )
    return served_needs


def validate_traceability(
    fsd_text: str,
    tsd_text: str,
    fsd_path: Path,
    tsd_path: Path,
    errors: list[str],
) -> tuple[set[str], set[str]]:
    f_sections = requirement_sections(fsd_text, F_HEADING)
    t_sections = requirement_sections(tsd_text, T_HEADING)
    validate_requirement_labels(f_sections, F_LABELS, fsd_path, errors)
    validate_requirement_labels(t_sections, T_LABELS, tsd_path, errors)
    f_ids = {item[0] for item in f_sections}
    t_ids = {item[0] for item in t_sections}
    inventory = table_ids(section_body(fsd_text, "Functional inventory"), "F")
    if inventory != f_ids:
        missing_specs = sorted(inventory - f_ids)
        missing_inventory = sorted(f_ids - inventory)
        if missing_specs:
            errors.append(f"{fsd_path.name}: inventory IDs missing specifications: {', '.join(missing_specs)}")
        if missing_inventory:
            errors.append(f"{fsd_path.name}: specification IDs missing inventory rows: {', '.join(missing_inventory)}")

    for t_id, body in t_sections:
        realizes = set(ANY_F.findall(label_value(body, "Realizes") or ""))
        unknown = sorted(realizes - f_ids)
        if unknown:
            errors.append(f"{tsd_path.name}: {t_id} realizes unknown F-IDs: {', '.join(unknown)}")
        if not realizes:
            errors.append(f"{tsd_path.name}: {t_id} 'Realizes' cites no F-ID; technology cannot create a requirement")

    # The FSD's own traceability table (F to UN/C and F to decision, fsd.md section 14) is
    # optional; when an FSD carries one it must cover every specified F and invent none.
    # F-NFR IDs keep their own namespace and are traced in the TSD.
    fsd_trace_body = section_body(fsd_text, "Traceability")
    if fsd_trace_body.strip():
        fsd_traced = set(ANY_F.findall(fsd_trace_body))
        fsd_orphans = sorted(f_ids - fsd_traced)
        fsd_unknown = sorted(fsd_traced - f_ids)
        if fsd_orphans:
            errors.append(f"{fsd_path.name}: F-IDs missing traceability: {', '.join(fsd_orphans)}")
        if fsd_unknown:
            errors.append(
                f"{fsd_path.name}: traceability cites unknown F-IDs: {', '.join(fsd_unknown)}"
            )

    trace_body = section_body(tsd_text, "Traceability")
    traced_f = set(ANY_F.findall(trace_body))
    traced_t = set(ANY_T.findall(trace_body))
    orphan_f = sorted(f_ids - traced_f)
    orphan_t = sorted(t_ids - traced_t)
    unknown_f = sorted(traced_f - f_ids)
    unknown_t = sorted(traced_t - t_ids)
    if orphan_f:
        errors.append(f"{tsd_path.name}: F-IDs missing traceability: {', '.join(orphan_f)}")
    if orphan_t:
        errors.append(f"{tsd_path.name}: T-IDs missing traceability: {', '.join(orphan_t)}")
    if unknown_f:
        errors.append(f"{tsd_path.name}: traceability cites unknown F-IDs: {', '.join(unknown_f)}")
    if unknown_t:
        errors.append(f"{tsd_path.name}: traceability cites unknown T-IDs: {', '.join(unknown_t)}")

    # Non-functional outcomes keep their own F-NFR namespace but must still be realized.
    nfr_ids = set(NFR_ID.findall(section_body(fsd_text, "Non-functional outcomes")))
    orphan_nfr = sorted(nfr_ids - set(NFR_ID.findall(trace_body)))
    if orphan_nfr:
        errors.append(f"{tsd_path.name}: F-NFR IDs missing traceability: {', '.join(orphan_nfr)}")
    return f_ids, t_ids


# --- entry point ---------------------------------------------------------------------


def validate_repository(repo: Path, project: str, mode: str) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    docs = repo / "docs"
    fsd_path = docs / f"{project}-FSD.md"
    tsd_path = docs / f"{project}-TSD.md"
    con_path = docs / f"{project}-CON.md"
    decisions_path = repo / "DECISIONS.md" if mode == "governance" else docs / f"{project}-DECISIONS.md"
    if mode == "governance" and (docs / f"{project}-DECISIONS.md").exists():
        errors.append(
            f"Duplicate decision authority: remove docs/{project}-DECISIONS.md and use root DECISIONS.md"
        )

    fsd_text = read(fsd_path, errors)
    tsd_text = read(tsd_path, errors)
    decisions_text = read(decisions_path, errors)
    con_text = con_path.read_text(encoding="utf-8", errors="replace") if con_path.is_file() else ""

    con_model: NeedModel | None = None
    if con_text:
        con_model = validate_con(con_text, con_path, errors, warnings)

    model = NeedModel()
    f_ids: set[str] = set()
    t_ids: set[str] = set()
    if fsd_text:
        validate_frontmatter(fsd_text, "FSD", fsd_path, errors)
        forbidden = sorted(headings(fsd_text).intersection(FORBIDDEN_FSD_HEADINGS))
        if forbidden:
            errors.append(f"{fsd_path.name}: HOW/build-order headings forbidden in FSD: {', '.join(forbidden)}")
        validate_blocking_section(fsd_text, fsd_path, errors)
        validate_verification(fsd_text, fsd_path, errors)
        model = validate_fsd_baseline(fsd_text, fsd_path, con_model, errors, warnings)
        f_sections = requirement_sections(fsd_text, F_HEADING)
        served = validate_f_items(f_sections, model, fsd_path, errors, warnings)
        # Every accepted response must be realized by at least one F; the FSD is where an
        # accepted response becomes behavior. Hypotheses and deferrals need no F.
        served_responses: set[str] = set()
        for _f_id, body in f_sections:
            served_responses |= set(ANY_C.findall(label_value(body, "Serves") or ""))
        unrealized = sorted(model.accepted_responses - served_responses)
        if unrealized:
            errors.append(
                f"{fsd_path.name}: accepted responses not served by any F item: {', '.join(unrealized)}"
            )
        del served
    if tsd_text:
        validate_frontmatter(tsd_text, "TSD", tsd_path, errors)
        forbidden = sorted(headings(tsd_text).intersection(FORBIDDEN_TSD_HEADINGS))
        if forbidden:
            errors.append(f"{tsd_path.name}: delivery-plan headings forbidden in TSD: {', '.join(forbidden)}")
        validate_blocking_section(tsd_text, tsd_path, errors)
        validate_verification(tsd_text, tsd_path, errors)
        if not section_body(tsd_text, "Cost evidence"):
            errors.append(f"{tsd_path.name}: missing Cost evidence section")
        if not section_body(tsd_text, "Product deltas surfaced"):
            errors.append(f"{tsd_path.name}: missing Product deltas surfaced section (state 'None' when empty)")
    if fsd_text and tsd_text:
        f_ids, t_ids = validate_traceability(fsd_text, tsd_text, fsd_path, tsd_path, errors)

    specs = [(fsd_path, fsd_text), (tsd_path, tsd_text)]
    if con_text:
        specs.insert(0, (con_path, con_text))
    if decisions_text:
        validate_decision_references(specs, decisions_text, errors)
    for path, text in specs:
        if WRONG_RISK.search(text):
            errors.append(f"{path.name}: use RK-### for risks; R-### is reserved for worktree resolutions")
        if text:
            validate_placeholders(text, path, errors)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "project": project,
        "mode": mode,
        "con": str(con_path) if con_path.is_file() else None,
        "fsd": str(fsd_path),
        "tsd": str(tsd_path),
        "needs_source": model.source,
        "user_ids": sorted(model.users),
        "need_ids": sorted(model.needs),
        "response_ids": sorted(model.responses),
        "accepted_response_ids": sorted(model.accepted_responses),
        "functional_ids": sorted(f_ids),
        "technical_ids": sorted(t_ids),
        "risk_ids": sorted(set(ANY_RISK.findall("\n".join(text for _path, text in specs)))),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--mode", choices=["governance", "standalone"], required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    result = validate_repository(repo, args.project, args.mode)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        lines = list(result["errors"])  # type: ignore[arg-type]
        lines += [f"warning: {item}" for item in result["warnings"]]  # type: ignore[union-attr]
        print("valid" if result["valid"] and not lines else "\n".join(lines) if lines else "valid")
    return 0 if result["valid"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
