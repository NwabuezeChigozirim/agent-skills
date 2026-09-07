"""Wave 4 tests exercise actual opt-in closure, not just the unreleased-policy gate."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from test_review_regressions import rt, gc
from test_policy_upgrade import tree_state


class StageContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = rt.GovernanceRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.repo = self.fixture.repo
        rt.ctl(self.repo, "discover")
        (self.repo / "intent.txt").write_text("Preserve the existing recorded item.\n")
        (self.repo / "start.txt").write_text("Owner approves this fixture's stage scope and required check.\n")
        (self.repo / "signoff.txt").write_text("Owner sign-off reference; authorization is supplied explicitly at closure.\n")
        self.contract = {"version": 1, "name": "Recorded item", "scope": "Verify the existing app item only",
                         "inputs": ["intent.txt"], "outputs": ["app.txt"],
                         "acceptance": [{"id": "AC-001", "description": "The existing item remains readable",
                                         "checks": ["CHK-001"]}],
                         "checks": [{"id": "CHK-001", "argv": [sys.executable, "-c",
                                     "from pathlib import Path; assert Path('app.txt').read_text(); print('checked')"],
                                     "timeout_seconds": 5}]}
        self.write_contract()

    def write_contract(self):
        (self.repo / "stage.json").write_text(json.dumps(self.contract))

    def freeze(self, check=True):
        return rt.ctl(self.repo, "freeze-stage", "--contract", "stage.json", "--owner-approved",
                      "--approval-ref", "start.txt", check=check)

    def check(self, identifier="CHK-001", check=True):
        return rt.ctl(self.repo, "run-check", "--id", identifier, check=check)

    def inspect(self, current=False):
        args = ["--policy", "current"] if current else []
        return json.loads(rt.ctl(self.repo, "check-stage", *args, check=False).stdout)

    def codes(self, current=False):
        return {d["code"] for d in self.inspect(current)["stage"]["diagnostics"]}

    def close(self, check=True):
        return rt.ctl(self.repo, "close-stage", "--owner-approved", "--approval-ref", "signoff.txt", check=check)

    def stage_dir(self):
        run = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        return gc.state_dir(self.repo) / "stages" / run["stage_id"]

    def test_clean_current_preview_is_read_only_but_unreleased(self):
        self.freeze()
        self.check()
        before = tree_state(self.repo)
        result = self.inspect(True)
        self.assertTrue(result["stage_valid"], result)
        self.assertFalse(result["valid"])
        self.assertFalse(result["policy_enforcement_ready"])
        self.assertEqual(before, tree_state(self.repo))

    def test_real_opt_in_closure_binds_evidence_and_owner_approval(self):
        self.freeze()
        self.check()
        self.close()
        run = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        completion = run["stage_completion"]
        self.assertEqual(run["status"], "closed")
        self.assertEqual(completion["contract_sha256"], run["stage_contract_sha256"])
        self.assertEqual(completion["subject"], gc.stages.subject(gc, self.repo, self.contract))
        self.assertEqual(completion["evidence"][0]["check_id"], "CHK-001")
        self.assertEqual(completion["owner_approval"]["path"], "signoff.txt")
        before = tree_state(self.repo)
        self.assertTrue(json.loads(self.close().stdout)["already_closed"])
        self.assertEqual(before, tree_state(self.repo))
        for path in self.stage_dir().rglob("*"):
            if path.is_file():
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        (self.repo / "signoff.txt").write_text("Changed approval record")
        self.assertIn("stage-approval-changed", self.codes())

    def test_phase_does_not_supply_a_contract_and_legacy_is_preserved(self):
        rt.ctl(self.repo, "phase", "handoff")
        self.assertIn("stage-contract-required", self.codes(True))
        self.assertTrue(self.inspect()["valid"])
        self.assertTrue(json.loads(rt.ctl(self.repo, "close-stage", "--owner-approved").stdout)["closed"])

    def test_missing_check_blocks_actual_closure(self):
        self.freeze()
        self.assertIn("stage-check-missing", self.codes())
        result = self.close(False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertIn("stage-check-missing", result.stdout)

    def test_failed_check_and_later_failed_attempt_cannot_reuse_a_pass(self):
        self.contract["checks"][0]["argv"] = [sys.executable, "-c",
            "from pathlib import Path; import sys; sys.exit(1 if Path('fail.txt').exists() else 0)"]
        self.write_contract()
        self.freeze()
        self.check()
        (self.repo / "fail.txt").write_text("fail now")
        self.assertEqual(self.check(check=False).returncode, gc.EXIT_VALIDATION)
        (self.repo / "fail.txt").unlink()
        self.assertIn("stage-check-failed", self.codes())
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)

    def test_same_head_changes_and_staging_only_changes_make_evidence_stale(self):
        self.freeze()
        self.check()
        head = gc.current_head(self.repo)
        (self.repo / "app.txt").write_text("changed item\n")
        self.assertEqual(gc.current_head(self.repo), head)
        self.assertIn("stage-check-stale", self.codes())
        self.check()
        self.assertTrue(self.inspect()["valid"])
        rt.run(["git", "add", "app.txt"], self.repo)
        self.assertIn("stage-check-stale", self.codes())
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)

    def test_changed_inputs_cannot_be_reapproved_by_rerunning_checks(self):
        self.freeze()
        self.check()
        (self.repo / "intent.txt").write_text("Different scope\n")
        self.assertIn("stage-input-changed", self.codes())
        self.assertEqual(self.check(check=False).returncode, gc.EXIT_GATE)
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)

    def test_missing_outputs_block_despite_a_successful_command(self):
        self.contract["outputs"] = ["delivery.txt"]
        self.write_contract()
        self.freeze()
        self.check()
        self.assertIn("stage-output-missing", self.codes())
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)

    def test_owner_flags_and_references_are_separate_requirements(self):
        before = tree_state(self.repo)
        result = rt.ctl(self.repo, "freeze-stage", "--contract", "stage.json", "--approval-ref", "start.txt", check=False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertEqual(before, tree_state(self.repo))
        self.freeze()
        self.check()
        self.assertEqual(rt.ctl(self.repo, "close-stage", "--owner-approved", check=False).returncode, gc.EXIT_GATE)
        self.assertEqual(rt.ctl(self.repo, "close-stage", "--approval-ref", "signoff.txt", check=False).returncode, gc.EXIT_GATE)
        (self.repo / "signoff.txt").write_text("")
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)

    def test_freeze_is_idempotent_but_never_silently_replaces_scope(self):
        self.freeze()
        before = tree_state(self.repo)
        self.assertFalse(json.loads(self.freeze().stdout)["changed"])
        self.assertEqual(before, tree_state(self.repo))
        self.contract["scope"] = "Broader work"
        self.write_contract()
        self.assertEqual(self.freeze(False).returncode, gc.EXIT_GATE)

    def test_cancel_retains_history_and_cannot_disable_contract_requirement(self):
        self.freeze()
        directory = self.stage_dir()
        original = (directory / "contract.json").read_bytes()
        with patch.object(gc, "atomic_write_json", side_effect=OSError("pointer write interrupted")):
            with self.assertRaises(OSError):
                gc.stages.cancel(gc, self.repo, True, "signoff.txt", "Input assumption changed")
        cancellation = (directory / "cancellation.json").read_bytes()
        rt.ctl(self.repo, "cancel-stage", "--owner-approved", "--approval-ref", "signoff.txt", "--reason", "Input assumption changed")
        self.assertEqual(cancellation, (directory / "cancellation.json").read_bytes())
        self.assertEqual((directory / "contract.json").read_bytes(), original)
        self.assertFalse(gc.read_json(directory / "cancellation.json")["completed"])
        self.assertIn("stage-contract-required", self.codes())
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)
        self.freeze()
        self.assertNotEqual(self.stage_dir(), directory)
        self.check()
        self.close()

    def test_blocking_intent_needs_a_current_ratified_decision(self):
        rt.ctl(self.repo, "note", "--kind", "blocking", "--text", "Owner acceptance uncertain")
        self.freeze()
        self.assertIn("stage-blocking-note", self.codes())
        self.assertEqual(self.check(check=False).returncode, gc.EXIT_GATE)
        (self.repo / "DECISIONS.md").write_text("| D-001 | proposed | accept item |\n")
        args = ["resolve-note", "--id", "N-001", "--decision", "D-001", "--note", "Owner agreed acceptance", "--owner-approved"]
        self.assertEqual(rt.ctl(self.repo, *args, check=False).returncode, gc.EXIT_GATE)
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted | accept item |\n")
        rt.ctl(self.repo, *args)
        self.assertNotIn("stage-blocking-note", self.codes())
        rt.ctl(self.repo, "discover")
        self.assertNotIn("stage-blocking-note", self.codes())
        before = tree_state(self.repo)
        self.assertFalse(json.loads(rt.ctl(self.repo, *args).stdout)["changed"])
        self.assertEqual(before, tree_state(self.repo))
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted | different acceptance |\n")
        self.assertIn("stage-blocking-note", self.codes())

    def test_nonblocking_observations_do_not_create_approval_ceremony(self):
        rt.ctl(self.repo, "note", "--kind", "observation", "--text", "The item is readable", "--evidence", "app.txt")
        self.freeze()
        self.check()
        self.close()

    def test_corrupt_frozen_contract_logs_and_receipts_fail_closed(self):
        self.freeze()
        self.check()
        directory = self.stage_dir()
        log = next((directory / "checks").glob("*.log"))
        original_log = log.read_bytes()
        log.write_bytes(b"tampered")
        self.assertIn("stage-evidence-corrupt", self.codes())
        log.write_bytes(original_log)
        receipt = next((directory / "checks").glob("*.result"))
        original_receipt = receipt.read_bytes()
        record = json.loads(original_receipt)
        record["finished_at"] = "changed"
        receipt.write_text(json.dumps(record))
        self.assertIn("stage-evidence-corrupt", self.codes())
        receipt.write_bytes(original_receipt)
        contract = directory / "contract.json"
        record = json.loads(contract.read_bytes())
        record["contract"]["outputs"] = []
        contract.write_text(json.dumps(record))
        self.assertIn("stage-state-invalid", self.codes())

    def test_interrupted_attempt_supersedes_previous_success(self):
        self.freeze()
        self.check()
        original = gc.stages.subprocess.Popen
        def interrupt_check(command, *args, **kwargs):
            if command == self.contract["checks"][0]["argv"]:
                raise RuntimeError("interrupted")
            return original(command, *args, **kwargs)
        with patch.object(gc.stages.subprocess, "Popen", side_effect=interrupt_check):
            with self.assertRaises(RuntimeError):
                gc.stages.run_check(gc, self.repo, "CHK-001")
        self.assertIn("stage-evidence-corrupt", self.codes())
        self.assertEqual(self.close(False).returncode, gc.EXIT_GATE)
        self.check()
        self.close()

    def test_mutating_check_cannot_certify_its_post_change_content(self):
        self.contract["checks"][0]["argv"] = [sys.executable, "-c", "from pathlib import Path; Path('app.txt').write_text('changed')"]
        self.write_contract()
        self.freeze()
        result = self.check(check=False)
        self.assertEqual(result.returncode, gc.EXIT_VALIDATION)
        self.assertFalse(json.loads(result.stdout)["subject_unchanged"])
        self.assertIn("stage-check-stale", self.codes())

    def test_timeout_is_a_recorded_failure_not_missing_success(self):
        self.contract["checks"][0].update(argv=[sys.executable, "-c", "import time; time.sleep(10)"], timeout_seconds=1)
        self.write_contract()
        self.freeze()
        result = self.check(check=False)
        self.assertEqual(json.loads(result.stdout)["status"], "timed-out")
        self.assertIn("stage-check-failed", self.codes())

    def test_all_acceptance_checks_are_required(self):
        self.contract["checks"].append({**self.contract["checks"][0], "id": "CHK-002"})
        self.contract["acceptance"][0]["checks"].append("CHK-002")
        self.write_contract()
        self.freeze()
        self.check()
        self.assertIn("stage-check-missing", self.codes())
        self.check("CHK-002")
        self.close()

    def test_path_escape_symlink_and_unknown_contract_fields_are_rejected(self):
        for field, value in (("inputs", ["../outside.txt"]), ("outputs", [".git/config"]), ("outputs", [str(self.repo / "app.txt")])):
            with self.subTest(field=field, value=value):
                original = self.contract[field]
                self.contract[field] = value
                self.write_contract()
                self.assertNotEqual(self.freeze(False).returncode, 0)
                self.contract[field] = original
        (self.repo / "linked.txt").symlink_to(self.repo / "intent.txt")
        self.contract["inputs"] = ["linked.txt"]
        self.write_contract()
        self.assertNotEqual(self.freeze(False).returncode, 0)
        self.contract["inputs"] = ["intent.txt"]
        self.contract["unknown"] = "typo"
        self.write_contract()
        self.assertNotEqual(self.freeze(False).returncode, 0)

    def test_invalid_acceptance_and_check_declarations_cannot_be_frozen(self):
        for mutate in (lambda c: c.update(acceptance=[]), lambda c: c["acceptance"][0].update(description="TBD"),
                       lambda c: c["acceptance"][0].update(checks=["CHK-999"]),
                       lambda c: c["checks"][0].update(argv="echo passed"),
                       lambda c: c["checks"][0].update(timeout_seconds=True)):
            with self.subTest(mutate=mutate):
                value = json.loads(json.dumps(self.contract))
                mutate(value)
                self.assertTrue(gc.stages.contract_errors(value))

    def test_policy_two_execution_remains_disabled(self):
        config_path = gc.config_path(self.repo)
        config = gc.read_json(config_path)
        config["policy_version"] = 2
        config_path.write_text(json.dumps(config))
        before = tree_state(self.repo)
        self.assertEqual(self.freeze(False).returncode, gc.EXIT_GATE)
        self.assertEqual(before, tree_state(self.repo))

    def test_uninitialized_preview_does_not_create_runtime_state(self):
        fixture = rt.GovernanceRuntimeTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        before = tree_state(fixture.repo)
        report = json.loads(rt.ctl(fixture.repo, "check-stage", "--policy", "current", check=False).stdout)
        self.assertIn("stage-contract-required", {d["code"] for d in report["stage"]["diagnostics"]})
        self.assertEqual(before, tree_state(fixture.repo))

    def test_validate_reports_stage_findings_without_executing_checks(self):
        self.freeze()
        before = tree_state(self.repo)
        report = json.loads(rt.ctl(self.repo, "validate", check=False).stdout)
        self.assertIn("stage-check-missing", {d["code"] for d in report["stage"]["diagnostics"]})
        self.assertEqual(before, tree_state(self.repo))
        audit = json.loads(rt.ctl(self.repo, "audit", check=False).stdout)
        self.assertFalse(audit["runtime_validation"]["stage_valid"])
        self.assertEqual(before, tree_state(self.repo))
        self.check()
        report = json.loads(rt.ctl(self.repo, "validate", "--policy", "current", check=False).stdout)
        self.assertTrue(report["artifact_valid"], report["errors"])
        self.assertTrue(report["stage_valid"])
        self.assertFalse(report["valid"])

    def test_unknown_check_and_missing_executable_do_not_claim_success(self):
        self.contract["checks"][0]["argv"] = [str(self.repo / "absent-executable")]
        self.write_contract()
        self.freeze()
        self.assertEqual(self.check("CHK-999", False).returncode, gc.EXIT_GATE)
        result = json.loads(self.check(check=False).stdout)
        self.assertEqual(result["status"], "could-not-start")
        self.assertIn("stage-check-failed", self.codes())

    def test_contract_freeze_publication_failure_does_not_activate_a_partial_contract(self):
        before = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        with patch.object(gc.stages.os, "link", side_effect=OSError("publication interrupted")):
            with self.assertRaises(OSError):
                gc.stages.freeze(gc, self.repo, "stage.json", True, "start.txt")
        self.assertEqual(before, gc.read_json(gc.state_path(self.repo, "run-state.json")))
        self.assertIn("stage-contract-required", self.codes(True))
        self.freeze()

    def test_interrupted_closure_can_resume_without_overwriting_receipt(self):
        self.freeze()
        self.check()
        original = gc.atomic_write_json
        def fail_close(path, value, **kwargs):
            if path.name == "run-state.json" and value.get("status") == "closed":
                raise OSError("closure publication interrupted")
            return original(path, value, **kwargs)
        with patch.object(gc, "atomic_write_json", side_effect=fail_close):
            with self.assertRaises(OSError):
                gc.command_close_stage(self.repo, True, "signoff.txt")
        receipt = (self.stage_dir() / "closure.json").read_bytes()
        self.close()
        self.assertEqual(receipt, (self.stage_dir() / "closure.json").read_bytes())

    def test_existing_worktree_gates_still_block_a_fully_checked_stage(self):
        self.freeze()
        self.check()
        sibling = self.fixture.add_sibling()
        (sibling / "app.txt").write_text("unreviewed variant\n")
        result = self.close(False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertIn("Unresolved worktree resolution records", result.stdout)

    def test_canonical_change_requires_new_contract_but_allows_explicit_cancellation(self):
        self.freeze()
        sibling = self.fixture.add_sibling()
        (sibling / "approval.txt").write_text("Owner authorizes cancellation after canonical selection changed.")
        rt.ctl(self.repo, "set-canonical", "--path", str(sibling))
        self.assertIn("stage-state-invalid", self.codes())
        result = rt.ctl(self.repo, "cancel-stage", "--owner-approved", "--approval-ref", "approval.txt", "--reason", "Canonical worktree changed")
        self.assertTrue(json.loads(result.stdout)["cancelled"])

    def test_needs_owner_blocks_but_incidental_decision_citation_cannot_resolve_it(self):
        rt.ctl(self.repo, "note", "--kind", "needs-owner", "--text", "Confirm scope")
        (self.repo / "DECISIONS.md").write_text("D-001 might settle the issue later.")
        self.freeze()
        result = rt.ctl(self.repo, "resolve-note", "--id", "N-001", "--decision", "D-001", "--note", "Assumed settled", "--owner-approved", check=False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertIn("stage-blocking-note", self.codes())

    def test_ignored_declared_output_changes_are_still_evidence_changes(self):
        (self.repo / ".gitignore").write_text("delivery.txt\n")
        (self.repo / "delivery.txt").write_text("first result")
        self.contract["outputs"].append("delivery.txt")
        self.write_contract()
        self.freeze()
        self.check()
        fingerprint = gc.stages.subject(gc, self.repo)["content_fingerprint"]
        (self.repo / "delivery.txt").write_text("different result")
        self.assertEqual(fingerprint, gc.stages.subject(gc, self.repo)["content_fingerprint"])
        self.assertIn("stage-check-stale", self.codes())

    def test_external_owner_signoff_can_follow_checks_without_changing_tested_content(self):
        self.freeze()
        self.check()
        external = self.repo.parent / "owner-signoff.txt"
        external.write_text("Owner reviewed this stage's actual successful results and approved closure.")
        result = rt.ctl(self.repo, "close-stage", "--owner-approved", "--approval-ref", str(external))
        self.assertTrue(json.loads(result.stdout)["closed"])


if __name__ == "__main__":
    unittest.main()
