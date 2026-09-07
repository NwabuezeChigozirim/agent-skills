"""Wave 5: impact review is read-only; revision preserves authority and evidence."""

from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_stage_contracts as fixtures
from test_review_regressions import rt, gc, fx, pt
from test_policy_upgrade import tree_state


class ChangeImpactTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.StageContractTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.repo
        self.review_path = self.repo.parent / "impact-review.json"

    def report(self, current=False):
        args = ["--policy", "current"] if current else []
        return json.loads(rt.ctl(self.repo, "stage-impact", "--contract", "stage.json", *args, check=False).stdout)

    def review(self):
        report = self.report()["impact"]
        review = {"version": 1, "impact_sha256": report["impact_sha256"],
                  "rationale": "Owner reviewed the updated agreement and affected engineering work",
                  "activities": {a: "Re-enter or review this activity within the approved revised scope" for a in report["reentry"]},
                  "retirements": {r: "Owner explicitly removes this obligation in the revised scope" for r in report["retired_obligations"]},
                  "uncertainty": "Owner reviewed incomplete graph/baseline coverage" if report["uncertainty"] else ""}
        self.review_path.write_text(json.dumps(review))
        return report, review

    def revise(self, check=True, reopen=False):
        args = ["--reopen"] if reopen else []
        return rt.ctl(self.repo, "revise-stage", "--contract", "stage.json", "--review", str(self.review_path),
                      "--owner-approved", "--approval-ref", "signoff.txt", "--reason", "New evidence changes the agreed input", *args, check=check)

    def graph_fixture(self):
        docs = self.repo / "docs"
        docs.mkdir(exist_ok=True)
        waves = docs / "waves"
        waves.mkdir()
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted | owner baseline |\n")
        (docs / "sample-CON.md").write_text(fx.con())
        (docs / "sample-FSD.md").write_text(fx.fsd())
        (docs / "sample-TSD.md").write_text(fx.tsd())
        (waves / "README.md").write_text(pt.wave_index())
        (waves / "wave-1-auth.md").write_text(pt.brief())
        config = gc.read_json(gc.config_path(self.repo))
        config["project_slug"] = "sample"
        gc.atomic_write_json(gc.config_path(self.repo), config)
        return docs, waves

    def test_impact_is_deterministic_read_only_and_not_policy_adoption(self):
        self.fixture.freeze()
        before = tree_state(self.repo)
        result = self.report()
        self.assertTrue(result["analysis_valid"])
        self.assertFalse(result["acceptance_checked"])
        self.assertFalse(result["impact"]["reuse_check_evidence"])
        self.assertFalse(any(result["impact"]["changed_artifacts"].values()))
        self.assertEqual(result, self.report())
        current = self.report(True)
        self.assertTrue(current["analysis_valid"])
        self.assertFalse(current["valid"])
        self.assertEqual(before, tree_state(self.repo))

    def test_real_revision_preserves_predecessor_and_requires_fresh_checks(self):
        self.fixture.freeze()
        self.fixture.check()
        old_directory = self.fixture.stage_dir()
        old_files = {p.relative_to(old_directory): p.read_bytes() for p in old_directory.rglob("*") if p.is_file()}
        rt.ctl(self.repo, "phase", "handoff")
        (self.repo / "intent.txt").write_text("Owner-approved clarified acceptance\n")
        self.review()
        result = json.loads(self.revise().stdout)
        self.assertTrue(result["checks_invalidated"])
        self.assertNotEqual(self.fixture.stage_dir(), old_directory)
        self.assertEqual(old_files, {p.relative_to(old_directory): p.read_bytes() for p in old_directory.rglob("*") if p.is_file()})
        run = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        self.assertEqual(run["phase"], "handoff")
        self.assertIn("rerun every required check", run["next_action"])
        self.assertEqual(run["stage_history"][-1]["status"], "superseded")
        self.assertFalse(run["stage_history"][-1]["completed"])
        self.assertIn("stage-check-missing", self.fixture.codes())
        self.assertEqual(self.fixture.close(False).returncode, gc.EXIT_GATE)
        self.fixture.check()
        self.fixture.close()

    def test_requirement_change_reaches_technical_and_dependent_slices(self):
        docs, waves = self.graph_fixture()
        brief = waves / "wave-1-auth.md"
        brief.write_text(pt.brief(slices=pt.slice_block() + pt.slice_block("W1-S2").replace("**Depends on:** none", "**Depends on:** W1-S1")))
        self.fixture.freeze()
        path = docs / "sample-FSD.md"
        path.write_text(path.read_text().replace("- **Done when:** value", "- **Done when:** denial is explicit"))
        report = self.report()["impact"]
        affected = {n["id"] for n in report["affected"]}
        self.assertTrue({"F-001", "T-001", "W1-S1", "W1-S2", "W1"} <= affected)
        self.assertIn("F-001", report["changed_definitions"]["modified"])
        self.assertTrue({"specification", "planning", "validation"} <= set(report["reentry"]))

    def test_deleted_edges_still_propagate_through_the_previous_graph(self):
        docs, _ = self.graph_fixture()
        self.fixture.freeze()
        (docs / "sample-FSD.md").unlink()
        report = self.report()["impact"]
        self.assertIn("docs/sample-FSD.md", report["changed_artifacts"]["removed"])
        self.assertIn("F-001", report["changed_definitions"]["removed"])
        self.assertIn("definitions:F-001", report["retired_obligations"])
        self.assertTrue({"T-001", "W1-S1"} <= {n["id"] for n in report["affected"]})
        self.assertTrue(report["uncertainty"])

    def test_compact_decision_text_change_is_not_mistaken_for_unchanged_status(self):
        self.graph_fixture()
        self.fixture.freeze()
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted | different owner baseline |\n")
        report = self.report()["impact"]
        self.assertIn("D-001", report["changed_definitions"]["modified"])
        self.assertTrue({"C-001", "F-001", "T-001"} <= {n["id"] for n in report["affected"]})

    def test_technical_reference_change_reaches_its_wave(self):
        docs, _ = self.graph_fixture()
        self.fixture.freeze()
        path = docs / "sample-TSD.md"
        path.write_text(path.read_text().replace("- **Verification:** value", "- **Verification:** contract tests"))
        self.assertTrue({"T-001", "W1", "W1-S1"} <= {n["id"] for n in self.report()["impact"]["affected"]})

    def test_unmodeled_prose_is_conservative_not_a_harmless_change_claim(self):
        docs, _ = self.graph_fixture()
        self.fixture.freeze()
        path = docs / "sample-FSD.md"
        path.write_text(path.read_text() + "\n## Additional constraint\nExisting acceptance also applies when offline.\n")
        report = self.report()["impact"]
        self.assertFalse(report["changed_definitions"]["modified"])
        self.assertIn("W1-S1", {n["id"] for n in report["affected"]})
        self.assertEqual(report["precision"], "conservative-file-and-graph")

    def test_stale_review_cannot_authorize_a_new_input_version(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("First revision\n")
        self.review()
        (self.repo / "intent.txt").write_text("Unreviewed second revision\n")
        before = tree_state(self.repo)
        result = self.revise(False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertIn("stale", result.stdout)
        self.assertEqual(before, tree_state(self.repo))

    def test_changed_proposed_checks_invalidate_the_review(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        self.fixture.contract["checks"][0]["argv"] = ["unexpected-command"]
        self.fixture.write_contract()
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)

    def test_retired_acceptance_checks_inputs_and_outputs_need_explicit_rationale(self):
        (self.repo / "extra.txt").write_text("Additional agreed input/output")
        contract = self.fixture.contract
        contract["inputs"].append("extra.txt")
        contract["outputs"].append("extra.txt")
        contract["checks"].append({**contract["checks"][0], "id": "CHK-002"})
        contract["acceptance"].append({"id": "AC-002", "description": "The additional promise", "checks": ["CHK-002"]})
        self.fixture.write_contract()
        self.fixture.freeze()
        contract["inputs"].remove("extra.txt")
        contract["outputs"].remove("extra.txt")
        contract["checks"].pop()
        contract["acceptance"].pop()
        self.fixture.write_contract()
        report, review = self.review()
        self.assertEqual(set(report["retired_obligations"]), {"inputs:extra.txt", "outputs:extra.txt", "checks:CHK-002", "acceptance:AC-002"})
        review["retirements"] = {}
        self.review_path.write_text(json.dumps(review))
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)
        self.review()
        self.revise()

    def test_missing_reentry_rationale_is_not_implicit_approval(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        _, review = self.review()
        review["activities"].pop("intent")
        self.review_path.write_text(json.dumps(review))
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)

    def test_historical_hash_only_contract_is_honest_and_can_be_revised_explicitly(self):
        self.fixture.freeze()
        path = self.fixture.stage_dir() / "contract.json"
        envelope = gc.read_json(path)
        envelope.pop("impact_baseline")
        gc.atomic_write_json(path, envelope)
        run_path = gc.state_path(self.repo, "run-state.json")
        run = gc.read_json(run_path)
        run["stage_contract_sha256"] = gc.stages.digest(envelope)
        gc.atomic_write_json(run_path, run)
        report, review = self.review()
        self.assertEqual(report["precision"], "historical-baseline-missing")
        self.assertTrue(report["uncertainty"])
        review["uncertainty"] = ""
        self.review_path.write_text(json.dumps(review))
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)
        self.review()
        self.revise()
        self.assertEqual(self.report()["impact"]["precision"], "conservative-file-and-graph")

    def test_deleted_declared_input_is_reported_and_can_be_explicitly_replaced(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").unlink()
        report = self.report()["impact"]
        self.assertIn("intent.txt", report["changed_artifacts"]["removed"])
        (self.repo / "new-intent.txt").write_text("Replacement agreed constraint")
        self.fixture.contract["inputs"] = ["new-intent.txt"]
        self.fixture.write_contract()
        self.review()
        self.revise()

    def test_revision_requires_actual_owner_flag_and_never_runs_checks(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        before = tree_state(self.repo)
        result = rt.ctl(self.repo, "revise-stage", "--contract", "stage.json", "--review", str(self.review_path),
                        "--approval-ref", "signoff.txt", "--reason", "Reviewed input change", check=False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertEqual(before, tree_state(self.repo))
        self.revise()
        self.assertFalse((self.fixture.stage_dir() / "checks").exists())

    def test_identical_revision_retry_is_read_only(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        self.revise()
        before = tree_state(self.repo)
        self.assertFalse(json.loads(self.revise().stdout)["changed"])
        self.assertEqual(before, tree_state(self.repo))

    def test_no_change_does_not_manufacture_revision_history(self):
        self.fixture.freeze()
        self.review()
        result = self.revise(False)
        self.assertEqual(result.returncode, gc.EXIT_GATE)
        self.assertIn("No contract or recorded context change", result.stdout)

    def test_new_findings_change_the_review_without_becoming_accepted_intent(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        rt.ctl(self.repo, "note", "--kind", "hypothesis", "--text", "Offline use may matter")
        report = self.report()["impact"]
        self.assertIn("N-001", report["changed_findings"]["added"])
        self.assertIn("discovery", report["reentry"])
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)
        self.assertEqual(gc.discovery_notes(self.repo)[0]["evidence_class"], "hypothesis")

    def test_publication_failure_preserves_the_active_predecessor(self):
        self.fixture.freeze()
        old = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        with patch.object(gc, "atomic_write_json", side_effect=OSError("pointer interrupted")):
            with self.assertRaises(OSError):
                gc.impact.revise(gc, self.repo, "stage.json", str(self.review_path), True, "signoff.txt", "New evidence changes the agreed input")
        self.assertEqual(old, gc.read_json(gc.state_path(self.repo, "run-state.json")))
        self.revise()
        self.assertEqual(len(gc.read_json(gc.state_path(self.repo, "run-state.json"))["stage_history"]), 1)

    def test_changed_artifacts_during_publication_are_rejected(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        original = gc.impact.snapshot
        count = 0
        def race(*args, **kwargs):
            nonlocal count
            count += 1
            if count == 2:
                (self.repo / "intent.txt").write_text("Changed during review")
            return original(*args, **kwargs)
        with patch.object(gc.impact, "snapshot", side_effect=race):
            with self.assertRaisesRegex(ValueError, "Artifacts changed"):
                gc.impact.revise(gc, self.repo, "stage.json", str(self.review_path), True, "signoff.txt", "New evidence changes the agreed input")

    def test_missing_predecessor_is_not_an_intact_revision_chain(self):
        self.fixture.freeze()
        old = self.fixture.stage_dir() / "contract.json"
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        self.revise()
        old.unlink()
        self.assertIn("stage-state-invalid", self.fixture.codes())

    def test_policy_two_revision_stays_disabled(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised input\n")
        self.review()
        config = gc.read_json(gc.config_path(self.repo))
        config["policy_version"] = 2
        gc.atomic_write_json(gc.config_path(self.repo), config)
        before = tree_state(self.repo)
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)
        self.assertEqual(before, tree_state(self.repo))

    def test_valid_graph_baseline_has_no_manufactured_uncertainty(self):
        self.graph_fixture()
        self.fixture.freeze()
        report = self.report()["impact"]
        self.assertFalse(report["graph_diagnostics"], report["graph_diagnostics"])
        self.assertFalse(report["uncertainty"])
        self.assertFalse(report["affected"])

    def test_nfr_measure_change_propagates_like_functional_requirements(self):
        docs, _ = self.graph_fixture()
        nfr = "## Non-functional outcomes\n| ID | Outcome | Serves | Measure | Verification |\n|---|---|---|---|---|\n| F-NFR-001 | Access is controlled | UN-001 | Every denial is explicit | Denial tests |\n"
        (docs / "sample-FSD.md").write_text(fx.fsd(extra=nfr))
        (docs / "sample-TSD.md").write_text(fx.tsd(realizes="F-001, F-NFR-001", trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-NFR-001 | UN-001 | T-001 | denial tests |"))
        self.fixture.freeze()
        path = docs / "sample-FSD.md"
        path.write_text(path.read_text().replace("Every denial is explicit", "Every request is authorized"))
        report = self.report()["impact"]
        self.assertIn("F-NFR-001", report["changed_definitions"]["modified"])
        self.assertTrue({"T-001", "W1-S1"} <= {n["id"] for n in report["affected"]})

    def test_ratified_no_con_baseline_decision_reaches_user_needs(self):
        docs, _ = self.graph_fixture()
        (docs / "sample-CON.md").unlink()
        (docs / "sample-FSD.md").write_text(rt.VALID_FSD)
        (docs / "sample-TSD.md").write_text(rt.VALID_TSD)
        self.fixture.freeze()
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted | revised user baseline |\n")
        self.assertTrue({"UN-001", "F-001", "T-001"} <= {n["id"] for n in self.report()["impact"]["affected"]})

    def test_revision_never_writes_the_owned_specifications_or_plan(self):
        docs, _ = self.graph_fixture()
        self.fixture.freeze()
        path = docs / "sample-FSD.md"
        path.write_text(path.read_text().replace("- **Done when:** value", "- **Done when:** denied requests stay denied"))
        self.review()
        before = {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()}
        self.revise()
        self.assertEqual(before, {p.relative_to(docs): p.read_bytes() for p in docs.rglob("*") if p.is_file()})

    def test_multiple_revisions_have_verifiable_lineage_and_no_evidence_inheritance(self):
        self.fixture.freeze()
        ancestors = [self.fixture.stage_dir()]
        for index in range(2):
            (self.repo / "intent.txt").write_text(f"Owner-approved revision {index}\n")
            self.review()
            self.revise()
            ancestors.append(self.fixture.stage_dir())
        self.assertEqual(len(set(ancestors)), 3)
        self.assertTrue(all((p / "contract.json").is_file() for p in ancestors))
        self.assertIn("stage-check-missing", self.fixture.codes())
        self.fixture.check()
        self.fixture.close()

    def test_revision_approval_does_not_resolve_a_blocking_finding(self):
        self.fixture.freeze()
        rt.ctl(self.repo, "note", "--kind", "blocking", "--text", "Acceptance still needs a decision")
        self.review()
        self.revise()
        self.assertIn("stage-blocking-note", self.fixture.codes())
        self.assertEqual(self.fixture.check(check=False).returncode, gc.EXIT_GATE)

    def test_missing_graph_helper_is_not_silently_partial_analysis(self):
        self.graph_fixture()
        with patch.object(gc, "find_skill_root", return_value=self.repo / "uninstalled/governance-system"):
            with self.assertRaisesRegex(ValueError, "unavailable"):
                gc.stages.freeze(gc, self.repo, "stage.json", True, "start.txt")
        self.assertFalse(gc.read_json(gc.state_path(self.repo, "run-state.json")).get("stage_id"))

    def test_completed_work_reopens_only_explicitly_without_erasing_earlier_acceptance(self):
        self.fixture.freeze()
        self.fixture.check()
        self.fixture.close()
        old_directory = self.fixture.stage_dir()
        closure = (old_directory / "closure.json").read_bytes()
        old_run = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        (self.repo / "intent.txt").write_text("Later evidence changes the accepted scope\n")
        self.review()
        self.assertEqual(self.revise(False).returncode, gc.EXIT_GATE)
        result = json.loads(self.revise(reopen=True).stdout)
        self.assertTrue(result["reopened"])
        run = gc.read_json(gc.state_path(self.repo, "run-state.json"))
        self.assertEqual(run["status"], "active")
        self.assertNotEqual(run["run_id"], old_run["run_id"])
        self.assertFalse(run["owner_close_approved"])
        self.assertNotIn("stage_completion", run)
        self.assertTrue(run["stage_history"][-1]["completed"])
        self.assertEqual(closure, (old_directory / "closure.json").read_bytes())
        self.assertIn("stage-check-missing", self.fixture.codes())
        before = tree_state(self.repo)
        self.assertFalse(json.loads(self.revise(reopen=True).stdout)["changed"])
        self.assertEqual(before, tree_state(self.repo))
        self.fixture.check()
        self.fixture.close()

    def test_reopen_cannot_bypass_a_missing_historical_closure_receipt(self):
        self.fixture.freeze()
        self.fixture.check()
        self.fixture.close()
        (self.repo / "intent.txt").write_text("Later revised scope\n")
        self.review()
        (self.fixture.stage_dir() / "closure.json").unlink()
        self.assertEqual(self.revise(False, True).returncode, gc.EXIT_GATE)

    def test_reopen_flag_cannot_reset_an_already_active_run(self):
        self.fixture.freeze()
        (self.repo / "intent.txt").write_text("Revised scope\n")
        self.review()
        before = tree_state(self.repo)
        self.assertEqual(self.revise(False, True).returncode, gc.EXIT_GATE)
        self.assertEqual(before, tree_state(self.repo))


if __name__ == "__main__":
    unittest.main()
