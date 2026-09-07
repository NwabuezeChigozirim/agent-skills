#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


VALIDATOR = Path(__file__).resolve().parents[1] / "scripts" / "validate_suite.py"
SKILLS = ["governance-system", "plan-waves-slices", "spec-chain"]

SKILL_MD = """---
name: {name}
description: A synthetic skill package used to exercise the suite validator.
---
# {title}

Reads [references/notes.md](references/notes.md).
"""

# spec-chain states the philosophy; the other two point at it across the sibling boundary.
PHILOSOPHY = {
    "spec-chain": "references/need-first.md",
    "governance-system": "../spec-chain/references/need-first.md",
    "plan-waves-slices": "../spec-chain/references/need-first.md",
}


def evals(*, philosophy: str | None, cases: list | None = None) -> str:
    payload: dict[str, object] = {"skill": "synthetic"}
    if philosophy is not None:
        payload["philosophy"] = philosophy
    payload["cases"] = (
        [{"name": "case", "prompt": "do the thing", "should_trigger": True, "expected": ["thing"]}]
        if cases is None
        else cases
    )
    return json.dumps(payload, indent=2)


class SuiteValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="suite-validator-")
        self.root = Path(self.temp.name) / "agent-skills"
        (self.root / "governance-system" / "scripts").mkdir(parents=True)
        (self.root / "governance-system" / "scripts" / "engineering_policy.py").write_text("# Synthetic policy selector\n")
        for package, filename in (("governance-system", "artifact_contracts.py"), ("governance-system", "stage_contracts.py"), ("spec-chain", "specification_graph.py"), ("plan-waves-slices", "planning_graph.py")):
            (self.root / package / "scripts").mkdir(parents=True, exist_ok=True)
            (self.root / package / "scripts" / filename).write_text("# Synthetic graph contract\n")
        for name in SKILLS:
            skill = self.root / name
            for directory in ["references", "assets", "evals"]:
                (skill / directory).mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                SKILL_MD.format(name=name, title=name.replace("-", " ").title()), encoding="utf-8"
            )
            (skill / "references" / "notes.md").write_text("# Notes\n", encoding="utf-8")
            (skill / "evals" / "evals.json").write_text(
                evals(philosophy=PHILOSOPHY[name]), encoding="utf-8"
            )
        (self.root / "spec-chain" / "references" / "need-first.md").write_text(
            "# Need First\n\nThe single statement of the suite's product philosophy.\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def validate(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "--root", str(self.root), "--json", *extra],
            capture_output=True,
            text=True,
            check=False,
        )

    def expect_invalid(self, *extra: str) -> list[str]:
        result = self.validate(*extra)
        self.assertEqual(result.returncode, 3, result.stdout)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])
        return payload["errors"]

    def stub(self, name: str, exit_code: int, message: str = "") -> Path:
        script = Path(self.temp.name) / name
        script.write_text(
            f'#!/usr/bin/env bash\n[[ -n "{message}" ]] && echo "{message}"\nexit {exit_code}\n',
            encoding="utf-8",
        )
        script.chmod(0o755)
        return script

    # --- baseline ---------------------------------------------------------------

    def test_synthetic_suite_is_valid(self) -> None:
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["errors"], [])

    def test_missing_shared_policy_selector_fails(self) -> None:
        (self.root / "governance-system" / "scripts" / "engineering_policy.py").unlink()
        errors = self.expect_invalid()
        self.assertTrue(any("engineering_policy.py" in error for error in errors), errors)

    def test_missing_graph_contract_modules_fail(self) -> None:
        for package, filename in (("governance-system", "artifact_contracts.py"), ("governance-system", "stage_contracts.py"), ("spec-chain", "specification_graph.py"), ("plan-waves-slices", "planning_graph.py")):
            (self.root / package / "scripts" / filename).unlink()
            errors = self.expect_invalid()
            self.assertTrue(any(filename in error for error in errors), errors)

    # --- the philosophy file ----------------------------------------------------

    def test_missing_need_first_fails(self) -> None:
        (self.root / "spec-chain" / "references" / "need-first.md").unlink()
        errors = self.expect_invalid()
        self.assertTrue(
            any(error.endswith("missing references/need-first.md") for error in errors), errors
        )

    def test_empty_need_first_fails(self) -> None:
        (self.root / "spec-chain" / "references" / "need-first.md").write_text("\n\n", encoding="utf-8")
        errors = self.expect_invalid()
        self.assertTrue(
            any(error.endswith("references/need-first.md is empty") for error in errors), errors
        )

    def test_need_first_is_required_of_spec_chain_only(self) -> None:
        # The philosophy is stated once; the siblings cite it rather than restating it.
        self.assertFalse((self.root / "governance-system" / "references" / "need-first.md").exists())
        self.assertEqual(self.validate().returncode, 0)

    # --- eval files and the philosophy pointer -----------------------------------

    def test_unparseable_eval_file_fails(self) -> None:
        (self.root / "spec-chain" / "evals" / "evals.json").write_text("{not json", encoding="utf-8")
        errors = self.expect_invalid()
        self.assertTrue(any("invalid JSON" in error for error in errors), errors)

    def test_eval_file_without_philosophy_pointer_fails(self) -> None:
        (self.root / "plan-waves-slices" / "evals" / "evals.json").write_text(
            evals(philosophy=None), encoding="utf-8"
        )
        errors = self.expect_invalid()
        self.assertTrue(any("missing philosophy pointer" in error for error in errors), errors)

    def test_unresolvable_philosophy_pointer_fails(self) -> None:
        (self.root / "governance-system" / "evals" / "evals.json").write_text(
            evals(philosophy="../spec-chain/references/moved-away.md"), encoding="utf-8"
        )
        errors = self.expect_invalid()
        self.assertTrue(
            any("philosophy pointer does not resolve" in error for error in errors), errors
        )

    def test_eval_file_without_cases_fails(self) -> None:
        (self.root / "spec-chain" / "evals" / "evals.json").write_text(
            evals(philosophy="references/need-first.md", cases=[]), encoding="utf-8"
        )
        errors = self.expect_invalid()
        self.assertTrue(any("no eval cases" in error for error in errors), errors)

    def test_missing_eval_file_fails(self) -> None:
        (self.root / "spec-chain" / "evals" / "evals.json").unlink()
        errors = self.expect_invalid()
        self.assertTrue(any("missing evals/evals.json" in error for error in errors), errors)

    # --- projection parity ------------------------------------------------------

    def test_projections_are_not_checked_by_default(self) -> None:
        # Off by default: a host may install the skills without the backup repository.
        self.assertFalse((self.root.parent / "scripts" / "sync-skills.sh").exists())
        self.assertEqual(self.validate().returncode, 0)

    def test_projection_check_passes_when_the_sync_script_agrees(self) -> None:
        script = self.stub("sync-ok.sh", 0, "projections in sync")
        result = self.validate("--check-projections", "--sync-script", str(script))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_projection_drift_is_relayed_as_errors(self) -> None:
        script = self.stub("sync-drift.sh", 3, "projection drift: cursor/skills")
        errors = self.expect_invalid("--check-projections", "--sync-script", str(script))
        self.assertTrue(any("projection parity failed" in error for error in errors), errors)
        self.assertIn("projection drift: cursor/skills", errors)

    def test_non_parity_exit_is_not_reported_as_drift(self) -> None:
        script = self.stub("sync-broken.sh", 2, "missing required tool: rsync")
        errors = self.expect_invalid("--check-projections", "--sync-script", str(script))
        self.assertTrue(any("could not complete (exit 2)" in error for error in errors), errors)
        self.assertFalse(any("parity failed" in error for error in errors), errors)
        self.assertIn("missing required tool: rsync", errors)

    def test_absent_sync_script_fails_naming_where_it_looked(self) -> None:
        errors = self.expect_invalid("--check-projections")
        expected = self.root.parent / "scripts" / "sync-skills.sh"
        self.assertEqual(errors, [f"{expected}: sync-skills.sh not found; pass --sync-script PATH"])

    def test_non_executable_sync_script_fails(self) -> None:
        script = Path(self.temp.name) / "sync-inert.sh"
        script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        script.chmod(0o644)
        errors = self.expect_invalid("--check-projections", "--sync-script", str(script))
        self.assertEqual(errors, [f"{script}: sync-skills.sh is not executable; pass --sync-script PATH"])

    # --- package structure ------------------------------------------------------

    def test_missing_skill_file_fails(self) -> None:
        (self.root / "plan-waves-slices" / "SKILL.md").unlink()
        errors = self.expect_invalid()
        self.assertTrue(any(error.startswith("Missing ") for error in errors), errors)

    def test_broken_relative_reference_fails(self) -> None:
        (self.root / "spec-chain" / "references" / "notes.md").unlink()
        errors = self.expect_invalid()
        self.assertTrue(
            any("broken reference references/notes.md" in error for error in errors), errors
        )

    def test_missing_frontmatter_name_and_description_fail(self) -> None:
        (self.root / "spec-chain" / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
        errors = self.expect_invalid()
        self.assertTrue(any("missing YAML frontmatter" in error for error in errors), errors)

    def test_oversized_skill_file_fails(self) -> None:
        skill = self.root / "governance-system" / "SKILL.md"
        skill.write_text(
            SKILL_MD.format(name="governance-system", title="Governance System")
            + "\nfiller\n" * 500,
            encoding="utf-8",
        )
        errors = self.expect_invalid()
        self.assertTrue(any("exceeds 500 lines" in error for error in errors), errors)

    def test_legacy_templates_directory_fails(self) -> None:
        (self.root / "spec-chain" / "templates").mkdir()
        errors = self.expect_invalid()
        self.assertTrue(any("legacy templates/ directory remains" in error for error in errors), errors)

    def test_missing_required_directory_fails(self) -> None:
        (self.root / "plan-waves-slices" / "assets").rmdir()
        errors = self.expect_invalid()
        self.assertTrue(any(error.endswith("missing assets/") for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
