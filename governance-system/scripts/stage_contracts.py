"""Opt-in, content-bound stage contracts. Runtime supplies Git, locking and storage.

The frozen JSON is an acceptance contract, not a replacement specification or plan.
Only run_check executes a command; inspection never executes or writes anything.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import uuid
from typing import Any

import artifact_contracts as ac


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def local_file(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or not path.parts or any(part in {"..", ".git"} for part in path.parts):
        raise ValueError(f"Expected a repository-relative file outside .git: {value}")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Stage references cannot traverse symlinks: {value}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Stage reference escapes the canonical repository: {value}")
    return current


def file_ref(root: Path, value: str) -> dict[str, str]:
    path = local_file(root, value)
    if not path.is_file() or not path.stat().st_size:
        raise ValueError(f"Stage reference must be an existing nonempty regular file: {value}")
    return {"path": path.relative_to(root).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def approval_record(rt: Any, repo: Path, value: str) -> dict[str, str]:
    """External local records allow owner sign-off without editing the tested tree."""
    root = canonical(rt, repo)
    path = Path(value)
    if not path.is_absolute():
        return file_ref(root, value)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Approval records cannot traverse symlinks")
    path = path.resolve()
    if path.is_relative_to(root):
        return file_ref(root, str(path.relative_to(root)))
    if any(path.is_relative_to(Path(w["path"]).resolve()) for w in rt.parse_worktrees(repo)):
        raise ValueError("An external approval record must be outside all registered worktrees")
    if not path.is_file() or not path.stat().st_size:
        raise ValueError("Approval record must be an existing nonempty regular file")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def contract_errors(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["Contract must be an object"]
    errors = []
    fields = {"version", "name", "scope", "inputs", "outputs", "acceptance", "checks"}
    if set(value) != fields or type(value.get("version")) is not int or value["version"] != 1:
        errors.append("Contract requires exactly version=1, name, scope, inputs, outputs, acceptance and checks")
    for key in ("name", "scope"):
        if not isinstance(value.get(key), str) or not ac.meaningful(value[key]):
            errors.append(f"Contract {key} must be meaningful text")
    for key in ("inputs", "outputs"):
        paths = value.get(key)
        if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p.strip() for p in paths):
            errors.append(f"Contract {key} must be a nonempty list of file paths")
        elif len(set(paths)) != len(paths):
            errors.append(f"Contract {key} contains duplicate paths")
    check_ids = set()
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("Contract needs at least one executable check")
        checks = []
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"id", "argv", "timeout_seconds"}:
            errors.append("Each check requires exactly id, argv and timeout_seconds")
            continue
        identifier = check.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"CHK-\d{3,}", identifier) or identifier in check_ids:
            errors.append("Check IDs must be unique CHK-### definitions")
        else:
            check_ids.add(identifier)
        argv = check.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(a, str) or not a or "\0" in a for a in argv):
            errors.append("Check argv must be a nonempty array of nonempty strings, not a shell command")
        timeout = check.get("timeout_seconds")
        if type(timeout) is not int or not 1 <= timeout <= 3600:
            errors.append("Check timeout_seconds must be an integer from 1 to 3600")
    acceptance = value.get("acceptance")
    if not isinstance(acceptance, list) or not acceptance:
        errors.append("Contract needs at least one acceptance obligation")
        acceptance = []
    used, covered = set(), set()
    for item in acceptance:
        if not isinstance(item, dict) or set(item) != {"id", "description", "checks"}:
            errors.append("Each acceptance obligation requires exactly id, description and checks")
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not re.fullmatch(r"AC-\d{3,}", identifier) or identifier in used:
            errors.append("Acceptance IDs must be unique AC-### definitions")
        else:
            used.add(identifier)
        if not isinstance(item.get("description"), str) or not ac.meaningful(item["description"]):
            errors.append("Acceptance descriptions must be meaningful")
        refs = item.get("checks")
        if not isinstance(refs, list) or not refs or any(not isinstance(r, str) for r in refs):
            errors.append("Acceptance checks must be a nonempty list of defined check IDs")
        elif len(set(refs)) != len(refs) or set(refs) - check_ids:
            errors.append("Acceptance checks must reference unique defined check IDs")
        else:
            covered.update(refs)
    if check_ids - covered:
        errors.append("Every required check must support an acceptance obligation")
    return errors


def publish(rt: Any, path: Path, value: Any) -> None:
    """Create only; a crash may leave an unreferenced file, never overwrite history."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd, temporary = tempfile.mkstemp(prefix=".stage-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def active(rt: Any, repo: Path) -> dict[str, Any]:
    rt.load_config(repo, required=True)
    run = rt.read_json(rt.state_path(repo, "run-state.json"))
    if not run or run.get("status") != "active":
        raise ValueError("An active run is required; use discover first")
    return run


