"""The 12 reproduced gaps at 2f223ce; expected failures are NOT passing checks.

Remove each expectedFailure when its owning wave implements the invariant. Fixture
setup runs outside the expected-failure body so setup failures remain hard errors.
No destructive command below is executed: hook probes classify strings only.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def module(name: str, relative: str):
    loader = importlib.machinery.SourceFileLoader(name, str(ROOT / relative))
    spec = importlib.util.spec_from_loader(name, loader)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    loader.exec_module(result)
    return result


fx = module("review_fixtures", "spec-chain/tests/fixtures.py")
vs = module("review_spec", "spec-chain/scripts/validate_spec.py")
tc = module("review_trace", "spec-chain/scripts/trace_chain.py")
rt = module("review_runtime_fixtures", "governance-system/tests/test_runtime.py")
pt = module("review_plan_fixtures", "plan-waves-slices/tests/test_validate_plan.py")
gc = module("review_runtime", "governance-system/scripts/governancectl")
ha = module("review_claude_hook", "governance-system/hooks/claude-code/governance-hook.py")


class SpecificationRegressions(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="review-regression-spec-")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.docs = self.repo / "docs"
        self.docs.mkdir()
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted | baseline |\n")
        self.write_chain()
        self.assertTrue(self.validate()["valid"])

    def write_chain(self, *, concept=None, functional=None, technical=None):
        for kind, text in (("CON", concept or fx.con()), ("FSD", functional or fx.fsd()),
                           ("TSD", technical or fx.tsd())):
            (self.docs / f"sample-{kind}.md").write_text(text, encoding="utf-8")

    def validate(self, requested_policy="auto"):
        return vs.validate_repository(self.repo, "sample", "governance", requested_policy)

    def assert_graph_error(self, code):
        result = self.validate("current")
        self.assertFalse(result["graph_valid"])
        self.assertIn(code, {finding["code"] for finding in result["graph"]["diagnostics"]})

    def test_gap_01_accepted_response_requires_ratification_reference(self):
        """Wave 3: an empty label is not a ratification reference."""
        self.write_chain(concept=fx.con().replace("- **Decision references:** D-001", "- **Decision references:**"))
        self.assert_graph_error("missing-ratification")

    def test_gap_02_functional_acceptance_cannot_be_empty(self):
        """Wave 3: acceptance must contain an obligation."""
        self.write_chain(functional=fx.fsd().replace("- **Done when:** value", "- **Done when:**"))
        self.assert_graph_error("empty-obligation")

    def test_gap_03_realization_edges_must_agree(self):
        """Wave 3: membership in tables is not edge consistency."""
        self.write_chain(
            functional=fx.fsd(items=fx.f_item() + fx.f_item("F-002", "Second behavior"), inventory_ids=["F-001", "F-002"]),
            technical=fx.tsd(trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-002 | UN-001, C-001 | T-001 | tests |"),
        )
        self.assert_graph_error("realization-edge-mismatch")

    def test_gap_04_nfr_requires_realization_and_verification(self):
        """Wave 3: NFRs participate in validation and explainability."""
        self.write_chain(
            functional=fx.fsd(extra="## Non-functional outcomes\n| ID | Outcome | Serves | Measure | Verification |\n|---|---|---|---|---|\n| F-NFR-001 | access control | UN-001 | | |\n"),
            technical=fx.tsd(trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-NFR-001 | UN-001 | | |"),
        )
        trace = tc.trace_all(tc.load_chain(self.repo, "sample", "current"))
        self.assert_graph_error("unrealized-requirement")
        self.assertIn("F-NFR-001", trace["traced"])

    def test_gap_05_accepted_hypothesis_remains_weak_evidence(self):
        """Wave 3: ratification does not establish an empirical fact."""
        self.write_chain(concept=fx.con(response_evidence="hypothesis"))
        self.assertTrue(self.validate("current")["graph_warnings"])


class RuntimeRegressions(unittest.TestCase):
    def setUp(self):
        self.fixture = rt.GovernanceRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.repo = self.fixture.repo
        rt.ctl(self.repo, "discover")

    def test_gap_06_phase_change_does_not_establish_completion(self):
        """Wave 4: handoff phase is not an acceptance contract."""
        rt.ctl(self.repo, "phase", "handoff")
        result = rt.ctl(self.repo, "check-stage", "--policy", "current", check=False)
        report = json.loads(result.stdout)
        self.assertFalse(report["stage_valid"])
        self.assertIn("stage-contract-required", {d["code"] for d in report["stage"]["diagnostics"]})

    def test_gap_07_blocking_finding_and_missing_tests_prevent_closure(self):
        """Wave 4: a flag does not satisfy open obligations."""
        rt.write_governance_docs(self.repo)
        rt.ctl(self.repo, "note", "--kind", "blocking", "--text", "Acceptance is not agreed")
        result = rt.ctl(self.repo, "check-stage", "--policy", "current", check=False)
        report = json.loads(result.stdout)
        self.assertFalse(report["stage_valid"])
        self.assertIn("stage-blocking-note", {d["code"] for d in report["stage"]["diagnostics"]})

    def test_gap_08_changed_content_needs_new_disposition_and_snapshot(self):
        """Wave 2: reviewed content is immutable and version-bound."""
        sibling = self.fixture.add_sibling()
        (sibling / "app.txt").write_text("variant one\n")
        rt.ctl(self.repo, "reconcile", check=False)
        original = next(r for r in self.fixture.resolutions() if r["kind"] == "unfinished-variant")
        snapshot = self.fixture.common_state() / "snapshots" / (original["snapshots"][0] + ".patch")
        before = snapshot.read_bytes()
        rt.ctl(self.repo, "resolve", "--id", original["id"], "--choice", "defer", "--note", "Reviewed first version")
        (sibling / "app.txt").write_text("different unreviewed variant two\n")
        rt.ctl(self.repo, "reconcile", check=False)
        needs_review = [r for r in self.fixture.resolutions() if r["status"] in {"needs-owner", "pending"}]
        self.assertEqual((snapshot.read_bytes() == before, bool(needs_review)), (True, True))


class PlanningRegressions(unittest.TestCase):
    def setUp(self):
        case_type = next(value for value in vars(pt).values()
                         if isinstance(value, type) and hasattr(value, "write_repo"))
        self.fixture = case_type()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.fixture.write_repo()
        self.assertEqual(self.fixture.validate().returncode, 0)

    def test_gap_09_cycle_missing_rationale_and_unapproved_completion(self):
        """Wave 3: validate dependencies, rationale and actual approval."""
        slices = (pt.slice_block().replace("**Depends on:** none", "**Depends on:** W1-S2")
                  + pt.slice_block("W1-S2").replace("**Depends on:** none", "**Depends on:** W1-S1"))
        self.fixture.write_repo(
            index=pt.wave_index().replace("| ⏸ |", "| ✅ |"),
            wave_brief=pt.brief(slices=slices).replace(
                "## Why this wave\n\nSign-in gates every later outcome, so it retires the most important uncertainty first.\n\n", ""),
        )
        result = self.fixture.validate("governance", "--policy", "current")
        self.assertEqual(result.returncode, 3)
        codes = {finding["code"] for finding in json.loads(result.stdout)["graph"]["diagnostics"]}
        self.assertTrue({"dependency-cycle", "missing-wave-rationale", "missing-approval-reference"} <= codes)

    def test_gap_10_standalone_plan_needs_actual_waves(self):
        """Wave 3: a status legend alone is not a plan."""
        self.fixture.write_standalone(waves=pt.LEGEND + "\n")
        result = self.fixture.validate("standalone", "--plan-name", "sample", "--policy", "current")
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("missing-waves", {finding["code"] for finding in json.loads(result.stdout)["graph"]["diagnostics"]})


class HookRegressions(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="review-regression-hook-")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        (self.repo / ".governance").mkdir()
        (self.repo / ".governance" / "config.json").write_text(json.dumps({"enabled": True, "hooks_enabled": True}))

    @unittest.expectedFailure
    def test_gap_11_git_global_options_do_not_bypass_review(self):
        """Wave 6: classify strings only; never execute destructive probes."""
        with patch.object(gc, "load_config", return_value={"enabled": True, "hooks_enabled": True}):
            permissions = [gc.neutral_hook_decision(self.repo, "pre-tool-use", {"command": spelling})["permission"]
                           for spelling in ("git reset --hard", "git -C /tmp/example reset --hard")]
        self.assertTrue(all(permission in {"ask", "deny"} for permission in permissions), permissions)

    @unittest.expectedFailure
    def test_gap_12_enabled_pre_action_guard_fails_closed(self):
        """Wave 6: missing runtime cannot authorize a guarded command."""
        with patch.object(ha, "repository_root", return_value=self.repo), patch.object(ha, "runtime_path", return_value=None), patch.object(ha, "EVENT", "pre-tool-use"):
            result = ha.neutral_decision(b'{"tool_input":{"command":"git reset --hard"}}')
        self.assertEqual(result["permission"], "deny")


if __name__ == "__main__":
    unittest.main()
