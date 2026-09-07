"""Read-only dependency impact and owner-reviewed immutable stage successors.

Reuse the specification and planning graph owners. Potential impact is conservative;
it never proves a change harmless, rewrites artifacts or permits test-result reuse.
"""

from __future__ import annotations

from collections import deque
import importlib.util
from pathlib import Path
import sys
from typing import Any
import uuid

import artifact_contracts as ac
import stage_contracts as st


ACTIVITIES = ("discovery", "intent", "specification", "planning", "implementation", "validation")


def sibling(rt: Any, package: str, script: str) -> Any:
    path = rt.find_skill_root().parent / package / "scripts" / (script + ".py")
    if not path.is_file():
        raise ValueError(f"Impact graph helper is unavailable: {package}/{script}.py")
    name = "_governance_impact_" + script + "_" + st.digest(str(path))[:12]
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[name] = module
    return sys.modules[name]


def snapshot(rt: Any, repo: Path, contract: dict[str, Any], extra_paths: tuple[str, ...] = ()) -> dict[str, Any]:
    root = st.canonical(rt, repo)
    config = rt.load_config(repo, required=True)
    slug = str(config.get("project_slug") or root.name)
    sources = {kind: f"docs/{slug}-{kind.upper()}.md" for kind in ("con", "fsd", "tsd")}
    sources["decisions"] = "DECISIONS.md"
    paths = set(sources.values()) | {"design.md", "docs/waves/README.md", "docs/waves/PR-CHECKLIST.md"}
    paths.update(p.relative_to(root).as_posix() for p in (root / "docs/waves").glob("wave-*-*.md"))
    paths.update(contract["inputs"] + contract["outputs"])
    paths.update(extra_paths)
    files = {}
    text = {}
    for value in sorted(paths):
        path = st.local_file(root, value)
        if path.exists():
            state, _ = rt.file_state(root, value)
            if state.get("kind") != "file":
                raise ValueError(f"Impact input must be a readable regular file: {value}")
            files[value] = {key: state[key] for key in ("sha256", "mode", "size")}
            if value in sources.values() or value.startswith("docs/waves/"):
                text[value] = path.read_text(encoding="utf-8")
        else:
            files[value] = None
    graphs = []
    if any(files[sources[k]] is not None for k in ("con", "fsd", "tsd")):
        sg = sibling(rt, "spec-chain", "specification_graph")
        graphs.append(sg.build_graph(*(text.get(sources[k], "") for k in ("con", "fsd", "tsd", "decisions")),
                                     {k: str(root / p) for k, p in sources.items()}))
    if any(value.startswith("docs/waves/") and content is not None for value, content in files.items()):
        pg = sibling(rt, "plan-waves-slices", "planning_graph")
        graphs.append(pg.build_graph(root, "governance"))
    definitions, duplicates = ac.decisions(text.get("DECISIONS.md", ""))
    nodes, edges, diagnostics = {}, set(), []
    for graph in graphs:
        for diagnostic in graph["diagnostics"]:
            if diagnostic["severity"] == "error":
                diagnostics.append({"code": diagnostic["code"], "id": diagnostic.get("id", ""),
                                    "path": str(Path(diagnostic["path"]).relative_to(root))})
        for node in graph["nodes"]:
            path = str(Path(node["path"]).relative_to(root))
            # Locations are diagnostic metadata, not definition identity. Compact D
            # registers need their full cells, not just the parsed status field.
            meaning = {k: node[k] for k in ("type", "name", "fields", "order") if k in node}
            if node["type"] == "D":
                meaning["cells"] = definitions.get(node["id"], {}).get("cells", [])
            if node["type"] in {"wave", "slice"}:
                lines = text.get(path, "").splitlines()
                meaning["heading"] = lines[node["line"] - 1] if 0 < node["line"] <= len(lines) else ""
            nodes[node["id"]] = {"type": node["type"], "path": path, "definition_sha256": st.digest(meaning)}
        edges.update((e["source"], e["relation"], e["target"]) for e in graph["edges"])
    for identifier, record in definitions.items():
        nodes[identifier] = {"type": "D", "path": "DECISIONS.md", "definition_sha256": st.digest(record["cells"])}
    for identifier in duplicates:
        diagnostics.append({"code": "duplicate-definition", "id": identifier, "path": "DECISIONS.md"})
    # Wave references make the technical/design handoff explicit for impact review.
    # They do not establish new specification authority or implementation traceability.
    for identifier, node in list(nodes.items()):
        if node["type"] == "wave":
            for target in ac.ids(ac.visible(text.get(node["path"], ""))):
                edges.add((identifier, "references", target))
    if not text.get(sources["con"]):
        baseline, _ = ac.section(ac.visible(text.get(sources["fsd"], "")), "User needs baseline")
        fields, _ = ac.labels(baseline)
        for decision in ac.ids(fields.get("baseline authority", ""), "D"):
            edges.update((identifier, "baseline-authority", decision) for identifier, node in nodes.items() if node["type"] == "UN")
    stored = rt.read_json(rt.state_path(repo, "discovery-notes.json"), {"notes": []})
    notes = stored.get("notes")
    if not isinstance(notes, list) or any(not isinstance(n, dict) or not isinstance(n.get("id"), str) for n in notes):
        raise ValueError("Cannot build impact from malformed discovery notes")
    if len({n["id"] for n in notes}) != len(notes):
        raise ValueError("Cannot build impact from duplicate discovery note IDs")
    findings = {n["id"]: st.digest({k: v for k, v in n.items() if k not in {"created_at", "resolved_at"}}) for n in notes}
    return {"version": 1, "files": files, "nodes": nodes,
            "edges": [{"source": s, "relation": r, "target": t} for s, r, t in sorted(edges)],
            "findings": findings, "diagnostics": sorted(diagnostics, key=lambda d: (d["path"], d["id"], d["code"]))}


