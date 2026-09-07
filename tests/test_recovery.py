"""Wave 2 invariants, exercised only in disposable repositories."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import unittest
from unittest.mock import patch

from test_review_regressions import gc, rt
from test_policy_upgrade import tree_state


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = rt.GovernanceRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.repo = self.fixture.repo
        rt.ctl(self.repo, "discover")
        self.sibling = self.fixture.add_sibling()

    def reconcile(self):
        return gc.command_reconcile(self.repo)

    def active(self, kind=None):
        return [r for r in self.fixture.resolutions()
                if not r.get("retired_at") and (kind is None or r["kind"] == kind)]

    def item(self, root=None):
        return next(item for item in gc.inventory(self.repo)["worktrees"] if item["path"] == str(root or self.sibling))

    def manifest(self, snapshot_id):
        return json.loads((self.fixture.common_state() / "snapshots" / f"{snapshot_id}.json").read_text())

    def test_same_head_change_preserves_old_snapshot_and_renews_disposition(self):
        (self.sibling / "app.txt").write_text("first version\n")
        self.reconcile()
        first = self.active("unfinished-variant")[0]
        first_manifest = self.manifest(first["snapshots"][0])
        saved = Path(first_manifest["tracked_patch"]).read_bytes()
        gc.command_resolve(self.repo, first["id"], "defer", "Reviewed version one")
        (self.sibling / "app.txt").write_text("second version\n")
        self.reconcile()
        current = self.active("unfinished-variant")[0]
        self.assertNotEqual(first["id"], current["id"])
        self.assertNotEqual(first["snapshots"], current["snapshots"])
        self.assertEqual(current["status"], "needs-owner")
        self.assertEqual(Path(first_manifest["tracked_patch"]).read_bytes(), saved)
        old = next(r for r in self.fixture.resolutions() if r["id"] == first["id"])
        self.assertEqual(old["choice"], "defer")
        self.assertIn(current["id"], old["superseded_by"])

    def test_unchanged_scan_reuses_snapshots_and_dispositions(self):
        (self.sibling / "app.txt").write_text("unchanged reviewed work\n")
        self.reconcile()
        first = self.active("unfinished-variant")[0]
        gc.command_resolve(self.repo, first["id"], "defer", "Review next wave")
        snapshots = tree_state(self.fixture.common_state() / "snapshots")
        result = self.reconcile()
        current = self.active("unfinished-variant")[0]
        self.assertEqual(current["id"], first["id"])
        self.assertEqual(current["status"], "deferred")
        self.assertEqual(result["snapshots_created"], 0)
        self.assertEqual(tree_state(self.fixture.common_state() / "snapshots"), snapshots)

    def test_index_only_change_changes_version_even_with_identical_working_content(self):
        (self.sibling / "app.txt").write_text("staged first\n")
        rt.run(["git", "add", "app.txt"], self.sibling)
        (self.sibling / "app.txt").write_text("base\n")
        before = self.item()
        (self.sibling / "app.txt").write_text("staged second\n")
        rt.run(["git", "add", "app.txt"], self.sibling)
        (self.sibling / "app.txt").write_text("base\n")
        after = self.item()
        self.assertNotEqual(before["content_fingerprint"], after["content_fingerprint"])

    def test_missing_worktree_is_unknown_and_blocks_closure(self):
        moved = Path(self.fixture.temp.name) / "temporarily-unavailable"
        self.sibling.rename(moved)
        self.addCleanup(lambda: moved.rename(self.sibling))
        item = self.item()
        self.assertEqual(item["availability"], "unavailable")
        self.assertIsNone(item["dirty"])
        self.reconcile()
        self.assertTrue(self.active("unavailable-worktree"))
        with self.assertRaises(gc.GovernanceError):
            gc.command_close_stage(self.repo, True)

    def test_resolve_rejects_content_changed_since_review(self):
        (self.sibling / "app.txt").write_text("reviewed\n")
        self.reconcile()
        record = self.active("unfinished-variant")[0]
        (self.sibling / "app.txt").write_text("not reviewed\n")
        with self.assertRaises(gc.GovernanceError):
            gc.command_resolve(self.repo, record["id"], "defer", "Old review")
        self.assertEqual(self.active("unfinished-variant")[0]["status"], "needs-owner")

    def test_incomplete_capture_requires_real_alternative_recovery(self):
        (self.sibling / ".env").write_text("secret-content-not-for-output\n")
        self.reconcile()
        missing = self.active("incomplete-recovery")[0]
        with self.assertRaises(gc.GovernanceError):
            gc.command_resolve(self.repo, missing["id"], "defer", "An unsupported claim of backup")
        backup = Path(self.fixture.temp.name) / "owner-backup.enc"
        backup.write_bytes(b"Owner-managed encrypted recovery fixture")
        gc.command_resolve(self.repo, missing["id"], "keep-canonical", "Backup covers excluded content", str(backup))
        for record in self.active("unfinished-variant"):
            gc.command_resolve(self.repo, record["id"], "defer", "Owner deferred this recoverable variant")
        self.assertTrue(gc.command_close_stage(self.repo, True)["closed"])
        backup.write_bytes(b"Changed backup no longer proves the same coverage")
        self.assertFalse(gc.command_validate(self.repo)["valid"])

    def test_unrelated_canonical_edit_does_not_reopen_variant_disposition(self):
        (self.sibling / "app.txt").write_text("reviewed variant\n")
        self.reconcile()
        record = self.active("unfinished-variant")[0]
        gc.command_resolve(self.repo, record["id"], "defer", "Wait for next wave")
        (self.repo / "unrelated.txt").write_text("unrelated canonical work\n")
        self.reconcile()
        current = self.active("unfinished-variant")[0]
        self.assertEqual((current["id"], current["status"]), (record["id"], "deferred"))

    def test_archives_restore_staged_and_working_binary_rename_deletion_modes_and_links(self):
        # Create a committed recovery base, then diverge the index and working tree.
        (self.sibling / "remove.txt").write_text("remove this base file\n")
        (self.sibling / "rename.txt").write_text("rename this base file\n")
        self.fixture.commit_all("test: recovery base", self.sibling)
        (self.sibling / "app.txt").write_bytes(b"staged\x00binary\xff\n")
        os.chmod(self.sibling / "app.txt", 0o755)
        rt.run(["git", "add", "app.txt"], self.sibling)
        (self.sibling / "app.txt").write_bytes(b"working\x00binary\xfe\n")
        os.chmod(self.sibling / "app.txt", 0o644)
        rt.run(["git", "mv", "rename.txt", "renamed.txt"], self.sibling)
        (self.sibling / "remove.txt").unlink()
        (self.sibling / "new executable").write_bytes(b"raw\x00new\xff")
        os.chmod(self.sibling / "new executable", 0o755)
        outside = Path(self.fixture.temp.name) / "outside-secret"
        outside.write_bytes(b"NEVER FOLLOW THIS LINK")
        (self.sibling / "external-link").symlink_to(outside)
        (self.sibling / "staged-link").symlink_to("app.txt")
        rt.run(["git", "add", "staged-link"], self.sibling)
        (self.sibling / "staged-link").unlink()
        (self.sibling / "staged-link").symlink_to("renamed.txt")
        captured = self.item()
        self.reconcile()
        record = self.active("unfinished-variant")[0]
        manifest = self.manifest(record["snapshots"][0])
        self.assertEqual(manifest["coverage"]["status"], "complete")
        restore = (Path(self.fixture.temp.name) / "restore").resolve()
        rt.run(["git", "clone", "-q", "--no-checkout", str(self.repo), str(restore)], self.repo)
        rt.run(["git", "checkout", "-q", manifest["head"]], restore)
        with tarfile.open(manifest["index_archive"], "r:gz") as archive:
            for member in archive:
                data = archive.extractfile(member).read()
                result = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=restore,
                                        input=data, capture_output=True, check=True)
                self.assertEqual(result.stdout.strip().decode(), member.name.split("/")[-1])
        # Clear affected index entries, then reconstruct every stage from saved immutable blobs.
        index_input = b"".join(f"0 {'0' * len(manifest['head'])}\t{path}\0".encode() for path in manifest["dirty_paths"])
        index_input += b"".join(f"{entry['mode']} {entry['oid']} {entry['stage']}\t{entry['path']}\0".encode()
                                for entry in manifest["index_entries"])
        subprocess.run(["git", "update-index", "-z", "--index-info"], cwd=restore, input=index_input,
                       capture_output=True, check=True)
        for path, state in manifest["files"].items():
            if state["kind"] == "deleted":
                (restore / path).unlink(missing_ok=True)
        for name in ("working_archive", "untracked_archive"):
            with tarfile.open(manifest[name], "r:gz") as archive:
                for member in archive:
                    target = restore / member.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.unlink(missing_ok=True)
                    if member.issym():
                        target.symlink_to(member.linkname)
                    else:
                        data = archive.extractfile(member).read()
                        self.assertNotIn(b"NEVER FOLLOW THIS LINK", data)
                        target.write_bytes(data)
                        os.chmod(target, member.mode)
        restored = gc.scan_worktree(restore)
        self.assertEqual(restored["content_fingerprint"], captured["content_fingerprint"])
        self.assertEqual(gc.git_bytes(restore, "ls-files", "--stage", "-z"), gc.git_bytes(self.sibling, "ls-files", "--stage", "-z"))

    def test_oversize_and_unreadable_content_stay_incomplete(self):
        (self.sibling / "large.bin").write_bytes(b"x" * 2048)
        with patch.object(gc, "MAX_SNAPSHOT_BYTES", 1024):
            self.reconcile()
        record = self.active("incomplete-recovery")[0]
        self.assertTrue(any(gap["reason"] == "size-limit" for gap in record["recovery_gaps"]))
        # Removing uncovered work is not proof that the prior version was recovered.
        (self.sibling / "large.bin").unlink()
        self.reconcile()
        self.assertIn(record["id"], [r["id"] for r in gc.unresolved_records(self.repo)])
        (self.sibling / "unreadable.bin").write_bytes(b"not readable by the capture")
        original = gc.file_state

        def inaccessible(root, relative, **kwargs):
            return ({"kind": "unreadable"}, None) if relative == "unreadable.bin" else original(root, relative, **kwargs)

        with patch.object(gc, "file_state", side_effect=inaccessible):
            self.reconcile()
        self.assertTrue(any(g["reason"] == "unreadable" for r in self.active("incomplete-recovery") for g in r["recovery_gaps"]))

    def test_capture_race_publishes_no_manifest_and_no_resolution(self):
        (self.sibling / "app.txt").write_text("captured version\n")
        item = self.item()
        original = gc.add_snapshot_file

        def change_after_copy(archive, name, state, data):
            original(archive, name, state, data)
            (self.sibling / "app.txt").write_text("raced version\n")

        with patch.object(gc, "add_snapshot_file", side_effect=change_after_copy):
            with self.assertRaises(gc.GovernanceError):
                gc.snapshot_worktree(self.repo, item)
        self.assertFalse(list((self.fixture.common_state() / "snapshots").glob("*.json")))
        self.assertFalse((self.fixture.common_state() / "resolutions.json").exists())

    def test_partial_publication_retry_is_create_only_and_corruption_is_not_overwritten(self):
        (self.sibling / "app.txt").write_text("durable payload\n")
        item = self.item()
        original = gc.publish_immutable

        def crash_before_manifest(source, target):
            if target.suffix == ".json":
                raise OSError("fixture interrupted before manifest")
            original(source, target)

        with patch.object(gc, "publish_immutable", side_effect=crash_before_manifest):
            with self.assertRaises(OSError):
                gc.snapshot_worktree(self.repo, item)
        directory = self.fixture.common_state() / "snapshots"
        payloads = {p.name: p.read_bytes() for p in directory.iterdir()}
        manifest = gc.snapshot_worktree(self.repo, item)
        self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir() if p.suffix != ".json"}, payloads)
        payload = Path(manifest["working_archive"])
        payload.write_bytes(b"fixture corrupted archive")
        before = tree_state(directory)
        with self.assertRaises(gc.GovernanceError):
            gc.snapshot_worktree(self.repo, item)
        self.assertEqual(before, tree_state(directory))
        self.assertFalse(gc.command_validate(self.repo)["valid"])

    def test_committed_version_advances_require_new_review_and_retain_old_head(self):
        (self.sibling / "app.txt").write_text("committed one\n")
        self.fixture.commit_all("test: first variant", self.sibling)
        self.reconcile()
        first = self.active("divergent-base")[0]
        gc.command_resolve(self.repo, first["id"], "defer", "Reviewed first commit")
        self.assertTrue(gc.check_recovery_ref(self.repo, first["head"]))
        (self.sibling / "app.txt").write_text("committed two\n")
        self.fixture.commit_all("test: second variant", self.sibling)
        self.reconcile()
        current = self.active("divergent-base")[0]
        self.assertNotEqual(first["id"], current["id"])
        self.assertEqual(current["status"], "needs-owner")
        self.assertTrue(gc.check_recovery_ref(self.repo, first["head"]))

    def test_pending_work_committed_is_superseded_not_marked_integrated(self):
        (self.sibling / "app.txt").write_text("pending work\n")
        self.reconcile()
        first = self.active("unfinished-variant")[0]
        gc.command_resolve(self.repo, first["id"], "adopt", "Integration still to do")
        self.fixture.commit_all("test: commit without integration", self.sibling)
        self.reconcile()
        old = next(r for r in self.fixture.resolutions() if r["id"] == first["id"])
        self.assertEqual(old["status"], "pending")
        self.assertIn(self.active("divergent-base")[0]["id"], old["superseded_by"])
        with self.assertRaises(gc.GovernanceError):
            gc.command_close_stage(self.repo, True)

    def test_unrelated_overlap_changes_do_not_reopen_shared_path_review(self):
        (self.repo / "app.txt").write_text("canonical\n")
        (self.sibling / "app.txt").write_text("variant\n")
        self.reconcile()
        first = self.active("overlapping-paths")[0]
        gc.command_resolve(self.repo, first["id"], "keep-canonical", "Reviewed shared path")
        (self.sibling / "other.txt").write_text("unrelated\n")
        self.reconcile()
        current = self.active("overlapping-paths")[0]
        self.assertEqual((current["id"], current["status"], current["snapshots"]),
                         (first["id"], "resolved", first["snapshots"]))

    def test_legacy_decision_is_retained_but_never_inherited_as_version_proof(self):
        (self.sibling / "app.txt").write_text("unversioned old review\n")
        self.reconcile()
        records = self.fixture.resolutions()
        first = next(r for r in records if r["kind"] == "unfinished-variant")
        first.pop("review_fingerprint")
        first.pop("scope_key")
        first.update(choice="defer", note="Legacy review", status="deferred")
        gc.atomic_write_json(self.fixture.common_state() / "resolutions.json", {"records": records})
        self.reconcile()
        current = self.active("unfinished-variant")[0]
        self.assertNotEqual(current["id"], first["id"])
        self.assertEqual(current["status"], "needs-owner")
        old = next(r for r in self.fixture.resolutions() if r["id"] == first["id"])
        self.assertEqual((old["choice"], old["note"]), ("defer", "Legacy review"))

    def test_legacy_snapshot_bytes_survive_and_unknown_coverage_requires_backup(self):
        directory = self.fixture.common_state() / "snapshots"
        directory.mkdir()
        manifest = {"snapshot_id": "old-head-only", "worktree": str(self.sibling), "dirty_paths": ["app.txt"],
                    "tracked_patch": str(directory / "old-head-only.patch")}
        gc.atomic_write_json(directory / "old-head-only.json", manifest)
        (directory / "old-head-only.patch").write_bytes(b"historical patch must remain intact")
        before = {p: p.read_bytes() for p in directory.iterdir()}
        self.reconcile()
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        self.assertTrue(self.active("incomplete-recovery"))
        with self.assertRaises(gc.GovernanceError):
            gc.command_close_stage(self.repo, True)

    def test_diagnostics_are_read_only_and_snapshot_files_are_private(self):
        (self.sibling / "app.txt").write_text("private recovery\n")
        self.reconcile()
        directory = self.fixture.common_state() / "snapshots"
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        for path in directory.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        before = tree_state(Path(self.fixture.temp.name))
        gc.command_audit(self.repo)
        gc.command_validate(self.repo)
        self.assertEqual(before, tree_state(Path(self.fixture.temp.name)))

    def test_alternative_reference_rejects_missing_symlink_empty_or_in_worktree_files(self):
        backup = Path(self.fixture.temp.name) / "backup"
        for value in [backup, self.sibling / "app.txt"]:
            with self.subTest(value=value), self.assertRaises(gc.GovernanceError):
                gc.alternative_recovery(self.repo, str(value))
        backup.touch()
        with self.assertRaises(gc.GovernanceError):
            gc.alternative_recovery(self.repo, str(backup))
        backup.unlink()
        backup.symlink_to(self.sibling / "app.txt")
        with self.assertRaises(gc.GovernanceError):
            gc.alternative_recovery(self.repo, str(backup))

    def test_mode_only_change_and_return_to_old_content_require_fresh_review(self):
        (self.sibling / "app.txt").write_text("version A\n")
        self.reconcile()
        first = self.active("unfinished-variant")[0]
        gc.command_resolve(self.repo, first["id"], "defer", "Reviewed A")
        os.chmod(self.sibling / "app.txt", 0o755)
        self.reconcile()
        executable = self.active("unfinished-variant")[0]
        self.assertNotEqual(executable["id"], first["id"])
        os.chmod(self.sibling / "app.txt", 0o644)
        self.reconcile()
        returned = self.active("unfinished-variant")[0]
        self.assertNotEqual(returned["id"], first["id"])
        self.assertEqual(returned["status"], "needs-owner")
        self.assertEqual(returned["snapshots"], first["snapshots"])

    def test_repeated_choice_is_idempotent_and_revised_choice_preserves_history(self):
        (self.sibling / "app.txt").write_text("reviewed\n")
        self.reconcile()
        record = self.active("unfinished-variant")[0]
        gc.command_resolve(self.repo, record["id"], "defer", "First decision")
        path = self.fixture.common_state() / "resolutions.json"
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        gc.command_resolve(self.repo, record["id"], "defer", "First decision")
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)
        gc.command_resolve(self.repo, record["id"], "keep-canonical", "Revised by owner")
        current = self.active("unfinished-variant")[0]
        self.assertEqual(current["decision_history"][0]["note"], "First decision")

    def test_merge_index_stages_are_all_captured(self):
        oids = []
        for data in [b"merge base\n", b"ours\n", b"theirs\n"]:
            result = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=self.sibling, input=data,
                                    capture_output=True, check=True)
            oids.append(result.stdout.strip().decode())
        index_input = f"0 {'0' * len(oids[0])}\tapp.txt\n"
        index_input += "".join(f"100644 {oid} {stage}\tapp.txt\n" for stage, oid in enumerate(oids, 1))
        rt.run(["git", "update-index", "--index-info"], self.sibling, input_text=index_input)
        (self.sibling / "app.txt").write_text("unresolved working conflict\n")
        self.reconcile()
        manifest = self.manifest(self.active("unfinished-variant")[0]["snapshots"][0])
        self.assertEqual(manifest["coverage"]["status"], "complete")
        self.assertEqual([entry["stage"] for entry in manifest["index_entries"]], [1, 2, 3])
        self.assertEqual(set(manifest["index_objects"]), set(oids))

    def test_tracked_sensitive_working_and_staged_content_is_not_copied(self):
        (self.sibling / ".env").write_text("fixture base config\n")
        self.fixture.commit_all("test: tracked config base", self.sibling)
        (self.sibling / ".env").write_bytes(b"DO-NOT-COPY-STAGED-SECRET")
        rt.run(["git", "add", ".env"], self.sibling)
        (self.sibling / ".env").write_bytes(b"DO-NOT-COPY-WORKING-SECRET")
        self.reconcile()
        manifest = self.manifest(self.active("unfinished-variant")[0]["snapshots"][0])
        self.assertEqual(manifest["coverage"]["status"], "incomplete")
        self.assertEqual(Path(manifest["tracked_patch"]).read_bytes(), b"")
        for name in ("working_archive", "untracked_archive", "index_archive"):
            with tarfile.open(manifest[name], "r:gz") as archive:
                self.assertEqual(archive.getnames(), [])

    def test_closure_detects_change_after_validation(self):
        self.reconcile()
        original = gc.command_validate

        def change_after_validation(repo):
            result = original(repo)
            (self.repo / "late.txt").write_text("arrived after validation\n")
            return result

        with patch.object(gc, "command_validate", side_effect=change_after_validation):
            with self.assertRaisesRegex(gc.GovernanceError, "changed while closing"):
                gc.command_close_stage(self.repo, True)
        self.assertNotEqual(self.fixture.run_state()["status"], "closed")

    def test_symbolic_or_conflicting_retention_refs_are_not_overwritten(self):
        head = gc.current_head(self.sibling)
        ref = gc.recovery_ref(head)
        rt.run(["git", "symbolic-ref", ref, "refs/heads/nonexistent-fixture"], self.repo)
        with self.assertRaises(gc.GovernanceError):
            gc.pin_head(self.repo, head)
        self.assertEqual(gc.git(self.repo, "symbolic-ref", ref), "refs/heads/nonexistent-fixture")

    def test_malformed_manifest_is_a_gate_not_silent_reuse(self):
        (self.sibling / "app.txt").write_text("content\n")
        self.reconcile()
        record = self.active("unfinished-variant")[0]
        manifest = self.manifest(record["snapshots"][0])
        manifest.pop("files")
        gc.atomic_write_json(self.fixture.common_state() / "snapshots" / f"{record['snapshots'][0]}.json", manifest)
        with self.assertRaisesRegex(gc.GovernanceError, "Malformed recovery manifest"):
            self.reconcile()

    def test_valid_json_metadata_corruption_is_detected_without_rewriting_it(self):
        (self.sibling / "app.txt").write_text("recoverable content\n")
        self.reconcile()
        record = self.active("unfinished-variant")[0]
        manifest = self.manifest(record["snapshots"][0])
        manifest["files"]["app.txt"]["mode"] = 0o777
        path = self.fixture.common_state() / "snapshots" / f"{record['snapshots'][0]}.json"
        gc.atomic_write_json(path, manifest)
        before = tree_state(self.fixture.common_state() / "snapshots")
        validation = gc.command_validate(self.repo)
        self.assertFalse(validation["valid"])
        self.assertTrue(any("Changed recovery metadata" in error for error in validation["errors"]))
        with self.assertRaises(gc.GovernanceError):
            self.reconcile()
        self.assertEqual(before, tree_state(self.fixture.common_state() / "snapshots"))


if __name__ == "__main__":
    unittest.main()
