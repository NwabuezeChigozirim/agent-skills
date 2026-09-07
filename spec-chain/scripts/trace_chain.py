#!/usr/bin/env python3
"""Walk the specification chain backward: T -> F -> C -> UN -> UR.

Implements the backward-explainability invariant from references/need-first.md §11 as a
structural check. A break means an item cannot be explained by a user, a context and an
outcome; judging whether an intact chain is honest remains a review task.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_spec as vs  # noqa: E402


def load_chain(repo: Path, project: str, requested_policy: str = "auto", mode: str = "governance") -> dict[str, Any]:
    docs = repo / "docs"
    con_path = docs / f"{project}-CON.md"
    fsd_path = docs / f"{project}-FSD.md"
    tsd_path = docs / f"{project}-TSD.md"
    con_text = con_path.read_text(encoding="utf-8", errors="replace") if con_path.is_file() else ""
    fsd_text = fsd_path.read_text(encoding="utf-8", errors="replace") if fsd_path.is_file() else ""
    tsd_text = tsd_path.read_text(encoding="utf-8", errors="replace") if tsd_path.is_file() else ""
    selected = vs.policy.evaluate_policy(repo, [con_path, fsd_path, tsd_path], requested_policy)
    graph = None
    if selected["policy_version"] == vs.policy.CURRENT_POLICY:
        decisions_path = repo / "DECISIONS.md" if mode == "governance" else docs / f"{project}-DECISIONS.md"
        decisions = decisions_path.read_text(encoding="utf-8") if decisions_path.is_file() else ""
        graph = vs.sg.build_graph(con_text, fsd_text, tsd_text, decisions,
                                 {"con": str(con_path), "fsd": str(fsd_path), "tsd": str(tsd_path), "decisions": str(decisions_path)})
        con_text, fsd_text, tsd_text = (vs.ac.visible(text) for text in (con_text, fsd_text, tsd_text))

    if con_text:
        model = vs.parse_need_model(con_text, "con")
    else:
        model = vs.parse_need_model(vs.section_body(fsd_text, "User needs baseline"), "fsd-baseline")

    f_items: dict[str, dict[str, Any]] = {}
    for f_id, body in vs.requirement_sections(fsd_text, vs.F_HEADING):
        serves = vs.label_value(body, "Serves") or ""
        f_items[f_id] = {
            "needs": sorted(set(vs.ANY_UN.findall(serves))),
            "responses": sorted(set(vs.ANY_C.findall(serves))),
            "purpose": vs.label_value(body, "Purpose") or "",
        }
    t_items: dict[str, dict[str, Any]] = {}
    for t_id, body in vs.requirement_sections(tsd_text, vs.T_HEADING):
        t_items[t_id] = {
            "realizes": sorted(set(vs.ANY_F.findall(vs.label_value(body, "Realizes") or ""))),
            "purpose": vs.label_value(body, "Purpose") or "",
        }
    if graph is not None:
        for node in graph["nodes"]:
            if node["type"] in {"F", "F-NFR"}:
                fields = node["fields"]
                f_items[node["id"]] = {"needs": sorted(vs.ac.ids(fields.get("serves", ""), "UN")),
                    "responses": sorted(vs.ac.ids(fields.get("serves", ""), "C")),
                    "purpose": fields.get("purpose", fields.get("outcome", ""))}
            elif node["type"] == "T":
                t_items[node["id"]] = {"realizes": sorted(vs.ac.ids(node["fields"].get("realizes", ""), "F", "F-NFR")),
                    "purpose": node["fields"].get("purpose", "")}
    return {"model": model, "f": f_items, "t": t_items, "has_fsd": bool(fsd_text), "has_tsd": bool(tsd_text),
            "graph": graph, "policy": selected}


def trace_need(model: vs.NeedModel, need_id: str, lines: list[str], breaks: list[str], indent: str) -> None:
    body = model.needs.get(need_id)
    if body is None:
        breaks.append(f"{need_id} is not defined")
        lines.append(f"{indent}{need_id}: UNDEFINED")
        return
    job = vs.label_value(body, "Underlying job") or ""
    outcome = vs.label_value(body, "Desired outcome") or ""
    evidence = vs.label_value(body, "Evidence class") or ""
    lines.append(f"{indent}{need_id}: job={job!r} outcome={outcome!r} evidence={evidence}")
    if not job.strip() or not outcome.strip():
        breaks.append(f"{need_id} lacks an underlying job or desired outcome")
    roles = model.need_roles.get(need_id, set())
    if not roles:
        breaks.append(f"{need_id} cites no user role")
    for role in sorted(roles):
        user = model.users.get(role)
        if user is None:
            breaks.append(f"{need_id} cites undefined role {role}")
            lines.append(f"{indent}  {role}: UNDEFINED")
        else:
            lines.append(f"{indent}  {role}: {vs.label_value(user, 'Description') or ''}")


def trace_response(model: vs.NeedModel, response_id: str, lines: list[str], breaks: list[str], indent: str) -> None:
    body = model.responses.get(response_id)
    if body is None:
        breaks.append(f"{response_id} is not defined")
        lines.append(f"{indent}{response_id}: UNDEFINED")
        return
    status = model.response_status.get(response_id, "")
    lines.append(f"{indent}{response_id}: status={status} response={vs.label_value(body, 'Proposed response') or ''!r}")
    if status != "accepted":
        breaks.append(f"{response_id} has status '{status or 'unknown'}'; only accepted responses may be realized")
    needs = model.response_serves.get(response_id, set())
    if not needs:
        breaks.append(f"{response_id} serves no need")
    for need_id in sorted(needs):
        trace_need(model, need_id, lines, breaks, indent + "  ")


def trace_f(chain: dict[str, Any], f_id: str, lines: list[str], breaks: list[str], indent: str = "") -> None:
    item = chain["f"].get(f_id)
    model: vs.NeedModel = chain["model"]
    if item is None:
        breaks.append(f"{f_id} is not defined")
        lines.append(f"{indent}{f_id}: UNDEFINED")
        return
    lines.append(f"{indent}{f_id}: {item['purpose']}")
    if not item["needs"] and not item["responses"]:
        breaks.append(f"{f_id} serves no need or response")
    for response_id in item["responses"]:
        trace_response(model, response_id, lines, breaks, indent + "  ")
    for need_id in item["needs"]:
        trace_need(model, need_id, lines, breaks, indent + "  ")


def trace_t(chain: dict[str, Any], t_id: str, lines: list[str], breaks: list[str]) -> None:
    item = chain["t"].get(t_id)
    if item is None:
        breaks.append(f"{t_id} is not defined")
        lines.append(f"{t_id}: UNDEFINED")
        return
    lines.append(f"{t_id}: {item['purpose']}")
    if not item["realizes"]:
        breaks.append(f"{t_id} realizes no F-ID")
    for f_id in item["realizes"]:
        trace_f(chain, f_id, lines, breaks, "  ")


def trace(chain: dict[str, Any], identifier: str) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    breaks: list[str] = []
    model: vs.NeedModel = chain["model"]
    if identifier.startswith("T-"):
        trace_t(chain, identifier, lines, breaks)
    elif identifier.startswith("F-"):
        trace_f(chain, identifier, lines, breaks)
    elif identifier.startswith("C-"):
        trace_response(model, identifier, lines, breaks, "")
    elif identifier.startswith("UN-"):
        trace_need(model, identifier, lines, breaks, "")
    else:
        breaks.append(f"unsupported identifier: {identifier}")
    return lines, breaks


def trace_all(chain: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {"traced": {}, "breaks": []}
    if chain.get("graph") is not None:
        report["breaks"].extend(vs.ac.messages(chain["graph"]))
    for t_id in sorted(chain["t"]):
        lines, breaks = trace(chain, t_id)
        report["traced"][t_id] = lines
        report["breaks"].extend(f"{t_id}: {item}" for item in breaks)
    for f_id in sorted(chain["f"]):
        lines, breaks = trace(chain, f_id)
        report["traced"][f_id] = lines
        report["breaks"].extend(f"{f_id}: {item}" for item in breaks)
    # Deduplicate while preserving order; F breaks repeat under every T that realizes them.
    seen: set[str] = set()
    report["breaks"] = [item for item in report["breaks"] if not (item in seen or seen.add(item))]
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--mode", choices=["governance", "standalone"], default="governance")
    parser.add_argument("--id", dest="identifier", help="Trace one T-, F-, C- or UN- identifier backward")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--policy", choices=["auto", "legacy", "current"], default="auto")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    chain = load_chain(repo, args.project, args.policy, args.mode)
    if not chain["has_fsd"]:
        result = {"valid": False, "breaks": [f"Missing docs/{args.project}-FSD.md"], "traced": {}}
    elif args.identifier:
        lines, breaks = trace(chain, args.identifier)
        if chain["graph"] is not None:
            breaks.extend(vs.ac.messages(chain["graph"]))
        result = {"valid": not breaks, "breaks": breaks, "traced": {args.identifier: lines}}
    else:
        report = trace_all(chain)
        result = {"valid": not report["breaks"], "breaks": report["breaks"], "traced": report["traced"]}
    policy_result = vs.policy.evaluate_policy(
        repo, [repo / "docs" / f"{args.project}-{kind}.md" for kind in ("CON", "FSD", "TSD")], args.policy
    )
    result.update(policy_result)
    result["graph"] = chain["graph"]
    result["graph_errors"] = vs.ac.messages(chain["graph"]) if chain["graph"] is not None else []
    result["graph_warnings"] = vs.ac.messages(chain["graph"], "warning") if chain["graph"] is not None else []
    result["graph_valid"] = not result["graph_errors"] if chain["graph"] is not None else None
    result["artifact_valid"] = not result["breaks"]
    result["breaks"].extend(policy_result["policy_errors"])
    result["valid"] = not result["breaks"]
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        for identifier, lines in result["traced"].items():
            print("\n".join(lines) if lines else identifier)
            print()
        for warning in result["graph_warnings"]:
            print(f"warning: {warning}")
        if result["breaks"]:
            print("BREAKS:")
            for item in result["breaks"]:
                print(f"  {item}")
        else:
            print("chain intact")
    return 0 if result["valid"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
