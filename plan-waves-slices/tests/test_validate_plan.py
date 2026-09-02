#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_plan.py"
LEGEND = "⏸ gated · 🟡 approved & in progress · ✅ done & signed off"

SLICE_LABELS = [
    "Outcome",
    "Serves",
    "Why",
    "Usable when done",
    "Depends on",
    "Tests",
    "Acceptance evidence",
]

SLICE_VALUES = {
    "Outcome": "an owner signs in and reaches the account dashboard",
    "Why": "no other wave outcome is demonstrable without a session",
    "Usable when done": "an owner can sign in and stay signed in across requests",
    "Depends on": "none",
    "Tests": "unit tests for the token store, one sign-in flow test",
    "Acceptance evidence": "recorded sign-in transcript attached to the wave",
}


def slice_block(
    slice_id: str = "W1-S1",
    name: str = "Authenticate through the documented interface",
    *,
    kind: str | None = None,
    serves: str = "F-001, UN-001",
    unlocks: str | None = None,
    drop: tuple[str, ...] = (),
    separator: str = "—",
) -> str:
    """One slice subsection. `drop` omits labels; `unlocks` adds the infrastructure label."""
    pairs: list[tuple[str, str]] = []
    if kind is not None:
        pairs.append(("Kind", kind))
    pairs.append(("Outcome", SLICE_VALUES["Outcome"]))
    if unlocks is not None:
        pairs.append(("Unlocks", unlocks))
    pairs.append(("Serves", serves))
    for label in ["Why", "Usable when done", "Depends on", "Tests", "Acceptance evidence"]:
        pairs.append((label, SLICE_VALUES[label]))
    lines = [f"- **{label}:** {value}" for label, value in pairs if label not in drop]
    return f"### {slice_id} {separator} {name}\n\n" + "\n".join(lines) + "\n"


def brief(
    *,
    slices: str | None = None,
    decisions: str = "D-001",
    needs: str = "UN-001",
    functional: str = "F-001",
    technical: str = "T-001",
    exits: int = 1,
    extra: str = "",
) -> str:
    """A wave brief mirroring assets/wave-brief.md, with every placeholder resolved."""
    slices = slice_block() if slices is None else slices
    exit_sections = "".join(
        "## Exit criterion\n\n> An owner authenticates through the documented interface.\n\n"
        for _ in range(exits)
    )
    return f"""# Wave 1 — Authentication

## Objective

An owner authenticates through the documented interface.

## Why this wave

Sign-in gates every later outcome, so it retires the most important uncertainty first.

## References

- Decisions: {decisions}
- User needs: {needs}
- Behaviour: {functional}
- Technical design: {technical}

{exit_sections}## Slices

{slices}{extra}
## Sign-off checklist

- [ ] Every slice satisfies the project Definition of Done.
- [ ] Owner sign-off is recorded in the wave index.
"""


def wave_index() -> str:
    return (
        "# Sample Wave Index\n\n## Status\n\n"
        f"Legend: {LEGEND}\n\n"
        "| Wave | Capability | Brief | Status |\n|---|---|---|---|\n"
        "| W1 | Authentication | wave-1-auth.md | ⏸ |\n"
    )


def fsd(*, functional_ids: tuple[str, ...] = ("F-001",), needs: tuple[str, ...] = ("UN-001",)) -> str:
    baseline = (
        "## User needs baseline\n\n- **Baseline authority:** D-001\n\n"
        + "".join(f"### {need} — Reach account work without re-proving identity\n" for need in needs)
        if needs
        else ""
    )
    serves = ", ".join(needs) if needs else "C-001"
    items = "".join(f"### {fid} — Authenticate an owner\n- **Serves:** {serves}\n" for fid in functional_ids)
    return f"# Sample Functional Specification\n\n{baseline}\n## Functional specifications\n\n{items}"


def con(*, needs: tuple[str, ...] = ("UN-001",)) -> str:
    items = "".join(f"### {need} — Reach account work without re-proving identity\n" for need in needs)
    return f"# Sample Concept Document\n\n## User needs\n\n{items}"


def tsd(*, technical_ids: tuple[str, ...] = ("T-001",)) -> str:
    items = "".join(f"### {tid} — Session service\n- **Realizes:** F-001\n" for tid in technical_ids)
    return f"# Sample Technical Design\n\n## Technical requirements\n\n{items}"


TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "wave-brief.md"

# Placeholders whose resolution must satisfy an ID rule; everything else in the
# template resolves to prose the validator does not inspect.
TEMPLATE_IDS = {
    "<N>": "1",
    "<D-IDs>": "D-001",
    "<UN-IDs>": "UN-001",
    "<F-IDs and FSD sections>": "F-001",
    "<T-IDs and TSD sections>": "T-001",
    "<RK-IDs and non-blocking O-IDs>": "none",
    "<F-IDs, and UN-IDs where helpful>": "F-001, UN-001",
    "<F-ID this makes possible>": "F-001",
    "<F-ID>": "F-001",
}


def filled_template() -> str:
    """The shipped wave brief with every placeholder resolved as an author would resolve it."""
    text = TEMPLATE.read_text(encoding="utf-8")
    for placeholder, value in TEMPLATE_IDS.items():
        text = text.replace(placeholder, value)
    return re.sub(r"<[^<>\n]*>", "resolved", text)


def standalone_waves(
    *, waves: int = 1, exits: int = 1, decisions: str = "D-001", legend: bool = True
) -> str:
    header = "# Sample Delivery Plan\n\n"
    if legend:
        header += f"Legend: {LEGEND}\n\n"
    body = "".join(
        f"## Wave {index} — Authentication\n\nReferences: {decisions}\n\n"
        for index in range(1, waves + 1)
    )
    body += "".join(
        "## Exit criterion\n\n> An owner authenticates through the documented interface.\n\n"
        for _ in range(exits)
    )
    return header + body


class PlanValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="plan-validator-")
        self.repo = Path(self.temp.name)
        self.docs = self.repo / "docs"
        self.waves = self.docs / "waves"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_repo(
        self,
        *,
        wave_brief: str | None = None,
        index: str | None = None,
        checklist: str = "# PR Checklist\n\n- [ ] Slice outcome demonstrated.\n",
        functional: str | None = None,
        technical: str | None = None,
        concept: str | None = None,
        decisions: str = "| D-001 | accepted | session model |\n",
    ) -> None:
        self.waves.mkdir(parents=True, exist_ok=True)
        (self.docs / "sample-FSD.md").write_text(fsd() if functional is None else functional, encoding="utf-8")
        (self.docs / "sample-TSD.md").write_text(tsd() if technical is None else technical, encoding="utf-8")
        if concept is not None:
            (self.docs / "sample-CON.md").write_text(concept, encoding="utf-8")
        (self.repo / "DECISIONS.md").write_text(decisions, encoding="utf-8")
        (self.waves / "README.md").write_text(wave_index() if index is None else index, encoding="utf-8")
        (self.waves / "PR-CHECKLIST.md").write_text(checklist, encoding="utf-8")
        (self.waves / "wave-1-auth.md").write_text(
            brief() if wave_brief is None else wave_brief, encoding="utf-8"
        )

    def write_standalone(
        self,
        *,
        waves: str | None = None,
        decisions: str = "| D-001 | accepted | session model |\n",
        checklist: str = "# PR Checklist\n\n- [ ] Slice outcome demonstrated.\n",
    ) -> None:
        self.docs.mkdir(parents=True, exist_ok=True)
        (self.docs / "sample-WAVES.md").write_text(
            standalone_waves() if waves is None else waves, encoding="utf-8"
        )
        (self.docs / "sample-DECISIONS.md").write_text(decisions, encoding="utf-8")
        (self.docs / "sample-PR-CHECKLIST.md").write_text(checklist, encoding="utf-8")

    def validate(self, mode: str = "governance", *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--repo",
                str(self.repo),
                "--mode",
                mode,
                "--json",
                *extra,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def expect_invalid(self, result: subprocess.CompletedProcess[str]) -> list[str]:
        self.assertEqual(result.returncode, 3, result.stdout)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        return payload["errors"]

    # --- baseline ---------------------------------------------------------------

    def test_valid_governance_plan_passes(self) -> None:
        self.write_repo()
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])
        self.assertIsInstance(payload["warnings"], list)

    def test_slice_heading_accepts_dash_variants(self) -> None:
        for separator in ["—", "–", "-"]:
            with self.subTest(separator=separator):
                self.write_repo(wave_brief=brief(slices=slice_block(separator=separator)))
                result = self.validate()
                self.assertEqual(result.returncode, 0, result.stdout)

    # --- slice structure --------------------------------------------------------

    def test_missing_slice_label_fails_naming_label_and_slice(self) -> None:
        for label in SLICE_LABELS:
            with self.subTest(label=label):
                self.write_repo(wave_brief=brief(slices=slice_block(drop=(label,))))
                errors = self.expect_invalid(self.validate())
                self.assertTrue(
                    any(f"W1-S1 missing label '{label}'" in error for error in errors), errors
                )

    def test_brief_without_slice_sections_fails(self) -> None:
        self.write_repo(wave_brief=brief(slices=""))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("has no slice sections" in error for error in errors), errors)

    def test_slice_body_ends_at_the_next_heading(self) -> None:
        # A label-shaped line in a later section must not satisfy a slice's label.
        self.write_repo(
            wave_brief=brief(
                slices=slice_block(drop=("Tests",)),
                extra="\n## Mandatory tests\n\n- **Tests:** python3 -m unittest discover\n",
            )
        )
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["docs/waves/wave-1-auth.md W1-S1 missing label 'Tests'"])

    def test_slice_serving_no_functional_id_fails(self) -> None:
        self.write_repo(wave_brief=brief(slices=slice_block(serves="UN-001")))
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["docs/waves/wave-1-auth.md W1-S1 cites no F-ID in Serves"])

    def test_slice_citing_unknown_functional_id_fails(self) -> None:
        self.write_repo(wave_brief=brief(slices=slice_block(serves="F-901, UN-001")))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(
            any("W1-S1 cites unknown functional IDs: F-901" in error for error in errors), errors
        )

    # --- infrastructure slices --------------------------------------------------

    def test_infrastructure_slice_requires_unlocks_naming_a_functional_id(self) -> None:
        without_label = slice_block(kind="infrastructure", serves="UN-001")
        self.write_repo(wave_brief=brief(slices=without_label))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("W1-S1 missing label 'Unlocks'" in error for error in errors), errors)
        self.assertTrue(
            any("W1-S1 is infrastructure but Unlocks names no F-ID" in error for error in errors), errors
        )

        no_functional_id = slice_block(kind="infrastructure", serves="UN-001", unlocks="the sign-in flow")
        self.write_repo(wave_brief=brief(slices=no_functional_id))
        errors = self.expect_invalid(self.validate())
        self.assertEqual(
            errors, ["docs/waves/wave-1-auth.md W1-S1 is infrastructure but Unlocks names no F-ID"]
        )

        unknown = slice_block(kind="infrastructure", serves="UN-001", unlocks="F-901")
        self.write_repo(wave_brief=brief(slices=unknown))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(
            any("W1-S1 cites unknown functional IDs: F-901" in error for error in errors), errors
        )

    def test_infrastructure_slice_with_unlocks_passes_without_serving_a_functional_id(self) -> None:
        self.write_repo(
            wave_brief=brief(slices=slice_block(kind="infrastructure", serves="UN-001", unlocks="F-001"))
        )
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_infrastructure_slice_still_requires_every_other_label(self) -> None:
        self.write_repo(
            wave_brief=brief(
                slices=slice_block(
                    kind="infrastructure", serves="UN-001", unlocks="F-001", drop=("Acceptance evidence",)
                )
            )
        )
        errors = self.expect_invalid(self.validate())
        self.assertEqual(
            errors, ["docs/waves/wave-1-auth.md W1-S1 missing label 'Acceptance evidence'"]
        )

    def test_non_infrastructure_kind_does_not_earn_the_exemption(self) -> None:
        # Only 'infrastructure' trades Serves-names-an-F for Unlocks-names-an-F.
        self.write_repo(wave_brief=brief(slices=slice_block(kind="ui", serves="UN-001")))
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["docs/waves/wave-1-auth.md W1-S1 cites no F-ID in Serves"])

    def test_multiple_slices_are_reported_independently(self) -> None:
        slices = slice_block() + "\n" + slice_block(
            "W1-S2", "Persist sessions", kind="infrastructure", serves="UN-001"
        )
        self.write_repo(wave_brief=brief(slices=slices))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(all("W1-S1" not in error for error in errors), errors)
        self.assertTrue(any("W1-S2 missing label 'Unlocks'" in error for error in errors), errors)

    # --- brief-level citations --------------------------------------------------

    def test_brief_citing_no_user_need_fails(self) -> None:
        self.write_repo(wave_brief=brief(needs="none recorded", slices=slice_block(serves="F-001")))
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["docs/waves/wave-1-auth.md cites no UN-ID user need"])

    def test_brief_citing_unknown_user_need_fails(self) -> None:
        self.write_repo(wave_brief=brief(needs="UN-404"))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("cites unknown user needs: UN-404" in error for error in errors), errors)

    def test_user_need_known_from_concept_baseline_passes(self) -> None:
        self.write_repo(concept=con(), functional=fsd(needs=()))
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_brief_requires_functional_and_technical_citations(self) -> None:
        self.write_repo(wave_brief=brief(functional="none", slices=slice_block(serves="UN-001")))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("cites no F-ID behavior" in error for error in errors), errors)

        self.write_repo(wave_brief=brief(technical="none"))
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["docs/waves/wave-1-auth.md cites no T-ID technical constraint"])

    def test_brief_requires_exactly_one_exit_criterion(self) -> None:
        for exits in [0, 2]:
            with self.subTest(exits=exits):
                self.write_repo(wave_brief=brief(exits=exits))
                errors = self.expect_invalid(self.validate())
                self.assertTrue(
                    any(f"has {exits} exit-criterion sections; expected 1" in error for error in errors),
                    errors,
                )

    def test_unknown_decision_id_rejected(self) -> None:
        self.write_repo(wave_brief=brief(decisions="D-999"))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("cites unknown decisions: D-999" in error for error in errors), errors)

    def test_leftover_placeholders_rejected(self) -> None:
        self.write_repo(
            wave_brief=brief(
                extra="\n## Published contracts frozen at sign-off\n\n- `<ContractName v1>` — consumers\n"
            )
        )
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("<ContractName v1>" in error for error in errors), errors)

    # --- warnings ---------------------------------------------------------------

    def test_all_infrastructure_wave_warns_without_failing(self) -> None:
        self.write_repo(
            wave_brief=brief(
                slices=slice_block(kind="infrastructure", serves="UN-001", unlocks="F-001")
            )
        )
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])
        self.assertEqual(
            payload["warnings"],
            [
                "docs/waves/wave-1-auth.md has only infrastructure slices; "
                "the wave demonstrates no end-to-end outcome"
            ],
        )

    def test_one_end_to_end_slice_silences_the_infrastructure_warning(self) -> None:
        slices = slice_block() + "\n" + slice_block(
            "W1-S2", "Persist sessions", kind="infrastructure", serves="UN-001", unlocks="F-001"
        )
        self.write_repo(wave_brief=brief(slices=slices))
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["warnings"], [])

    # --- the shipped template ---------------------------------------------------

    def test_shipped_wave_brief_template_is_rejected_unfilled(self) -> None:
        self.write_repo(wave_brief=TEMPLATE.read_text(encoding="utf-8"))
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("unresolved template placeholders" in error for error in errors), errors)

    def test_shipped_wave_brief_template_validates_once_filled(self) -> None:
        # Couples assets/wave-brief.md to the validator: an asset edit that drops a
        # required label or changes the slice heading shape fails here.
        self.write_repo(wave_brief=filled_template())
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_shipped_template_slices_stay_attributable(self) -> None:
        # Pins the template's slice heading shape: if a heading stops being recognised,
        # the validator can no longer attribute that slice's error to it.
        broken = filled_template().replace("- **Acceptance evidence:** resolved\n", "", 1)
        self.write_repo(wave_brief=broken)
        errors = self.expect_invalid(self.validate())
        self.assertEqual(
            errors, ["docs/waves/wave-1-auth.md W1-S1 missing label 'Acceptance evidence'"]
        )

    # --- repository shape -------------------------------------------------------

    def test_wave_index_requires_the_fixed_status_legend(self) -> None:
        self.write_repo(index="# Sample Wave Index\n\n## Status\n\nLegend: gated, in progress, done\n")
        errors = self.expect_invalid(self.validate())
        self.assertTrue(
            any("missing the fixed status legend" in error for error in errors), errors
        )

    def test_governance_mode_requires_index_checklist_and_decisions(self) -> None:
        self.waves.mkdir(parents=True)
        (self.docs / "sample-FSD.md").write_text(fsd(), encoding="utf-8")
        (self.docs / "sample-TSD.md").write_text(tsd(), encoding="utf-8")
        errors = self.expect_invalid(self.validate())
        self.assertEqual(
            errors,
            [
                "Missing docs/waves/README.md",
                "Missing docs/waves/PR-CHECKLIST.md",
                "Missing DECISIONS.md",
            ],
        )

    def test_brief_citing_unknown_technical_id_fails(self) -> None:
        self.write_repo(wave_brief=brief(technical="T-909"))
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["docs/waves/wave-1-auth.md cites unknown technical IDs: T-909"])

    def test_mutable_legend_outside_the_canonical_index_fails(self) -> None:
        self.write_repo()
        (self.repo / "AGENTS.md").write_text(f"# Agents\n\nLegend: {LEGEND}\n", encoding="utf-8")
        errors = self.expect_invalid(self.validate())
        self.assertEqual(
            errors, ["Mutable wave legend duplicated outside canonical index: AGENTS.md"]
        )

    def test_exactly_one_canonical_fsd_and_tsd_are_required(self) -> None:
        self.write_repo()
        (self.docs / "other-FSD.md").write_text(fsd(), encoding="utf-8")
        (self.docs / "other-TSD.md").write_text(tsd(), encoding="utf-8")
        errors = self.expect_invalid(self.validate())
        self.assertIn("Expected exactly one canonical FSD; found 2", errors)
        self.assertIn("Expected exactly one canonical TSD; found 2", errors)

    def test_governance_mode_requires_at_least_one_brief(self) -> None:
        self.write_repo()
        (self.waves / "wave-1-auth.md").unlink()
        errors = self.expect_invalid(self.validate())
        self.assertEqual(errors, ["No per-wave brief files found"])

    def test_placeholders_in_the_index_and_checklist_are_rejected(self) -> None:
        self.write_repo(
            index=wave_index() + "\nOwner: <Owner Name>\n",
            checklist="# PR Checklist\n\n- [ ] <Reviewer name> signs off.\n",
        )
        errors = self.expect_invalid(self.validate())
        self.assertTrue(any("README.md contains" in error and "<Owner Name>" in error for error in errors), errors)
        self.assertTrue(
            any("PR-CHECKLIST.md contains" in error and "<Reviewer name>" in error for error in errors),
            errors,
        )

    # --- standalone mode --------------------------------------------------------

    def test_standalone_mode_requires_all_three_documents(self) -> None:
        result = self.validate("standalone", "--plan-name", "sample")
        errors = self.expect_invalid(result)
        self.assertEqual(len(errors), 3)
        self.assertTrue(all(error.startswith("Missing docs/sample-") for error in errors), errors)

    def test_standalone_plan_passes_with_its_three_documents(self) -> None:
        self.write_standalone()
        result = self.validate("standalone", "--plan-name", "sample")
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertIsInstance(payload["warnings"], list)

    def test_standalone_plan_requires_the_fixed_status_legend(self) -> None:
        self.write_standalone(waves=standalone_waves(legend=False))
        errors = self.expect_invalid(self.validate("standalone", "--plan-name", "sample"))
        self.assertEqual(
            errors, ["Standalone waves document is missing the fixed status legend"]
        )

    def test_standalone_plan_requires_one_exit_criterion_per_wave(self) -> None:
        self.write_standalone(waves=standalone_waves(waves=2, exits=1))
        errors = self.expect_invalid(self.validate("standalone", "--plan-name", "sample"))
        self.assertEqual(errors, ["Standalone plan has 2 waves but 1 exit criteria"])

    def test_standalone_plan_rejects_unknown_decisions(self) -> None:
        self.write_standalone(waves=standalone_waves(decisions="D-999"))
        errors = self.expect_invalid(self.validate("standalone", "--plan-name", "sample"))
        self.assertEqual(errors, ["Standalone plan cites unknown decisions: D-999"])


if __name__ == "__main__":
    unittest.main()
