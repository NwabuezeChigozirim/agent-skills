#!/usr/bin/env python3
"""Validate standalone or governance-mode wave planning output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "governance-system" / "scripts"))
import engineering_policy as policy  # noqa: E402
import artifact_contracts as ac  # noqa: E402
import planning_graph as pg  # noqa: E402


DECISION_ID = re.compile(r"\bD-\d{3,}\b")
FUNCTIONAL_ID = re.compile(r"\bF-\d{3,}\b")
TECHNICAL_ID = re.compile(r"\bT-\d{3,}\b")
NEED_ID = re.compile(r"\bUN-\d{3,}\b")
WAVE_HEADING = re.compile(r"^# Wave \d+\b|^## Wave \d+\b", re.MULTILINE)
EXIT_HEADING = re.compile(r"^## Exit criterion\s*$|^\*\*Exit criterion[^*]*\*\*", re.MULTILINE | re.IGNORECASE)
SLICE_HEADING = re.compile(r"^###\s+(W\d+-S\d+)\s+[—–-]\s+(.+)$", re.MULTILINE)
LEGEND = "⏸ gated · 🟡 approved & in progress · ✅ done & signed off"
SLICE_LABELS = [
    "Outcome",
    "Serves",
    "Why",
    "Usable when done",
    "Depends on",
    "Tests",
    "Acceptance evidence",
]

# Shared template-placeholder detector. Keep byte-identical with the copies in
# governance-system/scripts/governancectl and spec-chain/scripts/validate_spec.py.
# Matches <Project Name>, <install-command>, <YYYY-MM-DD>, <N>; ignores HTML tags,
# generics such as Vec<T>, autolinks <https://...> and <user@host> addresses.
PLACEHOLDER_RE = re.compile(r"(?<!\w)<(?!\w+://)([A-Za-z][^<>\n@]{0,120})>")
HTML_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "code", "dd", "del", "details", "div", "dl", "dt", "em",
    "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "li",
    "mark", "ol", "p", "pre", "s", "samp", "small", "span", "strong", "sub", "summary", "sup", "table",
    "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul", "var",
}


def find_placeholders(text: str) -> list[str]:
    found = {
        match.group(0)
        for match in PLACEHOLDER_RE.finditer(text)
        if match.group(1).split()[0].lower().rstrip("/") not in HTML_TAGS
    }
    return sorted(found)


def placeholder_errors(path: Path, repo: Path, text: str) -> list[str]:
    placeholders = find_placeholders(text)
    if not placeholders:
        return []
    preview = ", ".join(placeholders[:5]) + (" ..." if len(placeholders) > 5 else "")
    return [f"{path.relative_to(repo)} contains unresolved template placeholders: {preview}"]


def decision_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return set(DECISION_ID.findall(path.read_text(encoding="utf-8", errors="replace")))


def label_value(body: str, label: str) -> str | None:
    match = re.search(rf"^\s*-\s+\*\*{re.escape(label)}:\*\*\s*(.*)$", body, re.MULTILINE)
    return match.group(1).strip() if match else None


def slice_sections(text: str) -> list[tuple[str, str]]:
    matches = list(SLICE_HEADING.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        cut = re.search(r"^#{1,3}\s", body, re.MULTILINE)
        if cut:
            body = body[: cut.start()]
        sections.append((match.group(1), body))
    return sections


def known_needs(repo: Path) -> set[str]:
    docs = repo / "docs"
    found: set[str] = set()
    for path in list(docs.glob("*-CON.md")) + list(docs.glob("*-FSD.md")):
        found.update(NEED_ID.findall(path.read_text(encoding="utf-8", errors="replace")))
    return found


def validate_slices(
    brief: Path,
    repo: Path,
    text: str,
    known_functional: set[str],
    errors: list[str],
    warnings: list[str],
) -> None:
    slices = slice_sections(text)
    if not slices:
        errors.append(f"{brief.relative_to(repo)} has no slice sections (expected ### W<N>-S<k> — name)")
        return
    kinds = [(label_value(body, "Kind") or "").lower() for _, body in slices]
    if all(kind == "infrastructure" for kind in kinds):
        # slice-semantics.md: infrastructure slices are valid when genuinely prerequisite,
        # but are not a substitute for an end-to-end slice when one is possible. A wave
        # made only of them demonstrates no user-visible outcome, which may still be the
        # right call, so this is a warning and not an error.
        warnings.append(
            f"{brief.relative_to(repo)} has only infrastructure slices; the wave demonstrates "
            "no end-to-end outcome"
        )
    for slice_id, body in slices:
        kind = (label_value(body, "Kind") or "").lower()
        required = list(SLICE_LABELS)
        if kind == "infrastructure":
            required.append("Unlocks")
        for label in required:
            if not re.search(rf"^\s*-\s+\*\*{re.escape(label)}:\*\*", body, re.MULTILINE):
                errors.append(f"{brief.relative_to(repo)} {slice_id} missing label '{label}'")
        serves = label_value(body, "Serves") or ""
        unlocks = label_value(body, "Unlocks") or ""
        cited = set(FUNCTIONAL_ID.findall(serves)) | set(FUNCTIONAL_ID.findall(unlocks))
        if kind == "infrastructure":
            if not FUNCTIONAL_ID.search(unlocks):
                errors.append(f"{brief.relative_to(repo)} {slice_id} is infrastructure but Unlocks names no F-ID")
        elif not cited:
            errors.append(f"{brief.relative_to(repo)} {slice_id} cites no F-ID in Serves")
        unknown = sorted(cited - known_functional)
        if unknown:
            errors.append(
                f"{brief.relative_to(repo)} {slice_id} cites unknown functional IDs: {', '.join(unknown)}"
            )


def validate_governance(repo: Path, *, current: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    functional_pattern = re.compile(r"\bF-(?:NFR-)?\d{3,}\b") if current else FUNCTIONAL_ID
    waves_dir = repo / "docs" / "waves"
    index = waves_dir / "README.md"
    checklist = waves_dir / "PR-CHECKLIST.md"
    decisions = repo / "DECISIONS.md"
    for path in [index, checklist, decisions]:
        if not path.is_file():
            errors.append(f"Missing {path.relative_to(repo)}")
    if not index.is_file():
        return errors, warnings
    fsd_files = sorted((repo / "docs").glob("*-FSD.md"))
    tsd_files = sorted((repo / "docs").glob("*-TSD.md"))
    if len(fsd_files) != 1:
        errors.append(f"Expected exactly one canonical FSD; found {len(fsd_files)}")
    if len(tsd_files) != 1:
        errors.append(f"Expected exactly one canonical TSD; found {len(tsd_files)}")
    known_functional = (
        set(functional_pattern.findall(fsd_files[0].read_text(encoding="utf-8", errors="replace")))
        if len(fsd_files) == 1
        else set()
    )
    known_technical = (
        set(TECHNICAL_ID.findall(tsd_files[0].read_text(encoding="utf-8", errors="replace")))
        if len(tsd_files) == 1
        else set()
    )
    needs = known_needs(repo)
    index_text = index.read_text(encoding="utf-8", errors="replace")
    if current:
        index_text = ac.visible(index_text)
    if LEGEND not in index_text:
        errors.append("Wave index is missing the fixed status legend")
    errors.extend(placeholder_errors(index, repo, index_text))
    if checklist.is_file():
        errors.extend(
            placeholder_errors(checklist, repo, checklist.read_text(encoding="utf-8", errors="replace"))
        )
    briefs = sorted(waves_dir.glob("wave-[0-9]*-*.md"))
    if not briefs:
        errors.append("No per-wave brief files found")
    known_decisions = decision_ids(decisions)
    for brief in briefs:
        text = brief.read_text(encoding="utf-8", errors="replace")
        if current:
            text = ac.visible(text)
        count = len(EXIT_HEADING.findall(text))
        if count != 1:
            errors.append(f"{brief.relative_to(repo)} has {count} exit-criterion sections; expected 1")
        missing = sorted(set(DECISION_ID.findall(text)) - known_decisions)
        if missing:
            errors.append(f"{brief.relative_to(repo)} cites unknown decisions: {', '.join(missing)}")
        cited_functional = set(functional_pattern.findall(text))
        cited_technical = set(TECHNICAL_ID.findall(text))
        cited_needs = set(NEED_ID.findall(text))
        if not cited_functional:
            errors.append(f"{brief.relative_to(repo)} cites no F-ID behavior")
        if not cited_technical:
            errors.append(f"{brief.relative_to(repo)} cites no T-ID technical constraint")
        if not cited_needs:
            errors.append(f"{brief.relative_to(repo)} cites no UN-ID user need")
        unknown_functional = sorted(cited_functional - known_functional)
        unknown_technical = sorted(cited_technical - known_technical)
        unknown_needs = sorted(cited_needs - needs)
        if unknown_functional:
            errors.append(
                f"{brief.relative_to(repo)} cites unknown functional IDs: {', '.join(unknown_functional)}"
            )
        if unknown_technical:
            errors.append(
                f"{brief.relative_to(repo)} cites unknown technical IDs: {', '.join(unknown_technical)}"
            )
        if unknown_needs:
            errors.append(f"{brief.relative_to(repo)} cites unknown user needs: {', '.join(unknown_needs)}")
        if not current:
            validate_slices(brief, repo, text, known_functional, errors, warnings)
        errors.extend(placeholder_errors(brief, repo, text))
    duplicate_status = []
    for path in [repo / "AGENTS.md", repo / "CLAUDE.md", repo / "Implementations.md", repo / "README.md"]:
        if path.is_file() and LEGEND in path.read_text(encoding="utf-8", errors="replace"):
            duplicate_status.append(str(path.relative_to(repo)))
    if duplicate_status:
        errors.append(f"Mutable wave legend duplicated outside canonical index: {', '.join(duplicate_status)}")
    return errors, warnings


def validate_standalone(repo: Path, plan_name: str, *, current: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    decisions = repo / "docs" / f"{plan_name}-DECISIONS.md"
    waves = repo / "docs" / f"{plan_name}-WAVES.md"
    checklist = repo / "docs" / f"{plan_name}-PR-CHECKLIST.md"
    for path in [decisions, waves, checklist]:
        if not path.is_file():
            errors.append(f"Missing {path.relative_to(repo)}")
    if waves.is_file():
        text = waves.read_text(encoding="utf-8", errors="replace")
        if current:
            text = ac.visible(text)
        if LEGEND not in text:
            errors.append("Standalone waves document is missing the fixed status legend")
        wave_count = len(WAVE_HEADING.findall(text))
        exit_count = len(EXIT_HEADING.findall(text))
        if wave_count and exit_count != wave_count:
            errors.append(f"Standalone plan has {wave_count} waves but {exit_count} exit criteria")
        missing = sorted(set(DECISION_ID.findall(text)) - decision_ids(decisions))
        if missing:
            errors.append(f"Standalone plan cites unknown decisions: {', '.join(missing)}")
        errors.extend(placeholder_errors(waves, repo, text))
    for path in [decisions, checklist]:
        if path.is_file():
            errors.extend(placeholder_errors(path, repo, path.read_text(encoding="utf-8", errors="replace")))
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--mode", choices=["standalone", "governance"], required=True)
    parser.add_argument("--plan-name")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--policy", choices=["auto", "legacy", "current"], default="auto")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    if args.mode == "standalone" and not args.plan_name:
        parser.error("--plan-name is required in standalone mode")
    documents = (
        [repo / "docs" / f"{args.plan_name}-WAVES.md"]
        if args.mode == "standalone" else sorted((repo / "docs" / "waves").glob("*.md"))
    )
    policy_result = policy.evaluate_policy(repo, documents, args.policy)
    current = policy_result["policy_version"] == policy.CURRENT_POLICY
    errors, warnings = (
        validate_governance(repo, current=current)
        if args.mode == "governance"
        else validate_standalone(repo, args.plan_name, current=current)
    )
    errors.extend(policy_result["policy_errors"])
    graph = pg.build_graph(repo, args.mode, args.plan_name) if policy_result["policy_version"] == policy.CURRENT_POLICY else None
    graph_errors = ac.messages(graph) if graph is not None else []
    graph_warnings = ac.messages(graph, "warning") if graph is not None else []
    errors.extend(graph_errors)
    warnings.extend(graph_warnings)
    result = {**policy_result, "valid": not errors, "errors": errors, "warnings": warnings,
              "artifact_valid": not any(error not in policy_result["policy_errors"] for error in errors),
              "graph": graph, "graph_errors": graph_errors, "graph_warnings": graph_warnings,
              "graph_valid": not graph_errors if graph is not None else None}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("valid" if not errors else "\n".join(errors))
        for item in warnings:
            print(f"warning: {item}")
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
