"""Read-only policy-2 planning structure; never authorizes execution or sign-off."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import re
from typing import Any

import artifact_contracts as ac


WAVE = re.compile(r"^#{1,2}[ \t]+Wave[ \t]+([1-9]\d*)\b[^\n]*$", re.MULTILINE)
SLICE = re.compile(r"^###[ \t]+(W[1-9]\d*-S[1-9]\d*)[ \t]+[—–-][ \t]+(.+)$", re.MULTILINE)
DEPENDENCY = re.compile(r"(?<![\w-])W[1-9]\d*-S[1-9]\d*(?![\w-])")


def build_graph(repo: Path, mode: str, plan_name: str | None = None) -> dict[str, Any]:
    report: dict[str, Any] = {"nodes": [], "edges": [], "diagnostics": []}
    docs = repo / "docs"
    index = docs / "waves" / "README.md" if mode == "governance" else docs / f"{plan_name}-WAVES.md"
    decisions_path = repo / "DECISIONS.md" if mode == "governance" else docs / f"{plan_name}-DECISIONS.md"

    def read(path: Path) -> str:
        return ac.visible(path.read_text(encoding="utf-8", errors="replace")) if path.is_file() else ""

    def issue(code: str, message: str, path: Path, line: int = 1, identifier: str = "", severity: str = "error") -> None:
        report["diagnostics"].append(ac.diagnostic(code, message, str(path), line, identifier, severity))

    decisions, duplicate_decisions = ac.decisions(read(decisions_path))
    for identifier in duplicate_decisions:
        issue("duplicate-definition", "has multiple decision definitions", decisions_path, decisions[identifier]["line"], identifier)
    known: set[str] | None = set(decisions)
    fsds, tsds = sorted(docs.glob("*-FSD.md")), sorted(docs.glob("*-TSD.md"))
    if mode == "standalone" and not fsds and not tsds:
        known = None  # Focused standalone planning does not require inventing a specification suite.
        issue("unvalidated-specification-references", "No FSD/TSD supplied; requirement reference existence is not checked", index, severity="warning")
    else:
        if len(fsds) != 1 or len(tsds) != 1 or fsds[0].stem.removesuffix("-FSD") != tsds[0].stem.removesuffix("-TSD"):
            issue("specification-set-mismatch", "Planning needs one matching canonical FSD/TSD pair", index)
        for path in fsds + tsds:
            text = read(path)
            assert known is not None
            known.update(item["id"] for item in ac.items(text))
            body, offset = ac.section(text, "Non-functional outcomes")
            known.update(row["cells"][0] for row in ac.rows(body, offset) if row["cells"] and re.fullmatch(r"F-NFR-\d{3,}", row["cells"][0]))
        if len(fsds) == 1:
            concept = fsds[0].with_name(fsds[0].name.replace("-FSD.md", "-CON.md"))
            assert known is not None
            known.update(item["id"] for item in ac.items(read(concept)) if item["id"].startswith(("UR-", "UN-", "C-")))

    text = read(index)
    status_body, status_offset = ac.section(text, "Status")
    statuses = {}
    for row in ac.rows(status_body, status_offset):
        if not row["cells"] or not re.fullmatch(r"W[1-9]\d*", row["cells"][0]):
            continue
        identifier = row["cells"][0]
        if identifier in statuses:
            issue("duplicate-wave-status", "has multiple status rows", index, row["line"], identifier)
        statuses[identifier] = row

    def reference(value: str) -> bool:
        if not ac.meaningful(value):
            return False
        decision_refs = ac.ids(value, "D")
        if decision_refs:
            return all(ref in decisions and decisions[ref]["status"] in {"active", "accepted"} for ref in decision_refs)
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", value)
        candidates = links or [value.strip().strip("`")]
        valid = True
        for target in candidates:
            if re.fullmatch(r"https?://[^\s]+", target):
                issue("external-approval-reference", "External approval reference is recorded but not fetched or authenticated", index, severity="warning")
                continue
            path = (index.parent / target.split("#", 1)[0]).resolve()
            if not target.split("#", 1)[0] or not path.is_relative_to(repo.resolve()) or not path.is_file() or path.stat().st_size == 0:
                valid = False
        return valid

    for identifier, row in statuses.items():
        fields = row["fields"]
        status = fields.get("status", "").replace("\ufe0f", "")
        if status not in {"⏸", "🟡", "✅"}:
            issue("invalid-wave-status", "status must be ⏸, 🟡 or ✅", index, row["line"], identifier)
        combined = fields.get("approval or sign-off evidence", "")
        start = fields.get("start approval", combined if status == "🟡" else "")
        signoff = fields.get("sign-off evidence", "")
        if status == "✅" and combined:
            match = re.fullmatch(r"start:\s*(.+?);\s*sign-off:\s*(.+)", combined, re.IGNORECASE)
            if match:
                start, signoff = match.groups()
        if status in {"🟡", "✅"} and (not reference(start) or (status == "✅" and not reference(signoff))):
            issue("missing-approval-reference", "progress needs a start-approval reference; completion also needs a sign-off reference", index, row["line"], identifier)

    waves: dict[str, dict[str, Any]] = {}
    files = sorted((docs / "waves").glob("wave-[0-9]*-*.md")) if mode == "governance" else [index]
    slices: dict[str, dict[str, Any]] = {}
    dependencies: dict[str, set[str]] = {}
    status_order = {identifier: position for position, identifier in enumerate(statuses)}
    for path in files:
        content = read(path)
        matches = list(WAVE.finditer(content))
        if mode == "governance" and len(matches) != 1:
            issue("wave-file-membership", "a wave brief must define exactly one wave", path)
        for position, match in enumerate(matches):
            identifier = f"W{match[1]}"
            body = content[match.end():matches[position + 1].start() if position + 1 < len(matches) else len(content)]
            line = content.count("\n", 0, match.start()) + 1
            if identifier in waves:
                issue("duplicate-wave", "has multiple wave definitions", path, line, identifier)
            waves[identifier] = {"path": path, "line": line}
            report["nodes"].append({"id": identifier, "type": "wave", "path": str(path), "line": line})
            if mode == "governance":
                file_number = re.match(r"wave-(\d+)-", path.name)
                if not file_number or int(file_number[1]) != int(match[1]):
                    issue("wave-file-membership", "filename and wave heading disagree", path, line, identifier)
            rationale, _ = ac.section(body, "Why this wave")
            if not ac.meaningful(rationale):
                issue("missing-wave-rationale", "needs a substantive Why this wave section", path, line, identifier)
            exits = list(re.finditer(r"^##[ \t]+Exit criterion[ \t]*$|^\*\*Exit criterion[^*\n]*\*\*", body, re.MULTILINE | re.IGNORECASE))
            exit_body = body[exits[0].end():] if exits else ""
            cut = re.search(r"^#{1,3}\s", exit_body, re.MULTILINE)
            if cut:
                exit_body = exit_body[:cut.start()]
            if len(exits) != 1 or not ac.meaningful(exit_body.strip().lstrip("> ")):
                issue("invalid-exit-criterion", "needs exactly one nonempty exit criterion", path, line, identifier)
            for ref in sorted(ac.ids(body)):
                if ref.startswith(("F-", "T-", "UN-", "C-", "D-")) and known is not None and ref not in known:
                    issue("undefined-reference", f"cites {ref} without a canonical definition", path, line, identifier)
                if ref.startswith("D-") and (ref not in decisions or decisions[ref]["status"] not in {"active", "accepted"}):
                    issue("unratified-decision", f"{ref} is not a defined active/accepted planning decision", path, line, identifier)
            parts = list(SLICE.finditer(body))
            if not parts:
                issue("missing-slices", "needs reviewable slice definitions", path, line, identifier)
            wave_kinds = []
            for slice_position, part in enumerate(parts):
                sid = part[1]
                rest = body[part.end():]
                cut = re.search(r"^#{1,3}\s", rest, re.MULTILINE)
                fields, duplicates = ac.labels(rest[:cut.start()] if cut else rest)
                wave_kinds.append(ac.clean(fields.get("kind", "")).casefold())
                slice_line = line + body.count("\n", 0, part.start())
                if sid in slices:
                    issue("duplicate-slice", "has multiple slice definitions", path, slice_line, sid)
                if sid.split("-", 1)[0] != identifier:
                    issue("slice-wave-mismatch", f"does not belong to {identifier}", path, slice_line, sid)
                node = {"id": sid, "type": "slice", "path": str(path), "line": slice_line, "fields": fields,
                        "order": (status_order.get(identifier, int(match[1])), slice_position)}
                slices[sid] = node
                report["nodes"].append(node)
                report["edges"].append({"source": sid, "relation": "part-of", "target": identifier})
                for label in duplicates:
                    issue("duplicate-label", f"has multiple '{label}' labels", path, slice_line, sid)
                for label in ("serves", "depends on"):
                    if label not in fields:
                        issue("missing-slice-label", f"requires the '{label}' label", path, slice_line, sid)
                for label in ("outcome", "why", "usable when done", "tests", "acceptance evidence"):
                    if not ac.meaningful(fields.get(label, "")):
                        issue("empty-slice-obligation", f"requires a nonempty '{label}'", path, slice_line, sid)
                relation = "unlocks" if ac.clean(fields.get("kind", "")).casefold() == "infrastructure" else "serves"
                targets = ac.ids(fields.get(relation, ""), "F", "F-NFR")
                if not targets:
                    issue("missing-slice-requirement", f"{relation} must cite an F-ID or F-NFR-ID", path, slice_line, sid)
                for target in sorted(targets):
                    report["edges"].append({"source": sid, "relation": relation, "target": target})
                    if known is not None and target not in known:
                        issue("undefined-reference", f"{relation} undefined {target}", path, slice_line, sid)
                value = fields.get("depends on", "")
                dependencies[sid] = set(DEPENDENCY.findall(value))
                if not dependencies[sid] and ac.clean(value).casefold() != "none":
                    issue("invalid-dependency", "Depends on must name slice IDs or explicitly say none", path, slice_line, sid)
                if dependencies[sid] and re.search(r"\bnone\b", value, re.IGNORECASE):
                    issue("invalid-dependency", "cannot name dependencies and none together", path, slice_line, sid)
            if wave_kinds and all(kind == "infrastructure" for kind in wave_kinds):
                issue("infrastructure-only-wave", "only infrastructure slices; review whether the wave demonstrates the intended outcome", path, line, identifier, "warning")

    if not waves:
        issue("missing-waves", "plan defines no waves", index)
    if set(waves) != set(statuses):
        issue("wave-index-mismatch", "status rows and wave definitions must match exactly", index)
    if mode == "governance":
        for identifier in waves.keys() & statuses.keys():
            cell = statuses[identifier]["fields"].get("brief", "")
            link = re.search(r"\[[^\]]*\]\(([^)]+)\)", cell)
            target = (index.parent / (link[1] if link else cell).split("#", 1)[0]).resolve()
            if target != waves[identifier]["path"].resolve():
                issue("wave-index-mismatch", "Brief cell does not identify this wave's definition", index, statuses[identifier]["line"], identifier)

    # Kahn's algorithm avoids a recursion limit on large plans. Remaining nodes
    # are cyclic or depend on a cycle; diagnose both without authoring a new order.
    remaining = {sid: len(targets & slices.keys()) for sid, targets in dependencies.items()}
    consumers: dict[str, set[str]] = {sid: set() for sid in slices}
    for sid, targets in dependencies.items():
        node = slices[sid]
        for target in sorted(targets):
            report["edges"].append({"source": sid, "relation": "depends-on", "target": target})
            if target not in slices:
                issue("undefined-dependency", f"depends on undefined {target}", Path(node["path"]), node["line"], sid)
            else:
                consumers[target].add(sid)
                if slices[target]["order"] >= node["order"]:
                    issue("forward-dependency", f"{target} is not an earlier slice in the declared plan order", Path(node["path"]), node["line"], sid)
    ready = deque(sorted(sid for sid, count in remaining.items() if count == 0))
    while ready:
        for consumer in sorted(consumers[ready.popleft()]):
            remaining[consumer] -= 1
            if remaining[consumer] == 0:
                ready.append(consumer)
    for sid, count in remaining.items():
        if count:
            node = slices[sid]
            issue("dependency-cycle", "is cyclic or depends on a cyclic slice chain", Path(node["path"]), node["line"], sid)
    report["nodes"].sort(key=lambda node: (node["id"], node["path"], node["line"]))
    report["edges"].sort(key=lambda edge: (edge["source"], edge["relation"], edge["target"]))
    return report
