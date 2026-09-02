#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import baseline, con, f_item, fsd, tsd  # noqa: E402

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
VALIDATOR = SCRIPTS / "validate_spec.py"
TRACER = SCRIPTS / "trace_chain.py"


class SpecValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="spec-chain-validator-")
        self.repo = Path(self.temp.name)
        (self.repo / "docs").mkdir()
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted |\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_chain(
        self,
        *,
        concept: str | None = con(),
        functional: str | None = None,
        technical: str | None = None,
    ) -> None:
        if concept is not None:
            (self.repo / "docs" / "sample-CON.md").write_text(concept, encoding="utf-8")
        (self.repo / "docs" / "sample-FSD.md").write_text(
            functional if functional is not None else fsd(), encoding="utf-8"
        )
        (self.repo / "docs" / "sample-TSD.md").write_text(
            technical if technical is not None else tsd(), encoding="utf-8"
        )

    def run_script(self, script: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), "--repo", str(self.repo), "--project", "sample", *extra, "--json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def validate(self) -> subprocess.CompletedProcess[str]:
        return self.run_script(VALIDATOR, "--mode", "governance")

    def errors(self, result: subprocess.CompletedProcess[str]) -> list[str]:
        return json.loads(result.stdout)["errors"]

    # --- baseline ---------------------------------------------------------------

    def test_valid_chain_passes(self) -> None:
        self.write_chain()
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["functional_ids"], ["F-001"])
        self.assertEqual(payload["technical_ids"], ["T-001"])
        self.assertEqual(payload["need_ids"], ["UN-001"])
        self.assertEqual(payload["accepted_response_ids"], ["C-001"])
        self.assertEqual(payload["warnings"], [])

    def test_missing_fixed_label_fails(self) -> None:
        labels = [
            "Kind", "Purpose", "Serves", "Actors and permission", "Context/trigger", "Inputs/content",
            "Actions and outcomes", "States", "Rules", "Dependencies", "Done when",
        ]
        self.write_chain(functional=fsd(items=f_item(labels=labels)))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("Errors and recovery" in error for error in self.errors(result)))

    def test_traceability_orphan_fails(self) -> None:
        self.write_chain(technical=tsd(trace="| F-001 | UN-001 | T-999 | tests |"))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        errors = self.errors(result)
        self.assertTrue(any("T-001" in error for error in errors))
        self.assertTrue(any("T-999" in error for error in errors))

    def test_fsd_traceability_table_is_optional(self) -> None:
        # fsd.md section 14: the table is optional, so its absence is not an error.
        self.write_chain(functional=fsd(trace=None))
        self.assertEqual(self.validate().returncode, 0)

    def test_present_fsd_traceability_table_must_cover_every_item(self) -> None:
        two_items = f_item() + f_item("F-002", "Record and confirm", kind="journey", representation=True)
        self.write_chain(
            functional=fsd(
                items=two_items,
                inventory_ids=["F-001", "F-002"],
                trace="| F-001 | UN-001, C-001 | D-001 |",
            ),
            technical=tsd(
                trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-002 | UN-001 | T-001 | tests |"
            ),
        )
        errors = self.errors(self.validate())
        self.assertIn("sample-FSD.md: F-IDs missing traceability: F-002", errors)

        # Both rows present: the same chain validates.
        self.write_chain(
            functional=fsd(
                items=two_items,
                inventory_ids=["F-001", "F-002"],
                trace="| F-001 | UN-001, C-001 | D-001 |\n| F-002 | UN-001, C-001 | D-001 |",
            ),
            technical=tsd(
                trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-002 | UN-001 | T-001 | tests |"
            ),
        )
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_empty_fsd_traceability_table_orphans_every_item(self) -> None:
        self.write_chain(functional=fsd(trace=""))
        errors = self.errors(self.validate())
        self.assertIn("sample-FSD.md: F-IDs missing traceability: F-001", errors)

    def test_fsd_traceability_rejects_unspecified_functional_ids(self) -> None:
        self.write_chain(functional=fsd(trace="| F-001 | UN-001, C-001 | D-001 |\n| F-909 | UN-001 | D-001 |"))
        errors = self.errors(self.validate())
        self.assertIn("sample-FSD.md: traceability cites unknown F-IDs: F-909", errors)

    def test_fsd_traceability_ignores_the_non_functional_namespace(self) -> None:
        # F-NFR IDs keep their own namespace and are traced in the TSD, not here.
        self.write_chain(
            functional=fsd(
                trace="| F-001 | UN-001, C-001 | D-001 |",
                extra="## Non-functional outcomes\n| ID | Outcome | Serves |\n|---|---|---|\n"
                "| F-NFR-001 | responsive | UN-001 |\n",
            ),
            technical=tsd(
                trace="| F-001 | UN-001, C-001 | T-001 | tests |\n| F-NFR-001 | UN-001 | T-001 | measure |"
            ),
        )
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_fsd_how_heading_fails(self) -> None:
        self.write_chain(functional=fsd(extra="\n## Architecture\nForbidden detail.\n"))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("forbidden in FSD" in error for error in self.errors(result)))

    def test_unknown_decision_reference_fails(self) -> None:
        self.write_chain(technical=tsd(realizes="F-001, D-999"))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("D-999" in error for error in self.errors(result)))

    def test_blocking_open_item_fails(self) -> None:
        functional = fsd().replace("No blocking O-IDs remain.", "O-001 remains blocking.")
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted |\n| O-001 | open |\n", encoding="utf-8")
        self.write_chain(functional=functional)
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("blocking O-ID" in error for error in self.errors(result)))

    def test_unfilled_template_placeholders_fail(self) -> None:
        template = (VALIDATOR.parents[1] / "assets" / "FSD.md").read_text(encoding="utf-8")
        (self.repo / "DECISIONS.md").write_text("| D-001 | accepted |\n| O-001 | open |\n", encoding="utf-8")
        self.write_chain(functional=template)
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        placeholder_errors = [error for error in self.errors(result) if "unresolved template placeholders" in error]
        self.assertTrue(any(error.startswith("sample-FSD.md") for error in placeholder_errors), placeholder_errors)

    def test_numbered_headings_and_hyphen_separator_pass(self) -> None:
        functional = fsd().replace("### F-001 — Understand", "### F-001 - Understand")
        functional = functional.replace("## Functional inventory", "## 5. Functional inventory")
        functional = functional.replace("## Blocking open decisions", "## 11. Blocking open decisions")
        technical = tsd().replace("### T-001 — Proximity", "### T-001 – Proximity")
        technical = technical.replace("## Traceability", "## 15. Traceability")
        self.write_chain(functional=functional, technical=technical)
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_nfr_ids_require_traceability(self) -> None:
        functional = fsd(extra="\n## Non-functional outcomes\n| ID | Outcome |\n|---|---|\n| F-NFR-001 | fast |\n")
        self.write_chain(functional=functional)
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("F-NFR-001" in error for error in self.errors(result)))
        self.write_chain(
            functional=functional,
            technical=tsd(trace="| F-001 | UN-001 | T-001 | tests |\n| F-NFR-001 | UN-001 | T-001 | load test |"),
        )
        self.assertEqual(self.validate().returncode, 0)

    # --- need-first structural rules ------------------------------------------------

    def test_f_without_serves_fails(self) -> None:
        labels = [
            "Kind", "Purpose", "Actors and permission", "Context/trigger", "Inputs/content",
            "Actions and outcomes", "States", "Rules", "Errors and recovery", "Dependencies", "Done when",
        ]
        self.write_chain(functional=fsd(items=f_item(labels=labels)))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("missing label 'Serves'" in error for error in self.errors(result)))

    def test_f_serving_hypothesis_response_fails(self) -> None:
        self.write_chain(concept=con(response_status="hypothesis"))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        errors = self.errors(result)
        self.assertTrue(any("not accepted" in error and "C-001 (hypothesis)" in error for error in errors), errors)

    def test_f_serving_unknown_need_fails(self) -> None:
        self.write_chain(functional=fsd(items=f_item(serves="UN-042")))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("unknown needs: UN-042" in error for error in self.errors(result)))

    def test_accepted_response_without_f_fails(self) -> None:
        self.write_chain(functional=fsd(items=f_item(serves="UN-001")))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("accepted responses not served" in error for error in self.errors(result)))
        self.write_chain(concept=con(response_status="deferred"), functional=fsd(items=f_item(serves="UN-001")))
        self.assertEqual(self.validate().returncode, 0)

    def test_screen_requires_representation_rationale_but_endpoint_does_not(self) -> None:
        self.write_chain(functional=fsd(items=f_item(kind="page")))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        errors = self.errors(result)
        self.assertTrue(any("needs 'Representation rationale'" in error for error in errors), errors)
        self.write_chain(functional=fsd(items=f_item(kind="page", representation=True)))
        self.assertEqual(self.validate().returncode, 0)
        self.write_chain(functional=fsd(items=f_item(kind="endpoint")))
        self.assertEqual(self.validate().returncode, 0)

    def test_skipped_con_requires_named_baseline(self) -> None:
        self.write_chain(concept=None, functional=fsd(items=f_item(serves="UN-001")))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("no upstream" in error for error in self.errors(result)))
        self.write_chain(
            concept=None,
            functional=fsd(items=f_item(serves="UN-001"), baseline=baseline(authority="")),
        )
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("Baseline authority" in error for error in self.errors(result)))
        self.write_chain(concept=None, functional=fsd(items=f_item(serves="UN-001"), baseline=baseline()))
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["needs_source"], "fsd-baseline")

    def test_baseline_alongside_con_is_duplicate_authority(self) -> None:
        self.write_chain(functional=fsd(baseline=baseline()))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("duplicate need authority" in error for error in self.errors(result)))

    def test_con_need_without_response_or_deferral_fails(self) -> None:
        extra = """### UN-002 — Compare prices
- **Roles:** UR-001
- **Context:** shortlisting
- **Underlying job:** compare total cost
- **Decision or action:** pick a supplier
- **Desired outcome:** best value
- **Evidence class:** hypothesis
"""
        self.write_chain(concept=con(extra_needs=extra))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("UN-002" in error and "without a product response" in error for error in self.errors(result)))
        self.write_chain(concept=con(extra_needs=extra, deferred="| UN-002 | pricing data unavailable | keep price fields nullable |"))
        self.assertEqual(self.validate().returncode, 0)

    def test_invalid_evidence_class_and_status_fail(self) -> None:
        self.write_chain(concept=con(response_evidence="gut-feeling"))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("evidence class 'gut-feeling'" in error for error in self.errors(result)))
        self.write_chain(concept=con(response_status="approved"))
        result = self.validate()
        self.assertTrue(any("status 'approved'" in error for error in self.errors(result)))
        self.write_chain(concept=con(kind="feature"))
        result = self.validate()
        self.assertTrue(any("kind 'feature'" in error for error in self.errors(result)))

    def test_accepted_response_on_assumption_warns_but_passes(self) -> None:
        self.write_chain(concept=con(response_evidence="assumption"))
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        warnings = json.loads(result.stdout)["warnings"]
        self.assertTrue(any("C-001" in item and "assumption" in item for item in warnings), warnings)

    def test_tsd_requires_product_deltas_and_known_realizes(self) -> None:
        self.write_chain(technical=tsd(deltas=""))
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("Product deltas surfaced" in error for error in self.errors(result)))
        self.write_chain(technical=tsd(realizes="F-777"))
        result = self.validate()
        self.assertTrue(any("realizes unknown F-IDs: F-777" in error for error in self.errors(result)))
        self.write_chain(technical=tsd(realizes="none"))
        result = self.validate()
        self.assertTrue(any("technology cannot create a requirement" in error for error in self.errors(result)))

    def test_con_missing_sections_fail(self) -> None:
        concept = con().replace("## Non-goals", "## Things we skip")
        self.write_chain(concept=concept)
        result = self.validate()
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("missing section 'Non-goals'" in error for error in self.errors(result)))

    # --- trace_chain ------------------------------------------------------------

    def test_trace_chain_walks_to_user_and_breaks_on_gap(self) -> None:
        self.write_chain()
        result = self.run_script(TRACER)
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        joined = "\n".join(payload["traced"]["T-001"])
        for token in ("T-001", "F-001", "C-001", "UN-001", "UR-001"):
            self.assertIn(token, joined)
        single = json.loads(self.run_script(TRACER, "--id", "F-001").stdout)
        self.assertTrue(single["valid"])

        self.write_chain(concept=con(response_status="hypothesis"))
        result = self.run_script(TRACER)
        self.assertEqual(result.returncode, 3)
        breaks = json.loads(result.stdout)["breaks"]
        self.assertTrue(any("C-001 has status 'hypothesis'" in item for item in breaks), breaks)

        self.write_chain(technical=tsd(realizes="none"))
        result = self.run_script(TRACER, "--id", "T-001")
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("realizes no F-ID" in item for item in json.loads(result.stdout)["breaks"]))


if __name__ == "__main__":
    unittest.main()