def candidate(rt: Any, repo: Path, path: str | None, envelope: dict[str, Any], *, require_inputs: bool = True) -> dict[str, Any]:
    value = rt.read_json(st.local_file(st.canonical(rt, repo), path)) if path else envelope["contract"]
    errors = st.contract_errors(value)
    if errors:
        raise ValueError("; ".join(errors))
    for output in value["outputs"]:
        st.local_file(st.canonical(rt, repo), output)
    for source in value["inputs"]:
        st.local_file(st.canonical(rt, repo), source)
        if require_inputs:
            st.file_ref(st.canonical(rt, repo), source)
    return value


def difference(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    return {"added": sorted(after.keys() - before.keys()), "removed": sorted(before.keys() - after.keys()),
            "modified": sorted(k for k in before.keys() & after.keys() if before[k] != after[k])}


def build_report(rt: Any, repo: Path, contract_path: str | None = None) -> dict[str, Any]:
    run = rt.read_json(rt.state_path(repo, "run-state.json"), {})
    _, envelope = st.load_stage(rt, repo, run)
    value = candidate(rt, repo, contract_path, envelope, require_inputs=False)
    baseline = envelope.get("impact_baseline")
    if baseline is not None and (not isinstance(baseline, dict) or baseline.get("version") != 1
            or not all(isinstance(baseline.get(k), dict) for k in ("files", "nodes", "findings"))
            or not isinstance(baseline.get("edges"), list) or not isinstance(baseline.get("diagnostics"), list)):
        raise ValueError("Frozen impact baseline is malformed or unsupported; do not invent historical coverage")
    old = baseline or {"files": {r["path"]: {"sha256": r["sha256"]} for r in envelope["inputs"]},
                       "nodes": {}, "edges": [], "findings": {}, "diagnostics": []}
    current = snapshot(rt, repo, value, tuple(old["files"]))
    # Absent watched paths are not additions/removals; their existence transition is.
    before_files = {p: f for p, f in old["files"].items() if f is not None}
    after_files = {p: f for p, f in current["files"].items() if f is not None}
    if baseline is None:
        after_files = {p: {"sha256": f["sha256"]} for p, f in after_files.items()}
    changed = difference(before_files, after_files)
    changed_paths = set().union(*changed.values())
    definitions = difference(old["nodes"], current["nodes"])
    all_nodes = {**old["nodes"], **current["nodes"]}
    seeds = set().union(*definitions.values())
    # File-level conservative fallback covers prose/constraints not modeled by graph
    # fields. Never call an unparsed change harmless or use this graph to skip checks.
    seeds.update(k for k, n in all_nodes.items() if n["path"] in changed_paths)
    edges = {(e["source"], e["relation"], e["target"]) for e in old["edges"] + current["edges"]}
    consumers = {}
    for source, relation, target in edges:
        consumers.setdefault(target, set()).add((source, relation))
    affected, queue, reasons = set(seeds), deque(sorted(seeds)), {}
    while queue:
        target = queue.popleft()
        for source, relation in sorted(consumers.get(target, set())):
            if source not in affected:
                affected.add(source)
                reasons[source] = {"via": target, "relation": relation}
                queue.append(source)
    # Membership also reports the containing wave without propagating from this
    # reporting-only parent back to its otherwise unaffected children.
    parents = {target for source, relation, target in edges if relation == "part-of" and source in affected}
    affected.update(parents)
    changes = {}
    retired = [f"definitions:{identifier}" for identifier in definitions["removed"]]
    for key in ("inputs", "outputs", "acceptance", "checks"):
        before = {v if isinstance(v, str) else v["id"]: v for v in envelope["contract"][key]}
        after = {v if isinstance(v, str) else v["id"]: v for v in value[key]}
        changes[key] = difference(before, after)
        retired.extend(f"{key}:{identifier}" for identifier in changes[key]["removed"])
    changes["scope_changed"] = value["scope"] != envelope["contract"]["scope"]
    changes["name_changed"] = value["name"] != envelope["contract"]["name"]
    findings = difference(old["findings"], current["findings"])
    activities = {"validation"}
    for path in changed_paths:
        if path == "DECISIONS.md":
            activities.add("intent")
        elif path.endswith("-CON.md"):
            activities.update({"discovery", "specification"})
        elif path.endswith(("-FSD.md", "-TSD.md")) or path == "design.md":
            activities.add("specification")
        elif path.startswith("docs/waves/"):
            activities.add("planning")
        elif path in envelope["contract"]["inputs"] or path in value["inputs"]:
            activities.add("intent")
        else:
            activities.add("implementation")
    if any(findings.values()):
        activities.update({"discovery", "intent"})
    if changes["scope_changed"] or any(changes["acceptance"].values()) or any(changes["inputs"].values()):
        activities.add("intent")
    if any(all_nodes.get(k, {}).get("type") in {"wave", "slice"} for k in affected):
        activities.add("planning")
    if any(all_nodes.get(k, {}).get("type") in {"UR", "UN", "C", "F", "F-NFR", "T"} for k in affected):
        activities.add("specification")
    uncertainty = []
    if baseline is None:
        uncertainty.append("Historical stage has hashes only; no prior graph or complete artifact baseline can be reconstructed")
        activities.update({"discovery", "intent", "specification", "planning"})
    if old["diagnostics"] or current["diagnostics"]:
        uncertainty.append("Specification/planning graph errors limit dependency coverage; validators and owner review remain required")
    report = {"stage_id": run["stage_id"], "from_contract_sha256": run["stage_contract_sha256"],
              "candidate_contract_sha256": st.digest(value), "current_baseline_sha256": st.digest(current),
              "precision": "conservative-file-and-graph" if baseline else "historical-baseline-missing",
              "changed_artifacts": changed, "changed_definitions": definitions, "changed_findings": findings,
              "affected": [{"id": k, **all_nodes.get(k, {}), **reasons.get(k, {})} for k in sorted(affected)],
              "contract_changes": changes, "retired_obligations": sorted(retired),
              "reentry": [a for a in ACTIVITIES if a in activities], "uncertainty": uncertainty,
              "graph_diagnostics": current["diagnostics"], "reuse_check_evidence": False}
    report["impact_sha256"] = st.digest(report)
    return report


def review_errors(value: Any, report: dict[str, Any]) -> list[str]:
    if not isinstance(value, dict) or set(value) != {"version", "impact_sha256", "rationale", "activities", "retirements", "uncertainty"}:
        return ["Review requires exactly version, impact_sha256, rationale, activities, retirements and uncertainty"]
    errors = []
    if type(value["version"]) is not int or value["version"] != 1 or value["impact_sha256"] != report["impact_sha256"]:
        errors.append("Impact review is stale or has an unsupported version; inspect the current proposed revision again")
    if not isinstance(value["rationale"], str) or not ac.meaningful(value["rationale"]):
        errors.append("Impact review requires a meaningful rationale")
    for key, required in (("activities", report["reentry"]), ("retirements", report["retired_obligations"])):
        mapping = value[key]
        if (not isinstance(mapping, dict) or set(mapping) != set(required)
                or any(not isinstance(v, str) or not ac.meaningful(v) for v in mapping.values())):
            errors.append(f"Review {key} must give a rationale for exactly every reported obligation")
    if not isinstance(value["uncertainty"], str) or (report["uncertainty"] and not ac.meaningful(value["uncertainty"])):
        errors.append("Review must explicitly address reported uncertainty")
    return errors


def revise(rt: Any, repo: Path, contract_path: str, review_path: str, approved: bool,
           approval_ref: str, reason: str, reopen: bool = False) -> dict[str, Any]:
    if not approved or not ac.meaningful(reason):
        raise ValueError("Revision requires --owner-approved and a meaningful --reason")
    with rt.state_lock(repo):
        rt.load_config(repo, required=True)
        run = rt.read_json(rt.state_path(repo, "run-state.json"), {})
        if run.get("status") not in {"active", "closed"}:
            raise ValueError("Revision needs an existing contracted run")
        _, previous = st.load_stage(rt, repo, run)
        value = candidate(rt, repo, contract_path, previous)
        approval = st.approval_record(rt, repo, approval_ref)
        review_ref = st.approval_record(rt, repo, review_path)
        root = st.canonical(rt, repo)
        review = rt.read_json(root / review_ref["path"])
        prior_revision = previous.get("revision", {})
        if (prior_revision.get("review_sha256") == st.digest(review) and previous["contract"] == value
                and previous["start_approval"] == approval and prior_revision.get("reason") == reason.strip()
                and prior_revision.get("reopened", False) == reopen
                and snapshot(rt, repo, value, tuple(previous["impact_baseline"]["files"])) == previous["impact_baseline"]):
            return {"revised": True, "changed": False, "stage_id": run["stage_id"]}
        if run["status"] == "closed" and not reopen:
            raise ValueError("Completed work requires explicit --reopen; its prior acceptance remains historical")
        if run["status"] == "active" and reopen:
            raise ValueError("--reopen applies only to a closed contracted run")
        report = build_report(rt, repo, contract_path)
        errors = review_errors(review, report)
        if errors:
            raise ValueError("; ".join(errors))
        if (st.digest(value) == st.digest(previous["contract"]) and not any(report["changed_artifacts"].values())
                and not any(report["changed_findings"].values()) and previous.get("impact_baseline") is not None):
            raise ValueError("No contract or recorded context change to revise; rerun checks without manufacturing a revision")
        # Check and retain the exact reviewed target. No old check receipts are copied.
        previous_paths = previous.get("impact_baseline", {}).get("files", {r["path"]: None for r in previous["inputs"]})
        baseline = snapshot(rt, repo, value, tuple(previous_paths))
        if st.digest(baseline) != report["current_baseline_sha256"]:
            raise ValueError("Artifacts changed during revision review; inspect again")
        if st.approval_record(rt, repo, review_path) != review_ref or st.approval_record(rt, repo, approval_ref) != approval:
            raise ValueError("Review or approval record changed during revision")
        if candidate(rt, repo, contract_path, previous) != value:
            raise ValueError("Proposed contract changed during revision")
        identifier = "ST-" + uuid.uuid4().hex
        prior_completion = None
        if reopen:
            prior_completion = rt.read_json(rt.state_dir(repo) / "stages" / run["stage_id"] / "closure.json")
            if not prior_completion or prior_completion != run.get("stage_completion"):
                raise ValueError("Cannot reopen without the intact historical closure receipt")
        next_run_id = "revision-" + identifier[3:] if reopen else run["run_id"]
        envelope = {"contract": value, "inputs": [st.file_ref(root, p) for p in value["inputs"]],
                    "start_approval": approval, "repository_id": rt.repo_identity(repo), "run_id": next_run_id,
                    "canonical_worktree": str(root), "frozen_at": rt.utc_now(), "impact_baseline": baseline,
                    "revision": {"from_stage_id": run["stage_id"], "from_contract_sha256": run["stage_contract_sha256"],
                                 "impact_sha256": report["impact_sha256"], "review": review,
                                 "review_sha256": st.digest(review), "review_reference": review_ref, "reason": reason.strip(),
                                 "reopened": reopen, "prior_run_id": run["run_id"],
                                 "prior_completion_sha256": st.digest(prior_completion) if prior_completion else None}}
        st.publish(rt, rt.state_dir(repo) / "stages" / identifier / "contract.json", envelope)
        run.setdefault("stage_history", []).append({"stage_id": run["stage_id"],
            "contract_sha256": run["stage_contract_sha256"], "status": "reopened" if reopen else "superseded", "completed": reopen,
            "superseded_by": identifier, "impact_sha256": report["impact_sha256"]})
        run.update(stage_id=identifier, stage_contract_sha256=st.digest(envelope), stage_required=True, updated_at=rt.utc_now(),
                   next_action="Review approved revision re-entry: " + ", ".join(report["reentry"]) + "; rerun every required check before closure")
        if reopen:
            run.update(status="active", run_id=next_run_id, started_at=rt.utc_now(), owner_close_approved=False,
                       canonical_head=rt.current_head(root), canonical_branch=rt.branch_name(root))
            run.pop("stage_completion", None)
            run.pop("closed_at", None)
        rt.atomic_write_json(rt.state_path(repo, "run-state.json"), run)
    return {"revised": True, "changed": True, "reopened": reopen, "stage_id": identifier,
            "previous_stage_id": envelope["revision"]["from_stage_id"], "checks_invalidated": True,
            "reentry": report["reentry"]}
