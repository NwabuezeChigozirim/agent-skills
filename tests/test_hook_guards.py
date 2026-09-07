"""Wave 6: classify strings only; transport failure is never action authority."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_review_regressions import gc, ha, module, rt
from test_policy_upgrade import tree_state
import hook_policy as hp


cursor = module("guard_cursor", "governance-system/hooks/cursor/governance-hook.py")
support = ha.support


class CommandGuardTests(unittest.TestCase):
    def test_git_global_options_and_destructive_spellings_require_review(self):
        commands = ["git reset --hard", "git -C /tmp/example reset --hard", "git -C/tmp/example reset HEAD --hard",
                    "git -c core.quotePath=false --no-pager reset --hard", "git --git-dir=/tmp/git --work-tree /tmp/w reset --hard",
                    "git clean -xfd", "git checkout -- app.txt", "git checkout HEAD -- app.txt", "git checkout -f main", "git checkout app.txt",
                    "git restore app.txt", "git switch --discard-changes main", "git branch -D old", "git tag -d v1",
                    "git push --force-with-lease origin main", "git push -vf origin main", "git push origin +main:main",
                    "git push origin :old", "git push -d origin old", "git push --prune", "git push --mirror", "git rebase --abort", "git merge topic",
                    "git worktree remove /tmp/variant", "git stash clear", "git stash pop", "git reset --soft HEAD~1",
                    "git -c alias.wipe='reset --hard' wipe", "git --config-env=alias.wipe=EXTERNAL wipe",
                    "git --unknown-global value reset --hard", "git -C", "git mysterious-alias"]
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(hp.command_requires_review(command))

    def test_wrappers_chains_and_shell_bodies_are_not_executed(self):
        for command in ["env MODE=x git -C /tmp/repo reset --hard", "/usr/bin/git reset --hard",
                        "command git reset --hard", "sudo git reset --hard", "true && git reset --hard",
                        "git status; git clean -fd", "git status\ngit reset --hard", "false || git merge topic",
                        "bash -lc 'git -C /tmp/repo reset --hard'", "sh -c 'git push --force'",
                        "eval 'git reset --hard'", "echo $(git reset --hard)", "echo `git clean -fd`", "git 'unterminated"]:
            with self.subTest(command=command), patch.object(subprocess, "run", side_effect=AssertionError("classification executed a command")):
                self.assertTrue(hp.command_requires_review(command))

    def test_ordinary_commands_and_quoted_examples_remain_ungated(self):
        for command in ["git status --short", "git -C /tmp/repo diff --stat", "git --no-pager log -5", "git add app.txt",
                        "git commit -m 'Fix null check'", "git push origin main", "git branch --show-current",
                        "git worktree list --porcelain", "npm test", "python3 -m unittest",
                        "printf '%s' 'git reset --hard'", "echo 'git clean -fd'", "git --version", "git --help"]:
            with self.subTest(command=command):
                self.assertFalse(hp.command_requires_review(command))

    def test_payload_types_cannot_disappear_through_string_coercion(self):
        for value in [None, [], {"tool_input": []}, {"command": 17}, {"path": []}, {"file_path": "a\0b"},
                      {"stop_hook_active": "true"}, {"tool_input": {"command": False}},
                      {"tool_name": "Write", "tool_input": {}}, {"tool_name": "Bash", "tool_input": {}},
                      {"command": "git status", "tool_input": {"command": "git reset --hard"}},
                      {"path": "first.txt", "tool_input": {"file_path": "second.txt"}}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                hp.validate_payload(value)
        self.assertEqual(hp.action({"tool_name": "Read", "tool_input": {"file_path": "app.txt"}}), ("", None))
        self.assertEqual(hp.action({"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "a.ipynb"}}), ("", "a.ipynb"))


class AdapterGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="hook-transport-")
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.config = self.repo / ".governance/config.json"
        self.config.parent.mkdir()
        self.config.write_text(json.dumps({"enabled": True, "hooks_enabled": True}))

    def decision(self, adapter, payload=b'{"command":"git reset --hard"}', event="pre-tool-use", runtime=None):
        with patch.object(adapter, "repository_root", return_value=self.repo), patch.object(adapter, "runtime_path", return_value=runtime), patch.object(adapter, "EVENT", event):
            return adapter.neutral_decision(payload)

    def test_disabled_and_absent_projects_do_not_invoke_runtime(self):
        for adapter in (ha, cursor):
            for config in (None, {"enabled": False, "hooks_enabled": True}, {"enabled": True, "hooks_enabled": False}):
                if config is None:
                    self.config.unlink(missing_ok=True)
                else:
                    self.config.write_text(json.dumps(config))
                with patch.object(support.subprocess, "run", side_effect=AssertionError("disabled hook invoked runtime")):
                    self.assertEqual(self.decision(adapter)["permission"], "allow")

    def test_missing_runtime_denies_pre_action_but_never_blocks_stop(self):
        for adapter in (ha, cursor):
            self.assertEqual(self.decision(adapter)["permission"], "deny")
            for event in ("stop", "subagent-stop", "session-start", "session-end", "post-tool-use"):
                self.assertEqual(self.decision(adapter,event=event)["permission"], "allow")

    def test_timeout_crash_and_invalid_output_fail_closed_without_echoing_secrets(self):
        responses = [subprocess.TimeoutExpired("SECRET_PAYLOAD", 7), OSError("SECRET_PATH"),
                     subprocess.CompletedProcess([], 4, b'SECRET_OUTPUT', b'SECRET_STDERR'),
                     subprocess.CompletedProcess([], 0, b'[]'), subprocess.CompletedProcess([], 0, b'{}'),
                     subprocess.CompletedProcess([], 0, b'not json SECRET'), subprocess.CompletedProcess([], 0, b'\xff'),
                     subprocess.CompletedProcess([], 0, b'{"permission":"maybe","reason":"SECRET"}'),
                     subprocess.CompletedProcess([], 0, b'{"permission":"allow","reason":17}')]
        for adapter in (ha, cursor):
            for response in responses:
                kwargs = {"side_effect": response} if isinstance(response, Exception) else {"return_value": response}
                with self.subTest(adapter=adapter.__name__, response=str(response)), patch.object(support.subprocess, "run", **kwargs):
                    result = self.decision(adapter, runtime=Path("unused-runtime"))
                    self.assertEqual(result["permission"], "deny")
                    self.assertNotIn("SECRET", json.dumps(result))

    def test_malformed_activation_and_payload_cannot_authorize_actions(self):
        for adapter in (ha, cursor):
            for value in ["not JSON", "[]", '{"enabled":"false","hooks_enabled":true}']:
                self.config.write_text(value)
                self.assertEqual(self.decision(adapter)["permission"], "deny")
            self.config.write_text('{"enabled":true,"hooks_enabled":true}')
            for payload in [b'not JSON', b'[]', b'{"tool_input":[]}', b'{"stop_hook_active":"false"}', b'X' * (hp.MAX_PAYLOAD + 1)]:
                self.assertEqual(self.decision(adapter,payload)["permission"], "deny")

    def test_loop_suppression_is_honored_even_without_runtime(self):
        for adapter in (ha, cursor):
            result = self.decision(adapter, b'{"stop_hook_active":true}', "stop")
            with patch.object(adapter, "EVENT", "stop"):
                self.assertEqual(adapter.translate(result), {})

    def test_valid_responses_use_bounded_transport_and_preserve_no_write(self):
        before = tree_state(self.repo)
        with patch.object(support.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b'{"permission":"ask","reason":"Owner review required"}')) as run:
            for adapter in (ha, cursor):
                self.assertEqual(self.decision(adapter, runtime=Path("runtime"))["permission"], "ask")
                self.assertEqual(run.call_args.kwargs["timeout"], 7)
                self.assertNotIn("shell", run.call_args.kwargs)
        self.assertEqual(before, tree_state(self.repo))

    def test_host_translation_never_turns_no_objection_into_approval(self):
        for adapter in (ha, cursor):
            with patch.object(adapter, "EVENT", "pre-tool-use"):
                self.assertEqual(adapter.translate({"permission": "allow", "reason": "no-collision"}), {})
        with patch.object(ha, "EVENT", "pre-tool-use"):
            answer = ha.translate({"permission": "ask", "reason": "Owner review required"})["hookSpecificOutput"]
            self.assertEqual(answer["permissionDecision"], "ask")
            self.assertEqual(answer["permissionDecisionReason"], "Owner review required")
        with patch.object(cursor, "EVENT", "pre-tool-use"):
            self.assertEqual(cursor.translate({"permission": "ask", "reason": "Owner review required"})["permission"], "deny")

    def test_runtime_cannot_convert_stop_into_a_block(self):
        for adapter in (ha, cursor):
            with patch.object(support.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b'{"permission":"deny","reason":"block"}')):
                result = self.decision(adapter, b'{}', "stop", Path("runtime"))
            self.assertEqual(result["permission"], "allow")
            with patch.object(adapter, "EVENT", "stop"):
                answer = adapter.translate(result)
                self.assertNotIn("decision", answer)
                self.assertNotIn("permission", answer)

    def test_runtime_selection_honors_override_and_host_preference(self):
        with patch.dict(os.environ, {"GOVERNANCECTL": str(self.repo / "missing-runtime")}):
            self.assertIsNone(support.runtime_path())
        with patch.dict(os.environ, {"GOVERNANCECTL": ""}), patch.object(Path, "expanduser", lambda p: p), \
                patch.object(Path, "resolve", lambda p: p), \
                patch.object(Path, "is_file", lambda p: "/skills/" in str(p)):
            self.assertEqual(support.runtime_path("claude"), Path("~/.claude/skills/governance-system/scripts/governancectl"))
            self.assertEqual(support.runtime_path("cursor"), Path("~/.cursor/skills/governance-system/scripts/governancectl"))


class LiveHookTests(unittest.TestCase):
    def setUp(self):
        self.fixture = rt.GovernanceRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.repo = self.fixture.repo
        rt.ctl(self.repo, "discover")
        rt.ctl(self.repo, "install-hooks")

    def decision(self, payload):
        return gc.neutral_hook_decision(self.repo, "pre-tool-use", payload)

    def test_stale_inventory_does_not_hide_new_edit_collision(self):
        sibling = self.fixture.add_sibling()
        (sibling / "app.txt").write_text("New unreviewed work after the last inventory")
        before = tree_state(Path(self.fixture.temp.name))
        result = self.decision({"file_path": "app.txt"})
        self.assertEqual(result["permission"], "ask")
        self.assertEqual(before, tree_state(Path(self.fixture.temp.name)))

    def test_read_does_not_conflict_and_clean_edit_preserves_state(self):
        sibling = self.fixture.add_sibling()
        (sibling / "app.txt").write_text("Other work")
        before = tree_state(Path(self.fixture.temp.name))
        self.assertEqual(self.decision({"tool_name": "Read", "tool_input": {"file_path": "app.txt"}})["permission"], "allow")
        self.assertEqual(self.decision({"tool_name": "Edit", "tool_input": {"file_path": "other.txt"}})["permission"], "allow")
        self.assertEqual(before, tree_state(Path(self.fixture.temp.name)))

    def test_relative_path_is_resolved_against_payload_working_directory(self):
        sibling = self.fixture.add_sibling()
        (sibling / "src").mkdir()
        (sibling / "src/app.txt").write_text("Other work")
        self.assertEqual(self.decision({"cwd": str(self.repo / "src"), "file_path": "app.txt"})["permission"], "ask")
        self.assertEqual(self.decision({"file_path": "../outside.txt"})["permission"], "ask")

    def test_unknown_worktree_ownership_cannot_authorize_edit(self):
        sibling = self.fixture.add_sibling()
        sibling.rename(sibling.with_name("unavailable"))
        self.assertEqual(self.decision({"file_path": "app.txt"})["permission"], "deny")

    def test_direct_runtime_rejects_malformed_pre_action_without_writes(self):
        before = tree_state(self.repo)
        for raw in ('[]', '{"tool_input":[]}', 'not json', '{"command":23}'):
            response = rt.run([sys.executable, str(rt.RUNTIME), "--repo", str(self.repo), "--json", "hook", "pre-tool-use"], self.repo, input_text=raw)
            self.assertEqual(json.loads(response.stdout)["permission"], "deny")
        self.assertEqual(before, tree_state(self.repo))

    def test_missing_installed_support_still_denies_and_disabled_stays_noop(self):
        for platform in ("cursor", "claude"):
            directory = self.repo / ("." + platform) / "hooks"
            (directory / "hook_support.py").unlink()
            response = rt.run([sys.executable, str(directory / "governance-hook.py"), "pre-tool-use"], self.repo, input_text='{"command":"git reset --hard"}')
            value = json.loads(response.stdout)
            decision = value.get("permission") if platform == "cursor" else value["hookSpecificOutput"]["permissionDecision"]
            self.assertEqual(decision, "deny")
        config = gc.load_config(self.repo)
        config["hooks_enabled"] = False
        gc.atomic_write_json(gc.config_path(self.repo), config)
        for platform in ("cursor", "claude"):
            response = rt.run([sys.executable, str(self.repo / ("." + platform) / "hooks/governance-hook.py"), "pre-tool-use"], self.repo, input_text='{}')
            self.assertEqual(json.loads(response.stdout), {})

    def test_missing_shared_install_asset_does_not_partially_replace_wrappers(self):
        with patch.object(gc, "find_skill_root", return_value=self.repo / "missing-skill"):
            before = tree_state(self.repo)
            with self.assertRaises(gc.GovernanceError):
                gc.command_install_hooks(self.repo)
            self.assertEqual(before, tree_state(self.repo))

    def test_installed_wrappers_deny_a_missing_explicit_runtime_on_a_clean_host(self):
        with patch.dict(rt.AUTHOR_ENV, {"GOVERNANCECTL": str(self.repo / "missing-runtime")}):
            for platform in ("cursor", "claude"):
                command = [sys.executable, str(self.repo / ("." + platform) / "hooks/governance-hook.py")]
                response = rt.run(command + ["pre-tool-use"], self.repo, input_text='{"command":"git reset --hard"}')
                value = json.loads(response.stdout)
                permission = value.get("permission") if platform == "cursor" else value["hookSpecificOutput"]["permissionDecision"]
                self.assertEqual(permission, "deny")
                stopped = json.loads(rt.run(command + ["stop"], self.repo, input_text='{}').stdout)
                self.assertNotIn("decision", stopped)
                self.assertIn("warning", json.dumps(stopped))


if __name__ == "__main__":
    unittest.main()
