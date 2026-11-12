#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]
VERIFYCTL = PACKAGE / "scripts" / "verifyctl"
EXAMPLE = PACKAGE / "skills" / "create-verification-skill" / "references" / "feature-map-example"

SKILL_MD = """---
name: verify-notes
description: Drive the Notes web UI and CLI to prove behavior. Use to verify any Notes change.
---

# Verify Notes

## Launch

Run `control-notes launch` and wait for `ready on 4173`.

## Doctor

Run `control-notes doctor`.

## Drive

Use `control-notes browser` and `control-notes cli`.

## Evidence

Write proof under the run directory and seal it with `verifyctl record`.

## Cleanup

Run `control-notes stop`. Evidence is kept.

## Helpers

`control-notes` is on PATH.
"""


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, "-B", str(VERIFYCTL), *args], capture_output=True, text=True, check=False)


class VerifyctlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp, True)
        self.skill = self.temp / "verify-notes"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
        shutil.copytree(EXAMPLE, self.skill / "features")
        self.run_dir = self.temp / "runs" / "r1"
        self.run_dir.mkdir(parents=True)

    def proof(self, name: str = "list.png", data: bytes = b"proof") -> str:
        (self.run_dir / name).write_bytes(data)
        return name

    def record(self, feature: str, outcome: str = "verified", *extra: str, entry: str = "New note button"):
        return run("record", "--skill", str(self.skill), "--run", str(self.run_dir), "--feature", feature,
                   "--entry", entry, "--outcome", outcome, *extra)

    def check(self, *scope: str):
        return run("--json", "check", "--skill", str(self.skill), "--run", str(self.run_dir), *scope)

    def lint_errors(self) -> list[str]:
        result = run("--json", "lint", "--skill", str(self.skill))
        return json.loads(result.stdout)["errors"]

    # lint

    def test_shipped_example_map_lints_clean(self) -> None:
        result = run("lint", "--skill", str(self.skill))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_frontmatter_is_rejected(self) -> None:
        (self.skill / "SKILL.md").write_text(SKILL_MD.split("---\n", 2)[2], encoding="utf-8")
        self.assertTrue(any("frontmatter" in e for e in self.lint_errors()))

    def test_missing_required_section_is_rejected(self) -> None:
        (self.skill / "SKILL.md").write_text(SKILL_MD.replace("## Doctor", "## Health"), encoding="utf-8")
        self.assertTrue(any("'## Doctor'" in e for e in self.lint_errors()))

    def test_placeholder_is_rejected(self) -> None:
        (self.skill / "SKILL.md").write_text(SKILL_MD.replace("Verify Notes", "Verify <app>"), encoding="utf-8")
        self.assertTrue(any("placeholder" in e for e in self.lint_errors()))

    def test_unlisted_and_dangling_features_are_rejected(self) -> None:
        shutil.copy(self.skill / "features" / "search.md", self.skill / "features" / "orphan.md")
        (self.skill / "features" / "search.md").unlink()
        errors = self.lint_errors()
        self.assertTrue(any("orphan.md: not listed" in e for e in errors))
        self.assertTrue(any("missing file search.md" in e for e in errors))

    def test_feature_sections_must_match_the_contract(self) -> None:
        path = self.skill / "features" / "search.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## Gotchas", "## Notes"), encoding="utf-8")
        self.assertTrue(any("exactly these H2 sections" in e for e in self.lint_errors()))

    def test_driving_section_must_open_with_preconditions(self) -> None:
        path = self.skill / "features" / "search.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Preconditions:", "Setup:"), encoding="utf-8")
        self.assertTrue(any("Preconditions:" in e for e in self.lint_errors()))

    def test_helper_must_be_executable_and_documented(self) -> None:
        helper = self.skill / "drive.sh"
        helper.write_text("#!/bin/sh\n", encoding="utf-8")
        helper.chmod(0o644)
        errors = self.lint_errors()
        self.assertTrue(any("not executable" in e for e in errors))
        self.assertTrue(any("not shown in SKILL.md" in e for e in errors))

    # record

    def test_verified_needs_an_artifact(self) -> None:
        result = self.record("create-note")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--artifact", result.stderr)

    def test_unreachable_needs_a_reason(self) -> None:
        self.assertEqual(self.record("create-note", "unreachable").returncode, 2)

    def test_unknown_feature_is_refused(self) -> None:
        result = self.record("billing", "verified", "--artifact", self.proof())
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown feature", result.stderr)

    def test_artifact_outside_run_and_empty_artifact_are_refused(self) -> None:
        outside = self.temp / "elsewhere.png"
        outside.write_bytes(b"x")
        self.assertEqual(self.record("create-note", "verified", "--artifact", str(outside)).returncode, 2)
        self.assertEqual(self.record("create-note", "verified", "--artifact", self.proof("empty.png", b"")).returncode, 2)

    # check

    def test_recorded_proof_passes_for_that_feature(self) -> None:
        self.assertEqual(self.record("create-note", "verified", "--artifact", self.proof()).returncode, 0)
        result = self.check("--feature", "create-note")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_all_requires_every_mapped_feature(self) -> None:
        self.record("create-note", "verified", "--artifact", self.proof())
        result = self.check("--all")
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("search: no evidence" in e for e in json.loads(result.stdout)["errors"]))

    def test_tampered_or_deleted_evidence_fails(self) -> None:
        self.record("create-note", "verified", "--artifact", self.proof())
        (self.run_dir / "list.png").write_bytes(b"edited")
        self.assertTrue(any("changed after" in e for e in json.loads(self.check("--feature", "create-note").stdout)["errors"]))
        (self.run_dir / "list.png").unlink()
        self.assertTrue(any("evidence missing" in e for e in json.loads(self.check("--feature", "create-note").stdout)["errors"]))

    def test_later_failure_supersedes_earlier_pass(self) -> None:
        self.record("create-note", "verified", "--artifact", self.proof())
        self.record("create-note", "failed", "--reason", "Save button stayed disabled")
        result = self.check("--feature", "create-note")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(len(json.loads((self.run_dir / "manifest.json").read_text())["records"]), 2)

    def test_unreachable_entry_is_not_reported_as_verified(self) -> None:
        self.record("create-note", "unreachable", "--reason", "needs a paid seat", entry="CLI")
        result = self.check("--feature", "create-note")
        self.assertEqual(result.returncode, 3)
        self.assertTrue(any("not verified" in e for e in json.loads(result.stdout)["errors"]))

    def test_failure_on_one_entry_blocks_despite_pass_on_another(self) -> None:
        self.record("create-note", "verified", "--artifact", self.proof())
        self.record("create-note", "failed", "--reason", "exit code 1", entry="CLI")
        self.assertEqual(self.check("--feature", "create-note").returncode, 3)

    def test_check_refuses_a_run_without_a_manifest(self) -> None:
        self.assertEqual(self.check("--all").returncode, 2)


if __name__ == "__main__":
    unittest.main()