def canonical(rt: Any, repo: Path) -> Path:
    return Path(rt.load_canonical(repo)["canonical_worktree"])


def subject(rt: Any, repo: Path, contract: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = rt.inventory(repo)
    item = next(w for w in inventory["worktrees"] if w["canonical"])
    if item["availability"] != "available" or not item.get("content_verifiable", True):
        raise ValueError("Canonical content is unavailable or unverifiable")
    declared = {}
    for value in sorted(set((contract or {}).get("inputs", []) + (contract or {}).get("outputs", []))):
        path = local_file(Path(item["path"]), value)
        declared[value] = file_ref(Path(item["path"]), value)["sha256"] if path.exists() else None
    return {"canonical_worktree": item["path"], "head": item["head"],
            "content_fingerprint": item["content_fingerprint"], "declared_files": declared}


def load_stage(rt: Any, repo: Path, run: dict[str, Any], *, check_canonical: bool = True) -> tuple[Path, dict[str, Any]]:
    identifier = run.get("stage_id", "")
    if not isinstance(identifier, str) or not re.fullmatch(r"ST-[0-9a-f]{32}", identifier):
        raise ValueError("Missing or invalid frozen stage ID")
    directory = rt.state_dir(repo) / "stages" / identifier
    envelope = rt.read_json(directory / "contract.json")
    if not envelope or digest(envelope) != run.get("stage_contract_sha256"):
        raise ValueError("Frozen contract is missing or its content no longer matches the run")
    if envelope.get("repository_id") != rt.repo_identity(repo) or envelope.get("run_id") != run.get("run_id"):
        raise ValueError("Frozen contract belongs to a different repository or run")
    if check_canonical and envelope.get("canonical_worktree") != str(canonical(rt, repo)):
        raise ValueError("Canonical worktree changed after contract freeze")
    if contract_errors(envelope.get("contract")):
        raise ValueError("Stored stage contract is malformed")
    return directory, envelope


def freeze(rt: Any, repo: Path, contract_path: str, approved: bool, approval_ref: str) -> dict[str, Any]:
    if not approved:
        raise ValueError("Freezing a stage requires explicit --owner-approved")
    with rt.state_lock(repo):
        run = active(rt, repo)
        root = canonical(rt, repo)
        value = rt.read_json(local_file(root, contract_path))
        errors = contract_errors(value)
        if errors:
            raise ValueError("; ".join(errors))
        inputs = [file_ref(root, p) for p in value["inputs"]]
        for output in value["outputs"]:
            local_file(root, output)
        approval = approval_record(rt, repo, approval_ref)
        if run.get("stage_id"):
            _, previous = load_stage(rt, repo, run)
            if previous["contract"] == value and previous["inputs"] == inputs and previous["start_approval"] == approval:
                return {"frozen": True, "changed": False, "stage_id": run["stage_id"]}
            raise ValueError("An active contract is immutable; cancel it explicitly before freezing a replacement")
        identifier = "ST-" + uuid.uuid4().hex
        envelope = {"contract": value, "inputs": inputs, "start_approval": approval,
                    "repository_id": rt.repo_identity(repo), "run_id": run["run_id"],
                    "canonical_worktree": str(root), "frozen_at": rt.utc_now()}
        publish(rt, rt.state_dir(repo) / "stages" / identifier / "contract.json", envelope)
        run.update(stage_id=identifier, stage_contract_sha256=digest(envelope), stage_required=True,
                   updated_at=rt.utc_now())
        rt.atomic_write_json(rt.state_path(repo, "run-state.json"), run)
    return {"frozen": True, "changed": True, "stage_id": identifier, "contract_sha256": digest(envelope)}


def note_errors(rt: Any, repo: Path, root: Path) -> list[str]:
    errors = []
    stored = rt.read_json(rt.state_path(repo, "discovery-notes.json"), {"notes": []})
    notes = stored.get("notes")
    if not isinstance(notes, list) or any(not isinstance(n, dict) for n in notes):
        return ["Discovery notes are malformed"]
    decisions_path = root / "DECISIONS.md"
    definitions, duplicates = ac.decisions(decisions_path.read_text() if decisions_path.is_file() else "")
    for note in notes:
        if note.get("kind") not in {"blocking", "needs-owner"}:
            continue
        resolution = note.get("resolution", {})
        decision = resolution.get("decision") if isinstance(resolution, dict) else None
        if not isinstance(decision, str):
            decision = None
        accepted = definitions.get(decision, {})
        if (not accepted or decision in duplicates or accepted.get("status") not in {"active", "accepted"}
                or resolution.get("decision_sha256") != digest(accepted["cells"])
                or resolution.get("owner_approved") is not True
                or not ac.meaningful(resolution.get("rationale", ""))):
            errors.append(f"{note.get('id', 'unknown')}: blocking intent requires a current owner-ratified decision")
    return errors


def resolve_note(rt: Any, repo: Path, identifier: str, decision: str, rationale: str, approved: bool) -> dict[str, Any]:
    if not approved or not ac.meaningful(rationale):
        raise ValueError("Resolving intent requires --owner-approved and a meaningful --note")
    with rt.state_lock(repo):
        active(rt, repo)
        root = canonical(rt, repo)
        file_ref(root, "DECISIONS.md")
        definitions, duplicates = ac.decisions((root / "DECISIONS.md").read_text())
        if decision not in definitions or decision in duplicates or definitions[decision]["status"] not in {"active", "accepted"}:
            raise ValueError("Resolution requires a defined active or accepted D-ID in canonical DECISIONS.md")
        path = rt.state_path(repo, "discovery-notes.json")
        stored = rt.read_json(path, {"notes": []})
        note = next((n for n in stored["notes"] if n.get("id") == identifier), None)
        if not note or note.get("kind") not in {"blocking", "needs-owner"}:
            raise ValueError("Resolve an existing blocking or needs-owner N-ID; observations are not decisions")
        resolution = {"decision": decision, "decision_sha256": digest(definitions[decision]["cells"]),
                      "rationale": rationale.strip(), "owner_approved": True}
        if note.get("resolution") == resolution:
            return {"resolved": True, "id": identifier, "changed": False}
        if note.get("resolution"):
            note.setdefault("resolution_history", []).append(note["resolution"])
        note["resolution"] = resolution
        note["resolved_at"] = rt.utc_now()
        rt.atomic_write_json(path, stored)
        registry = rt.read_json(rt.state_path(repo, "registry.json"))
        if registry:
            rt.atomic_write_json(rt.state_path(repo, "discovery.json"), rt.discovery_packet(repo, registry))
    return {"resolved": True, "id": identifier, "changed": True}


def inspect(rt: Any, repo: Path, required: bool = False, *, include_checks: bool = True) -> dict[str, Any]:
    diagnostics: list[dict[str, str]] = []
    report: dict[str, Any] = {"stage_id": None, "diagnostics": diagnostics, "subject": None}
    def issue(code: str, message: str) -> None:
        diagnostics.append({"code": code, "message": message})
    try:
        run = rt.read_json(rt.state_path(repo, "run-state.json"), {})
        required = required or bool(run.get("stage_required") or run.get("stage_id"))
        report["required"] = required
        if not required:
            return {**report, "valid": True}
        root = canonical(rt, repo)
        for error in note_errors(rt, repo, root):
            issue("stage-blocking-note", error)
        if not run.get("stage_id"):
            issue("stage-contract-required", "Phase changes do not establish a frozen acceptance contract")
            return {**report, "valid": False}
        directory, envelope = load_stage(rt, repo, run)
        report["stage_id"] = run["stage_id"]
        report["contract_sha256"] = run["stage_contract_sha256"]
        for ref in envelope["inputs"]:
            try:
                if file_ref(root, ref["path"]) != ref:
                    raise ValueError(f"Frozen input or start approval changed: {ref['path']}")
            except (OSError, ValueError) as exc:
                issue("stage-input-changed", str(exc))
        try:
            if approval_record(rt, repo, envelope["start_approval"]["path"]) != envelope["start_approval"]:
                raise ValueError("Frozen start approval changed")
        except (OSError, ValueError) as exc:
            issue("stage-input-changed", str(exc))
        if not include_checks:
            return {**report, "valid": not diagnostics}
        for output in envelope["contract"]["outputs"]:
            try:
                file_ref(root, output)
            except (OSError, ValueError) as exc:
                issue("stage-output-missing", str(exc))
        current = subject(rt, repo, envelope["contract"])
        report["subject"] = current
        latest = {}
        for path in sorted((directory / "checks").glob("*.json")):
            attempt = rt.read_json(path)
            if not attempt or attempt.get("check_id") not in {c["id"] for c in envelope["contract"]["checks"]}:
                raise ValueError(f"Malformed check evidence: {path.name}")
            latest[attempt["check_id"]] = (path, attempt)
        evidence = []
        for check in envelope["contract"]["checks"]:
            if check["id"] not in latest:
                issue("stage-check-missing", f"{check['id']}: no runtime-recorded check attempt")
                continue
            path, attempt = latest[check["id"]]
            receipt = path.with_suffix(".result")
            result = rt.read_json(receipt)
            if (not result or result.get("record_sha256") != digest({k: v for k, v in result.items() if k != "record_sha256"})
                    or result.get("attempt_sha256") != digest(attempt)
                    or attempt.get("contract_sha256") != run["stage_contract_sha256"]
                    or attempt.get("argv") != check["argv"]):
                issue("stage-evidence-corrupt", f"{check['id']}: incomplete or mismatched execution evidence")
                continue
            log = path.with_suffix(".log")
            if not log.is_file() or hashlib.sha256(log.read_bytes()).hexdigest() != result.get("log_sha256"):
                issue("stage-evidence-corrupt", f"{check['id']}: execution log is missing or changed")
            if result.get("returncode") != 0 or result.get("status") != "passed":
                issue("stage-check-failed", f"{check['id']}: latest attempt did not pass")
            if attempt.get("subject") != current or result.get("subject_after") != current:
                issue("stage-check-stale", f"{check['id']}: canonical content differs from the tested subject")
            evidence.append({"check_id": check["id"], "attempt": path.name, "result_sha256": digest(result)})
        report["evidence"] = evidence
        if run.get("status") == "closed":
            completion = rt.read_json(directory / "closure.json")
            if (not completion or completion != run.get("stage_completion")
                    or completion.get("contract_sha256") != run["stage_contract_sha256"]
                    or completion.get("evidence") != evidence):
                issue("stage-evidence-corrupt", "Closed-stage receipt does not match retained completion evidence")
            else:
                approval = completion.get("owner_approval", {})
                try:
                    if approval_record(rt, repo, approval["path"]) != approval:
                        raise ValueError("Closed-stage owner sign-off changed")
                except (OSError, ValueError, KeyError) as exc:
                    issue("stage-approval-changed", str(exc))
    except (OSError, ValueError, TypeError, KeyError, rt.GovernanceError) as exc:
        issue("stage-state-invalid", str(exc))
    return {**report, "valid": not diagnostics}


def run_check(rt: Any, repo: Path, identifier: str) -> dict[str, Any]:
    # Serialize attempts and lifecycle writes. The bounded check must not invoke a
    # mutating governance command recursively (which would wait on this lock).
    with rt.state_lock(repo):
        run = active(rt, repo)
        directory, envelope = load_stage(rt, repo, run)
        readiness = inspect(rt, repo, True, include_checks=False)
        if not readiness["valid"]:
            raise ValueError("; ".join(d["message"] for d in readiness["diagnostics"]))
        check = next((c for c in envelope["contract"]["checks"] if c["id"] == identifier), None)
        if not check:
            raise ValueError("Unknown check ID in frozen contract")
        attempts = sorted((directory / "checks").glob("*.json"))
        sequence = max((int(p.stem) for p in attempts), default=0) + 1
        path = directory / "checks" / f"{sequence:08d}.json"
        before = subject(rt, repo, envelope["contract"])
        attempt = {"check_id": identifier, "argv": check["argv"], "subject": before,
                   "contract_sha256": run["stage_contract_sha256"], "started_at": rt.utc_now()}
        publish(rt, path, attempt)  # An interrupted attempt supersedes an older pass.
        code, status = None, "failed"
        log = path.with_suffix(".log")
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            try:
                process = subprocess.Popen(check["argv"], cwd=canonical(rt, repo), stdin=subprocess.DEVNULL,
                                           stdout=handle, stderr=subprocess.STDOUT, start_new_session=True,
                                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                try:
                    code = process.wait(timeout=check["timeout_seconds"])
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
                status = "passed" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timed-out"
            except OSError:
                status = "could-not-start"
            handle.flush()
            os.fsync(handle.fileno())
        after = subject(rt, repo, envelope["contract"])
        result_record = {"attempt_sha256": digest(attempt), "returncode": code, "status": status,
                         "subject_after": after, "finished_at": rt.utc_now(),
                         "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
        result_record["record_sha256"] = digest(result_record)
        publish(rt, path.with_suffix(".result"), result_record)
        usable = code == 0 and before == after
    return {"check_id": identifier, "passed": usable, "status": status,
            "subject_unchanged": before == after, "evidence": str(path.with_suffix('.result'))}


def cancel(rt: Any, repo: Path, approved: bool, approval_ref: str, reason: str) -> dict[str, Any]:
    if not approved or not ac.meaningful(reason):
        raise ValueError("Cancellation requires --owner-approved and a meaningful --reason")
    with rt.state_lock(repo):
        run = active(rt, repo)
        directory, _ = load_stage(rt, repo, run, check_canonical=False)
        cancellation = {"stage_id": run["stage_id"], "contract_sha256": run["stage_contract_sha256"],
                        "reason": reason.strip(), "approval": approval_record(rt, repo, approval_ref),
                        "cancelled_at": rt.utc_now(), "completed": False}
        previous = rt.read_json(directory / "cancellation.json")
        if previous:
            if any(previous.get(key) != cancellation[key] for key in cancellation if key != "cancelled_at"):
                raise ValueError("Interrupted cancellation differs; inspect the retained record before retrying")
            cancellation = previous
        else:
            publish(rt, directory / "cancellation.json", cancellation)
        run.setdefault("stage_history", []).append(cancellation)
        run.pop("stage_id")
        run.pop("stage_contract_sha256")
        run["stage_required"] = True
        rt.atomic_write_json(rt.state_path(repo, "run-state.json"), run)
    return {"cancelled": True, "completed": False, "stage_id": cancellation["stage_id"]}
