"""Wave 3: graph findings, never release-gate errors, prove enforcement."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_review_regressions as regressions
from test_review_regressions import fx, vs, tc, pt
from test_policy_upgrade import tree_state


class SpecificationGraphTests(unittest.TestCase):
    def setUp(self):
        self.fixture = regressions.SpecificationRegressions()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo = self.fixture.repo

    def validate(self):
        return vs.validate_repository(self.repo, "sample", "governance", "current")

    def codes(self, result=None):
        result = result or self.validate()
        return {d["code"] for d in result["graph"]["diagnostics"] if d["severity"] == "error"}

    def test_valid_current_graph_remains_unreleased_and_read_only(self):
        before = tree_state(self.repo)
        result = self.validate()
        self.assertTrue(result["graph_valid"], result["graph_errors"])
        self.assertTrue(result["artifact_valid"], result["errors"])
        self.assertFalse(result["valid"])
        self.assertFalse(result["policy_enforcement_ready"])
        self.assertEqual(result["errors"], result["policy_errors"])
        self.assertEqual(result, self.validate())
        self.assertEqual(before, tree_state(self.repo))

    def test_citation_in_prose_is_not_a_ratified_decision(self):
        (self.repo / "DECISIONS.md").write_text("Consider D-001 later; it has not been accepted.\n")
        self.assertIn("undefined-reference", self.codes())
        (self.repo / "DECISIONS.md").write_text("| D-001 | proposed | baseline |\n")
        self.assertIn("unratified-decision", self.codes())

    def test_duplicate_need_definitions_are_not_collapsed(self):
        self.fixture.write_chain(concept=fx.con().replace("## Non-goals", "### UN-001 — Duplicate need\n- **Context:** different\n## Non-goals"))
        self.assertIn("duplicate-definition", self.codes())

    def test_empty_fields_and_duplicate_labels_fail(self):
        self.fixture.write_chain(functional=fx.fsd().replace("- **Done when:** value", "- **Done when:**\n- **Purpose:** replacement"),
                                 technical=fx.tsd().replace("- **Verification:** value", "- **Verification:** none"))
        self.assertTrue({"empty-obligation", "duplicate-label"} <= self.codes())

    def test_edges_must_match_in_both_directions(self):
        functional = fx.fsd(items=fx.f_item() + fx.f_item("F-002"), inventory_ids=["F-001", "F-002"])
        self.fixture.write_chain(functional=functional, technical=fx.tsd(realizes="F-001, F-002", trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-002 | UN-001, C-001 | | tests |"))
        self.assertIn("realization-edge-mismatch", self.codes())
        self.fixture.write_chain(functional=functional, technical=fx.tsd(trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-002 | UN-001, C-001 | T-001 | tests |"))
        self.assertIn("realization-edge-mismatch", self.codes())

    def test_trace_serves_cannot_rewrite_authoritative_need_links(self):
        self.fixture.write_chain(technical=fx.tsd(trace="| F-001 | UN-001 | T-001 | tests |"))
        self.assertIn("serves-edge-mismatch", self.codes())

    def test_nfr_realization_and_backward_trace_are_first_class(self):
        nfr = "## Non-functional outcomes\n| ID | Outcome | Serves | Measure | Verification |\n|---|---|---|---|---|\n| F-NFR-001 | Access is controlled | UN-001 | Every denied request returns a denial | Authorization test |\n"
        self.fixture.write_chain(functional=fx.fsd(extra=nfr), technical=fx.tsd(realizes="F-001, F-NFR-001, D-001", trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-NFR-001 | UN-001 | T-001 | authorization test |"))
        self.assertTrue(self.validate()["graph_valid"], self.validate()["graph_errors"])
        trace = tc.trace_all(tc.load_chain(self.repo, "sample", "current"))
        self.assertIn("F-NFR-001", trace["traced"])
        self.assertFalse(trace["breaks"], trace["breaks"])
        self.assertTrue(any("UR-001" in line for line in trace["traced"]["F-NFR-001"]))

    def test_examples_do_not_define_requirements_or_ratifications(self):
        example = "\n```markdown\n### F-999 — example only\n- **Serves:** UN-999\n```\n"
        self.fixture.write_chain(functional=fx.fsd(extra=example))
        self.assertTrue(self.validate()["graph_valid"], self.validate()["graph_errors"])
        (self.repo / "DECISIONS.md").write_text("```markdown\n| D-001 | accepted | example |\n```\n")
        self.assertIn("undefined-reference", self.codes())

    def test_legacy_behavior_is_unchanged_for_empty_acceptance(self):
        self.fixture.write_chain(functional=fx.fsd().replace("- **Done when:** value", "- **Done when:**"))
        self.assertTrue(vs.validate_repository(self.repo, "sample", "governance")["valid"])
        self.assertIn("empty-obligation", self.codes())

    def test_optional_fsd_trace_table_still_requires_complete_coverage(self):
        self.fixture.write_chain(functional=fx.fsd(trace=""))
        self.assertIn("missing-fsd-trace-row", self.codes())

    def test_nfr_only_technical_item_is_valid_and_placeholder_nfr_is_not(self):
        nfr = "## Non-functional outcomes\n| ID | Outcome | Serves | Measure | Verification |\n|---|---|---|---|---|\n| F-NFR-001 | Safe access | UN-001 | No unauthorized access | Denial tests |\n"
        technical = fx.tsd(trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-NFR-001 | UN-001 | T-002 | denial tests |")
        second = fx.tsd(realizes="F-NFR-001").split("### T-001", 1)[1].split("## Product deltas", 1)[0]
        technical = technical.replace("## Product deltas", "### T-002" + second + "## Product deltas", 1)
        self.fixture.write_chain(functional=fx.fsd(extra=nfr), technical=technical)
        self.assertTrue(self.validate()["artifact_valid"], self.validate()["errors"])
        self.fixture.write_chain(functional=fx.fsd(extra=nfr.replace("No unauthorized access", "—")), technical=technical)
        self.assertIn("empty-obligation", self.codes())

    def test_scoped_definition_location_and_multiline_acceptance(self):
        self.fixture.write_chain(functional=fx.fsd().replace("- **Done when:** value", "- **Done when:**\n  A hirer shortlists suitable supply without exposing exact coordinates."))
        self.assertTrue(self.validate()["artifact_valid"], self.validate()["errors"])
        self.fixture.write_chain(functional=fx.fsd().replace("- **Done when:** value", "- **Done when:**"))
        result = self.validate()
        finding = next(d for d in result["graph"]["diagnostics"] if d["code"] == "empty-obligation")
        source = Path(finding["path"]).read_text().splitlines()
        self.assertTrue(source[finding["line"] - 1].startswith("### F-001"))

    def test_standalone_trace_uses_the_same_decision_authority(self):
        decisions = self.repo / "DECISIONS.md"
        decisions.rename(self.repo / "docs" / "sample-DECISIONS.md")
        result = vs.validate_repository(self.repo, "sample", "standalone", "current")
        self.assertTrue(result["artifact_valid"], result["errors"])
        trace = tc.trace_all(tc.load_chain(self.repo, "sample", "current", "standalone"))
        self.assertFalse(trace["breaks"])

    def test_cli_reports_graph_findings_not_just_policy_refusal(self):
        self.fixture.write_chain(functional=fx.fsd().replace("- **Done when:** value", "- **Done when:**"))
        command = [sys.executable, "-B", str(regressions.ROOT / "spec-chain/scripts/validate_spec.py"),
                   "--repo", str(self.repo), "--project", "sample", "--mode", "governance", "--policy", "current", "--json"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertIn("empty-obligation", self.codes(json.loads(result.stdout)))
        self.fixture.write_chain(concept=fx.con(response_evidence="hypothesis"))
        command[2] = str(regressions.ROOT / "spec-chain/scripts/trace_chain.py")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 3)
        self.assertTrue(report["artifact_valid"], report["breaks"])
        self.assertTrue(report["graph_valid"], report["graph_errors"])
        self.assertTrue(any("weak-evidence" in warning for warning in report["graph_warnings"]))
        result = subprocess.run(command[:-1], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any(line.startswith("warning: ") and "[weak-evidence]" in line
                            for line in result.stdout.splitlines()))


class PlanningGraphTests(unittest.TestCase):
    def setUp(self):
        self.fixture = pt.PlanValidatorTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.fixture.write_repo()
        self.repo = self.fixture.repo

    def validate(self, mode="governance"):
        args = ["--policy", "current"]
        if mode == "standalone":
            args += ["--plan-name", "sample"]
        return json.loads(self.fixture.validate(mode, *args).stdout)

    def codes(self, result=None):
        result = result or self.validate()
        return {d["code"] for d in result["graph"]["diagnostics"] if d["severity"] == "error"}

    def test_valid_current_plan_is_a_read_only_unreleased_preview(self):
        before = tree_state(self.repo)
        result = self.validate()
        self.assertTrue(result["graph_valid"], result["graph_errors"])
        self.assertEqual(result["errors"], result["policy_errors"])
        self.assertFalse(result["policy_enforcement_ready"])
        self.assertEqual(before, tree_state(self.repo))

    def test_cycles_and_forward_dependencies_are_explicit(self):
        slices = pt.slice_block().replace("**Depends on:** none", "**Depends on:** W1-S2")
        slices += pt.slice_block("W1-S2").replace("**Depends on:** none", "**Depends on:** W1-S1")
        self.fixture.write_repo(wave_brief=pt.brief(slices=slices))
        self.assertIn("dependency-cycle", self.codes())

    def test_duplicate_and_foreign_slice_ids_fail(self):
        self.fixture.write_repo(wave_brief=pt.brief(slices=pt.slice_block() + pt.slice_block() + pt.slice_block("W2-S1")))
        self.assertTrue({"duplicate-slice", "slice-wave-mismatch"} <= self.codes())

    def test_index_membership_and_rationale_are_checked(self):
        self.fixture.write_repo(index=pt.wave_index().replace("| W1 |", "| W2 |"), wave_brief=pt.brief().replace("## Why this wave\n\nSign-in gates every later outcome, so it retires the most important uncertainty first.\n\n", ""))
        self.assertTrue({"wave-index-mismatch", "missing-wave-rationale"} <= self.codes())

    def test_done_without_recorded_approval_is_not_a_completed_wave(self):
        self.fixture.write_repo(index=pt.wave_index().replace("| ⏸ |", "| ✅ |"))
        self.assertIn("missing-approval-reference", self.codes())

    def test_mentions_do_not_define_specification_requirements(self):
        self.fixture.write_repo(functional="# Notes\nMaybe F-001 and UN-001 someday.\n")
        self.assertIn("undefined-reference", self.codes())

    def test_empty_standalone_plan_has_specific_graph_error(self):
        self.fixture.write_standalone(waves=pt.LEGEND + "\n")
        self.assertIn("missing-waves", self.codes(self.validate("standalone")))

    def test_legal_dependencies_across_waves_and_completed_approval_references(self):
        approvals = self.fixture.waves / "approvals"
        approvals.mkdir()
        (approvals / "w1-start.md").write_text("Owner-approved start of W1, recorded in the review fixture.")
        (approvals / "w1-close.md").write_text("Owner sign-off for W1, recorded in the review fixture.")
        index = pt.wave_index().replace("| Status |", "| Status | Start approval | Sign-off evidence |")
        index = index.replace("|---|---|---|---|", "|---|---|---|---|---|---|")
        index = index.replace("| ⏸ |", "| ✅ | approvals/w1-start.md | approvals/w1-close.md |")
        index += "| W2 | Next outcome | wave-2-next.md | ⏸ | — | — |\n"
        self.fixture.write_repo(index=index)
        next_brief = pt.brief(slices=pt.slice_block("W2-S1").replace("**Depends on:** none", "**Depends on:** W1-S1")).replace("# Wave 1", "# Wave 2")
        (self.fixture.waves / "wave-2-next.md").write_text(next_brief)
        result = self.validate()
        self.assertTrue(result["artifact_valid"], result["errors"])
        (approvals / "w1-close.md").unlink()
        self.assertIn("missing-approval-reference", self.codes())

    def test_nonfunctional_slice_and_infrastructure_warning_do_not_force_restructuring(self):
        functional = pt.fsd() + "\n## Non-functional outcomes\n| ID | Outcome | Serves | Measure | Verification |\n|---|---|---|---|---|\n| F-NFR-001 | Safe access | UN-001 | All denied | Tests |\n"
        self.fixture.write_repo(functional=functional, wave_brief=pt.brief(slices=pt.slice_block(kind="infrastructure", serves="UN-001", unlocks="F-NFR-001")))
        result = self.validate()
        self.assertTrue(result["artifact_valid"], result["errors"])
        self.assertTrue(result["graph_warnings"])

    def test_unknown_self_and_blank_dependencies_fail_separately(self):
        for target, code in (("W9-S1", "undefined-dependency"), ("W1-S1", "dependency-cycle"), ("", "invalid-dependency")):
            with self.subTest(target=target):
                self.fixture.write_repo(wave_brief=pt.brief(slices=pt.slice_block().replace("**Depends on:** none", "**Depends on:** " + target)))
                self.assertIn(code, self.codes())

    def test_complete_standalone_plan_without_specs_is_honest_about_reference_limits(self):
        for path in self.fixture.docs.glob("*-FSD.md"):
            path.unlink()
        for path in self.fixture.docs.glob("*-TSD.md"):
            path.unlink()
        index = "## Status\n" + pt.LEGEND + "\n| Wave | Capability | Status |\n|---|---|---|\n| W1 | Authentication | ⏸ |\n"
        self.fixture.write_standalone(waves=index + pt.brief())
        result = self.validate("standalone")
        self.assertTrue(result["artifact_valid"], result["errors"])
        self.assertIn("unvalidated-specification-references", {d["code"] for d in result["graph"]["diagnostics"]})

    def test_legacy_empty_standalone_remains_legacy(self):
        self.fixture.write_standalone(waves=pt.LEGEND + "\n")
        legacy = self.fixture.validate("standalone", "--plan-name", "sample")
        self.assertEqual(legacy.returncode, 0)
        self.assertIn("missing-waves", self.codes(self.validate("standalone")))

    def test_existing_bold_exit_convention_remains_supported(self):
        self.fixture.write_repo(wave_brief=pt.brief().replace("## Exit criterion", "**Exit criterion:**"))
        result = self.validate()
        self.assertTrue(result["artifact_valid"], result["errors"])


if __name__ == "__main__":
    unittest.main()
