"""Policy-2 specification edges derived from canonical Markdown, never persisted."""

from __future__ import annotations

import re
from typing import Any

import artifact_contracts as ac


def build_graph(con: str, fsd: str, tsd: str, decisions: str, paths: dict[str, str]) -> dict[str, Any]:
    con, fsd, tsd = (ac.visible(text) for text in (con, fsd, tsd))
    report: dict[str, Any] = {"nodes": {}, "edges": [], "diagnostics": []}
    nodes = report["nodes"]
    accepted, repeated = ac.decisions(decisions)

    def issue(code: str, message: str, node: dict[str, Any], severity: str = "error") -> None:
        report["diagnostics"].append(ac.diagnostic(code, message, node["path"], node.get("line", 1), node.get("id", ""), severity))

    def add(item: dict[str, Any], source: str, kind: str | None = None) -> None:
        node = {**item, "path": paths[source], "type": kind or item["id"].rsplit("-", 1)[0]}
        if node["id"] in nodes:
            issue("duplicate-definition", "is defined more than once", node)
        else:
            nodes[node["id"]] = node
        for label in item.get("duplicate_labels", []):
            issue("duplicate-label", f"has multiple '{label}' fields", node)

    for identifier, record in accepted.items():
        add({"id": identifier, "line": record["line"], "fields": {**record["fields"], "status": record["status"]}}, "decisions", "D")
    for identifier in repeated:
        issue("duplicate-definition", "has multiple decision register definitions", nodes[identifier])
    for source, text in (("con", con), ("fsd", fsd), ("tsd", tsd)):
        allowed = {"con": {"UR", "UN", "C"}, "fsd": {"UR", "UN", "F"}, "tsd": {"T"}}[source]
        for item in ac.items(text):
            if item["id"].rsplit("-", 1)[0] in allowed:
                add(item, source)
    nfr_body, offset = ac.section(fsd, "Non-functional outcomes")
    for row in ac.rows(nfr_body, offset):
        if row["cells"] and re.fullmatch(r"F-NFR-\d{3,}", row["cells"][0]):
            add({"id": row["cells"][0], "line": row["line"], "fields": row["fields"]}, "fsd", "F-NFR")

    def edge(node: dict[str, Any], relation: str, target: str, allowed: set[str]) -> None:
        report["edges"].append({"source": node["id"], "relation": relation, "target": target,
                                "path": node["path"], "line": node["line"]})
        if target not in nodes:
            issue("undefined-reference", f"{relation} undefined {target}", node)
        elif nodes[target]["type"] not in allowed:
            issue("wrong-reference-type", f"{relation} {target}; expected {', '.join(sorted(allowed))}", node)
        elif nodes[target]["type"] == "D" and nodes[target]["fields"].get("status") not in {"active", "accepted"}:
            issue("unratified-decision", f"{target} is not active/accepted in the decision register", node)

    requirements = {key for key, node in nodes.items() if node["type"] in {"F", "F-NFR"}}
    technical = {key for key, node in nodes.items() if node["type"] == "T"}
    realizes: set[tuple[str, str]] = set()
    serves: dict[str, set[str]] = {}
    required = {"UR": ["description"], "UN": ["context", "underlying job", "decision or action", "desired outcome"],
                "F": ["purpose", "done when"], "T": ["purpose", "verification"],
                "F-NFR": ["outcome", "measure", "verification"]}
    for node in list(nodes.values()):
        kind, fields = node["type"], node["fields"]
        for label in required.get(kind, []):
            if not ac.meaningful(fields.get(label, "")):
                issue("empty-obligation", f"requires a nonempty '{label}' obligation", node)
        if kind == "UN":
            targets = ac.ids(fields.get("roles", ""))
            if not targets:
                issue("missing-user-role", "must name a defined UR-ID", node)
            for target in sorted(targets):
                edge(node, "roles", target, {"UR"})
        if kind in {"C", "F", "F-NFR"}:
            targets = ac.ids(fields.get("serves", ""))
            serves[node["id"]] = targets
            if not targets:
                issue("missing-serves", "must serve a defined need or accepted response", node)
            for target in sorted(targets):
                edge(node, "serves", target, {"UN"} if kind == "C" else {"UN", "C"})
                if kind != "C" and target in nodes and nodes[target]["type"] == "C":
                    if ac.clean(nodes[target]["fields"].get("status", "")).casefold() != "accepted":
                        issue("unaccepted-response", f"cannot implement {target} before acceptance", node)
        if kind == "C" and ac.clean(fields.get("status", "")).casefold() == "accepted":
            refs = ac.ids(fields.get("decision references", ""), "D")
            if not refs:
                issue("missing-ratification", "accepted response must cite a ratified D-ID", node)
            for ref in sorted(refs):
                edge(node, "ratified-by", ref, {"D"})
            if ac.clean(fields.get("evidence class", "")).casefold() in {"hypothesis", "assumption", "preference", "aesthetic-choice"}:
                issue("weak-evidence", "ratification authorizes the response but does not establish its empirical truth", node, "warning")
        if kind == "T":
            targets = ac.ids(fields.get("realizes", ""))
            functional = targets & requirements
            if not functional:
                issue("missing-realization", "must realize at least one defined F-ID or F-NFR-ID", node)
            for target in sorted(targets):
                edge(node, "realizes", target, {"F", "F-NFR", "D"})
                if target in requirements:
                    realizes.add((target, node["id"]))
        if kind in {"F", "T"}:
            for target in sorted(ac.ids(fields.get("dependencies", ""))):
                if target.startswith(("D-", "F-", "T-")):
                    edge(node, "depends-on", target, {"F", "F-NFR", "D"} if kind == "F" else {"F", "F-NFR", "T", "D"})

    if not con:
        baseline, offset = ac.section(fsd, "User needs baseline")
        fields, _ = ac.labels(baseline)
        for ref in sorted(ac.ids(fields.get("baseline authority", ""), "D")):
            if ref not in accepted or accepted[ref]["status"] not in {"active", "accepted"}:
                issue("unratified-baseline", f"baseline authority {ref} must be defined and active/accepted", {"path": paths["fsd"], "line": offset + 1})

    for prefix, title, text, source in (("C", "Response inventory", con, "con"), ("F", "Functional inventory", fsd, "fsd")):
        if prefix == "C" and not con:
            continue
        body, offset = ac.section(text, title)
        inventory = []
        for row in ac.rows(body, offset):
            if row["cells"] and re.fullmatch(rf"{prefix}-\d{{3,}}", row["cells"][0]):
                inventory.append(row["cells"][0])
        defined = {key for key, node in nodes.items() if node["type"] == prefix}
        origin = {"path": paths[source], "line": offset + 1}
        if set(inventory) != defined or len(inventory) != len(set(inventory)):
            issue("inventory-definition-mismatch", f"{title} must contain exactly one row for each defined {prefix}-ID", origin)
    if not requirements:
        issue("missing-requirements", "no functional or non-functional requirements are defined", {"path": paths["fsd"]})
    if not technical:
        issue("missing-technical-design", "no technical requirements are defined", {"path": paths["tsd"]})

    # Check exact edge sets, not just ID membership anywhere in a trace table.
    trace_body, offset = ac.section(tsd, "Traceability")
    traced: set[tuple[str, str]] = set()
    seen = set()
    for row in ac.rows(trace_body, offset):
        if not row["cells"] or not re.fullmatch(r"F-(?:NFR-)?\d{3,}", row["cells"][0]):
            continue
        identifier = row["cells"][0]
        origin = {"id": identifier, "path": paths["tsd"], "line": row["line"]}
        if identifier in seen:
            issue("duplicate-trace-row", "has multiple TSD trace rows", origin)
        seen.add(identifier)
        fields = row["fields"]
        targets = ac.ids(fields.get("implementing t-ids", ""))
        if identifier not in requirements:
            issue("undefined-reference", "trace row does not name a defined F/F-NFR", origin)
        if not targets:
            issue("missing-trace-realization", "trace row must name an implementing T-ID", origin)
        for target in sorted(targets):
            if target not in technical:
                issue("undefined-reference", f"trace row names undefined technical requirement {target}", origin)
            traced.add((identifier, target))
        if ac.ids(fields.get("serves", "")) != serves.get(identifier, set()):
            issue("serves-edge-mismatch", "TSD trace Serves must equal the authoritative FSD Serves set", origin)
        if not ac.meaningful(fields.get("verification", "")):
            issue("empty-verification", "trace row requires verification", origin)
    for identifier in sorted(requirements - seen):
        issue("missing-trace-row", "has no TSD trace row", nodes[identifier])
    for identifier, target in sorted(traced ^ realizes):
        origin = nodes.get(target, {"id": target, "path": paths["tsd"]})
        issue("realization-edge-mismatch", f"{identifier} → {target} disagrees between Realizes and the trace table", origin)
    for identifier in sorted(requirements - {f for f, _ in realizes}):
        issue("unrealized-requirement", "has no technical realization", nodes[identifier])

    fsd_trace, offset = ac.section(fsd, "Traceability")
    if fsd_trace.strip():
        fsd_seen = set()
        for row in ac.rows(fsd_trace, offset):
            if row["cells"] and re.fullmatch(r"F-(?:NFR-)?\d{3,}", row["cells"][0]):
                identifier = row["cells"][0]
                origin = {"id": identifier, "path": paths["fsd"], "line": row["line"]}
                if identifier in fsd_seen:
                    issue("duplicate-trace-row", "has multiple FSD trace rows", origin)
                fsd_seen.add(identifier)
                if identifier not in requirements:
                    issue("undefined-reference", "FSD trace names an undefined requirement", origin)
                fields = row["fields"]
                field = fields.get("serves (un / c)", fields.get("serves", ""))
                if ac.ids(field) != serves.get(identifier, set()):
                    issue("serves-edge-mismatch", "FSD trace Serves disagrees with the defining item", {"id": identifier, "path": paths["fsd"], "line": row["line"]})
        for identifier in sorted({key for key in requirements if nodes[key]["type"] == "F"} - fsd_seen):
            issue("missing-fsd-trace-row", "has no row in the optional FSD trace table", nodes[identifier])
    report["nodes"] = [nodes[key] for key in sorted(nodes)]
    report["edges"].sort(key=lambda edge: (edge["source"], edge["relation"], edge["target"]))
    return report
