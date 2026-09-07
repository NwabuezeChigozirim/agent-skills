"""Wave 1 acceptance: explicit adoption and genuinely read-only inspection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys
import unittest
from unittest.mock import patch

from test_review_regressions import ROOT, gc, rt
import engineering_policy as policy


def tree_state(root: Path) -> dict:
    """Compare bytes, modes, mtimes and directory entries, including .git state.

    Access times are intentionally excluded: reading a file may update its atime.
    Symlinks are recorded as links, never traversed into other projects.
    """
    result = {}
    for path in [root, *sorted(root.rglob("*"))]:
        info = path.lstat()
        if path.is_symlink():
            contents = str(path.readlink())
        elif path.is_file():
            contents = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            contents = None
        result[str(path.relative_to(root))] = (info.st_mode, info.st_mtime_ns, contents)
    return result


class PolicyUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = rt.GovernanceRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.repo = self.fixture.repo
        self.config = self.repo / ".governance" / "config.json"

    def configure(self, schema=3, *, canonical=None, version=None):
        config = {
            "schema_version": schema, "suite_version": "2.0.0",
            "repository_id": "old-path-identity" if schema == 2 else gc.repo_identity(self.repo),
            "enabled": True, "hooks_enabled": False, "project_slug": "repo",
            "created_at": "2026-01-01T00:00:00+00:00",
            "project_extension": {"keep": "this project-specific value"},
        }
        if schema == 2:
            config.update(canonical_worktree=str(canonical or self.repo), canonical_branch="main")
        if version is not None:
            config["policy_version"] = version
        self.config.parent.mkdir(exist_ok=True)
        self.config.write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")
        return config

    def assert_read_only(self, command, *args):
        root = Path(self.fixture.temp.name)
        before = tree_state(root)
        result = rt.ctl(self.repo, command, *args, check=False)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(tree_state(root), before, f"{command} {args} changed the filesystem")
        return result, json.loads(result.stdout)

    def inspect_all(self):
        for command, args in [
            ("doctor", ()), ("status", ()), ("audit", ()), ("validate", ()),
            ("upgrade", ("--dry-run",)), ("upgrade", ("--dry-run", "--policy", "legacy")),
        ]:
            with self.subTest(command=command, args=args):
                self.assert_read_only(command, *args)

    def test_uninitialized_inspection_does_not_create_config_state_or_lock(self):
        self.inspect_all()
        self.assertFalse(self.config.exists())
        self.assertFalse(self.fixture.common_state().exists())

    def test_schema_2_and_3_inspection_never_migrates_or_initializes(self):
        rt.write_governance_docs(self.repo)
        for schema in (2, 3):
            with self.subTest(schema=schema):
                original = self.configure(schema)
                self.inspect_all()
                self.assertEqual(json.loads(self.config.read_text()), original)
                self.assertFalse(self.fixture.common_state().exists())

    def test_dirty_index_and_sibling_worktree_inspection_is_read_only(self):
        rt.ctl(self.repo, "discover")
        sibling = self.fixture.add_sibling()
        (self.repo / "app.txt").write_text("staged\n")
        rt.run(["git", "add", "app.txt"], self.repo)
        (self.repo / "app.txt").write_text("unstaged after staged\n")
        (sibling / "untracked.txt").write_text("another agent's work\n")
        self.inspect_all()

    def test_canonical_lookup_is_read_only_and_respects_legacy_selection(self):
        sibling = self.fixture.add_sibling()
        self.configure(2, canonical=sibling)
        before = tree_state(Path(self.fixture.temp.name))
        self.assertEqual(Path(gc.load_canonical(self.repo)["canonical_worktree"]), sibling)
        self.assertEqual(tree_state(Path(self.fixture.temp.name)), before)

    def test_explicit_legacy_upgrade_preserves_bytes_extensions_and_canonical(self):
        sibling = self.fixture.add_sibling()
        original = self.configure(2, canonical=sibling)
        before = self.config.read_bytes()
        (self.repo / "DECISIONS.md").write_text("Owner's unchanged historical decisions.\n")
        preview = json.loads(rt.ctl(self.repo, "upgrade", "--dry-run", "--policy", "legacy").stdout)
        self.assertTrue(preview["valid"])
        self.assertFalse(preview["changed"])
        result = json.loads(rt.ctl(self.repo, "upgrade", "--apply", "--policy", "legacy").stdout)
        self.assertTrue(result["changed"])
        upgraded = json.loads(self.config.read_text())
        self.assertEqual(upgraded["policy_version"], 1)
        self.assertEqual(upgraded["schema_version"], 3)
        self.assertEqual(upgraded["project_extension"], original["project_extension"])
        self.assertEqual(upgraded["created_at"], original["created_at"])
        self.assertNotIn("canonical_worktree", upgraded)
        backup = Path(result["backup"])
        self.assertEqual((backup / "config.json").read_bytes(), before)
        self.assertEqual(stat.S_IMODE((backup / "config.json").stat().st_mode), 0o600)
        self.assertEqual(Path(gc.load_canonical(self.repo)["canonical_worktree"]), sibling)
        self.assertEqual((self.repo / "DECISIONS.md").read_text(), "Owner's unchanged historical decisions.\n")
        _, second = self.assert_read_only("upgrade", "--apply", "--policy", "legacy")
        self.assertTrue(second["applied"])
        self.assertFalse(second["changed"])

    def test_schema_3_upgrade_only_adds_explicit_policy_without_creating_canonical(self):
        self.configure()
        result = json.loads(rt.ctl(self.repo, "upgrade", "--apply", "--policy", "legacy").stdout)
        self.assertTrue(result["changed"])
        self.assertFalse(gc.canonical_state_path(self.repo).exists())
        self.assertEqual(json.loads(self.config.read_text())["policy_version"], 1)

    def test_upgrade_does_not_broaden_config_file_permissions(self):
        self.configure(2)
        self.config.chmod(0o600)
        rt.ctl(self.repo, "upgrade", "--apply", "--policy", "legacy")
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o600)

    def test_existing_canonical_and_run_history_are_not_rewritten(self):
        rt.ctl(self.repo, "discover")
        self.configure(2)
        before = gc.canonical_state_path(self.repo).read_bytes()
        run_before = gc.state_path(self.repo, "run-state.json").read_bytes()
        result = json.loads(rt.ctl(self.repo, "upgrade", "--apply", "--policy", "legacy").stdout)
        self.assertEqual(gc.canonical_state_path(self.repo).read_bytes(), before)
        self.assertEqual(gc.state_path(self.repo, "run-state.json").read_bytes(), run_before)
        self.assertEqual((Path(result["backup"]) / "canonical.json").read_bytes(), before)

    def test_current_policy_is_unavailable_and_cannot_be_partially_activated(self):
        self.configure()
        for action in ("--dry-run", "--apply"):
            result, payload = self.assert_read_only("upgrade", action)
            self.assertEqual(result.returncode, 4)
            self.assertFalse(payload["valid"])
            self.assertFalse(payload["applied"])
            self.assertTrue(any("not released" in item for item in payload["errors"]))

    def test_manually_setting_current_policy_does_not_enable_unguarded_execution(self):
        self.configure(version=2)
        for command, args in [("discover", ()), ("install-hooks", ()),
                              ("close-stage", ("--owner-approved",)),
                              ("upgrade", ("--apply", "--policy", "legacy"))]:
            result, _ = self.assert_read_only(command, *args)
            self.assertEqual(result.returncode, 4)

    def test_malformed_foreign_and_unknown_configs_have_structured_read_only_errors(self):
        valid = self.configure()
        for bad in ([], {**valid, "schema_version": 999}, {**valid, "repository_id": "foreign"},
                    {**valid, "policy_version": True}, {**valid, "policy_version": "2"}):
            with self.subTest(config=bad):
                self.config.write_text(json.dumps(bad))
                result, payload = self.assert_read_only("audit")
                self.assertEqual(result.returncode, 3)
                self.assertTrue(payload["errors"])
                result, _ = self.assert_read_only("upgrade", "--apply", "--policy", "legacy")
                self.assertEqual(result.returncode, 4)

    def test_upgrade_requires_exactly_one_explicit_action(self):
        self.configure()
        for args in [(), ("--apply", "--dry-run")]:
            before = tree_state(self.repo)
            result = rt.ctl(self.repo, "upgrade", *args, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(tree_state(self.repo), before)

    def test_corrupt_canonical_state_is_reported_without_repair(self):
        self.configure()
        canonical = gc.canonical_state_path(self.repo)
        canonical.parent.mkdir(parents=True)
        for contents in ("not json", "[]", "{}"):
            canonical.write_text(contents)
            result, payload = self.assert_read_only("audit")
            self.assertEqual(result.returncode, 3)
            self.assertTrue(payload["errors"])

    def test_metadata_upgrade_refuses_symlink_targets_without_writes(self):
        self.configure(2)
        actual = self.repo / "external-config.json"
        self.config.rename(actual)
        self.config.symlink_to(actual)
        result, payload = self.assert_read_only("upgrade", "--apply", "--policy", "legacy")
        self.assertEqual(result.returncode, 4)
        self.assertTrue(any("symlink" in item for item in payload["errors"]))

    def test_existing_migration_backup_is_not_overwritten(self):
        self.configure(2)
        original = self.config.read_bytes()
        applied = json.loads(rt.ctl(self.repo, "upgrade", "--apply", "--policy", "legacy").stdout)
        # Simulate restoring only pre-migration config and canonical absence after
        # an interrupted attempt. Existing recovery material must remain intact.
        self.config.write_bytes(original)
        gc.canonical_state_path(self.repo).unlink()
        backup = Path(applied["backup"])
        before_backup = tree_state(backup)
        result = rt.ctl(self.repo, "upgrade", "--apply", "--policy", "legacy", check=False)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(tree_state(backup), before_backup)
        self.assertEqual(self.config.read_bytes(), original)

    def test_config_change_before_snapshot_is_not_overwritten(self):
        self.configure()
        load = gc.load_config
        changed = False

        def concurrent_change(repo, *, required=False):
            nonlocal changed
            config = load(repo, required=required)
            if required and not changed:
                changed = True
                updated = {**config, "project_extension": {"keep": "concurrent owner edit"}}
                self.config.write_text(json.dumps(updated))
            return config

        with patch.object(gc, "load_config", side_effect=concurrent_change):
            with self.assertRaises(gc.GovernanceError) as raised:
                gc.command_upgrade(self.repo, apply=True, target_policy="legacy")
        self.assertTrue(changed)
        self.assertEqual(raised.exception.exit_code, 4)
        self.assertEqual(json.loads(self.config.read_text())["project_extension"]["keep"], "concurrent owner edit")
        self.assertFalse((self.fixture.common_state() / "upgrades").exists())

    def test_legacy_clone_defaults_locally_without_rewriting_committed_paths(self):
        self.configure(2, canonical=Path(self.fixture.temp.name) / "unavailable")
        self.fixture.commit_all("test: legacy config")
        clone = Path(self.fixture.temp.name) / "clone"
        rt.run(["git", "clone", "-q", str(self.repo), str(clone)], Path(self.fixture.temp.name))
        before = tree_state(clone)
        doctor = json.loads(rt.ctl(clone, "doctor").stdout)
        self.assertEqual(Path(doctor["canonical_worktree"]).resolve(), clone.resolve())
        self.assertEqual(doctor["config_schema"], 2)
        self.assertEqual(tree_state(clone), before)

    def test_new_initialization_explicitly_records_only_released_policy(self):
        rt.ctl(self.repo, "discover")
        self.assertEqual(json.loads(self.config.read_text())["policy_version"], policy.DEFAULT_POLICY)
        self.assertEqual(policy.DEFAULT_POLICY, 1)  # Release gate changes only after Wave 6.

    def test_cli_validators_report_policy_and_refuse_unavailable_preview(self):
        rt.write_governance_docs(self.repo)
        scripts = [
            ("spec-chain/scripts/validate_spec.py", ["--project", "repo", "--mode", "governance"]),
            ("spec-chain/scripts/trace_chain.py", ["--project", "repo"]),
            ("plan-waves-slices/scripts/validate_plan.py", ["--mode", "governance"]),
        ]
        for script, extra in scripts:
            for selection in ("auto", "legacy", "current"):
                with self.subTest(script=script, selection=selection):
                    before = tree_state(self.repo)
                    result = rt.run([sys.executable, str(ROOT / script), "--repo", str(self.repo), *extra,
                                     "--json", "--policy", selection], self.repo, check=False)
                    payload = json.loads(result.stdout)
                    self.assertEqual(result.returncode, 3 if selection == "current" else 0, result.stdout)
                    self.assertEqual(payload["policy_version"], 2 if selection == "current" else 1)
                    self.assertEqual(tree_state(self.repo), before)

    def test_three_sibling_packages_run_without_suite_root_helpers(self):
        installed = Path(self.fixture.temp.name) / "installed"
        for skill in ("governance-system", "spec-chain", "plan-waves-slices"):
            shutil.copytree(ROOT / skill, installed / skill, ignore=shutil.ignore_patterns("__pycache__", "node_modules"))
        self.assertFalse((installed / "scripts").exists())
        rt.write_governance_docs(self.repo)
        for script, arguments in [
            ("governance-system/scripts/governancectl", ["audit"]),
            ("spec-chain/scripts/validate_spec.py", ["--project", "repo", "--mode", "governance"]),
            ("spec-chain/scripts/trace_chain.py", ["--project", "repo"]),
            ("plan-waves-slices/scripts/validate_plan.py", ["--mode", "governance"]),
        ]:
            result = rt.run([sys.executable, str(installed / script), "--repo", str(self.repo), "--json", *arguments],
                            self.repo, check=False)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_standalone_metadata_and_governance_authority_cannot_be_downgraded(self):
        artifact = self.repo / "sample.md"
        artifact.write_text("---\npolicy_version: 2\n---\n# Sample\n")
        result = policy.evaluate_policy(self.repo, [artifact], "legacy")
        self.assertEqual(result["policy_version"], 2)
        self.assertTrue(any("downgrade" in message for message in result["policy_errors"]))
        self.configure(version=1)
        result = policy.evaluate_policy(self.repo, [artifact])
        self.assertTrue(any("conflicts" in message for message in result["policy_errors"]))

    def test_conflicting_and_malformed_document_markers_are_errors(self):
        first, second = self.repo / "first.md", self.repo / "second.md"
        first.write_text("---\npolicy_version: 1\n---\n")
        second.write_text("---\npolicy_version: 2\n---\n")
        self.assertTrue(policy.evaluate_policy(self.repo, [first, second])["policy_errors"])
        second.write_text("---\npolicy_version: true\n---\n")
        self.assertTrue(policy.evaluate_policy(self.repo, [second])["policy_errors"])
        second.write_text("---\npolicy_version: 1\npolicy_version: 1\n---\n")
        self.assertTrue(policy.evaluate_policy(self.repo, [second])["policy_errors"])


if __name__ == "__main__":
    unittest.main()
