#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNTIME = Path(__file__).resolve().parents[1] / "scripts" / "governancectl"
LEGEND = "⏸ gated · 🟡 approved & in progress · ✅ done & signed off"


def configured_identity() -> tuple[str, str]:
    # Hosts may enforce a specific commit author through global git hooks, so fixture
    # commits use the configured identity and fall back to a neutral one when unset.
    def read(key: str, fallback: str) -> str:
        result = subprocess.run(
            ["git", "config", "--get", key], capture_output=True, text=True, check=False
        )
        value = result.stdout.strip()
        return value or fallback

    return read("user.name", "Governance Fixture"), read("user.email", "fixture@example.invalid")


_NAME, _EMAIL = configured_identity()
AUTHOR_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": _NAME,
    "GIT_AUTHOR_EMAIL": _EMAIL,
    "GIT_COMMITTER_NAME": _NAME,
    "GIT_COMMITTER_EMAIL": _EMAIL,
}

# The FSD's upstream when no CON exists: UR/UN items in the CON schema plus the
# ratified authority that stands in for the concept stage.
NEEDS_BASELINE = """## User needs baseline
- **Baseline authority:** D-001
### UR-001 — Owner
- **Description:** owns the work recorded in this repository
- **Environment:** laptop, single working session
- **Expertise:** experienced
- **Evidence class:** stakeholder-requirement
### UN-001 — Record a unit of work
- **Roles:** UR-001
- **Context:** starting a unit of work that others will review
- **Underlying job:** keep an attributable record of what was agreed
- **Decision or action:** record the item or drop it
- **Desired outcome:** the item exists and names its owner
- **Evidence class:** stakeholder-requirement
- **Confidence:** high
"""

# Structurally valid, but C-001 is accepted on an 'assumption': the one fixture that
# provokes a specification warning rather than an error.
WARNING_CON = """---
document_type: CON
authority: concept
---
# Sample Concept Note
## User roles
| UR-ID | Role |
|---|---|
| UR-001 | Owner |
### UR-001 — Owner
- **Description:** owns the work recorded in this repository
- **Environment:** laptop, single working session
- **Expertise:** experienced
- **Evidence class:** observed-behavior
- **Evidence or source:** three working sessions observed
## User needs
### UN-001 — Record a unit of work
- **Roles:** UR-001
- **Context:** starting a unit of work that others will review
- **Stated request:** "give me a form"
- **Underlying job:** keep an attributable record of what was agreed
- **Decision or action:** record the item or drop it
- **Information required:** what the item is and who owns it
- **Desired outcome:** the item exists and names its owner
- **Evidence class:** observed-behavior
- **Evidence or source:** session notes
- **Confidence:** high
## Non-goals
| Non-goal | Reason |
|---|---|
| Scheduling the work | outside the job |
## Response inventory
| C-ID | Kind | Serves | Status |
|---|---|---|---|
| C-001 | capability | UN-001 | accepted |
### C-001 — Create an item explicitly
- **Kind:** capability
- **Serves:** UN-001
- **Status:** accepted
- **User:** owner
- **Context:** starting a unit of work
- **Underlying job:** keep an attributable record
- **Decision or action:** record the item
- **Required information:** item details and owner
- **Desired outcome:** the item exists and names its owner
- **Proposed response:** an explicit create step
- **Simplest adequate response:** one create call
- **Alternatives considered:** implicit creation (rejected: unattributable)
- **Incremental value:** attribution without a separate log
- **Cost:** low
- **Trust and privacy:** the owner is recorded, nothing further
- **Removal test:** owners keep the record outside the tool
- **Evidence class:** assumption
- **Decision references:** D-001
## Blocking open decisions
No blocking O-IDs remain.
## Verification register
| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | no external claims |
## Recommendation
Build.
"""


def functional_specification(*, baseline: str = NEEDS_BASELINE, serves: str = "UN-001") -> str:
    """Minimal valid FSD. A CON and a baseline are duplicate authority, so they never co-occur."""
    return f"""---
document_type: FSD
authority: behavior
---
# Sample Functional Specification
{baseline}
## Functional inventory
| F-ID | Kind | Name |
|---|---|---|
| F-001 | endpoint | Create item |
## Functional specifications
### F-001 — Create item
- **Kind:** endpoint
- **Purpose:** record a unit of work against its owner
- **Serves:** {serves}
- **Actors and permission:** owner; denial is explicit
- **Context/trigger:** the owner starts a unit of work
- **Inputs/content:** item details
- **Actions and outcomes:** the item is created and attributed
- **States:** initial, success, failure
- **Rules:** valid details required
- **Errors and recovery:** correct and retry
- **Dependencies:** D-001
- **Done when:** the owner creates an item and sees it attributed
## Blocking open decisions
No blocking O-IDs remain.
## Verification register
| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | no external claims |
"""


VALID_FSD = functional_specification()
CON_FSD = functional_specification(baseline="", serves="UN-001, C-001")

VALID_TSD = """---
document_type: TSD
authority: technical-design
---
# Sample Technical Design
## Cost evidence
Not applicable — no external cost conclusion.
## Technical requirements
### T-001 — Create item service
- **Purpose:** realize item creation
- **Realizes:** F-001, D-001
- **Design:** service boundary
- **Interfaces/contracts:** item contract
- **Invariants and failure handling:** atomic create
- **Security/data considerations:** owner authorization
- **Verification:** integration test
- **Dependencies:** none
- **Risks:** none
## Product deltas surfaced
None
## Blocking open decisions
No blocking O-IDs remain.
## Verification register
| Claim | Source | Accessed | Conclusion |
|---|---|---|---|
| Not applicable | — | — | no external claims |
## Traceability
| F-ID | Serves | Implementing T-IDs | Verification |
|---|---|---|---|
| F-001 | UN-001 | T-001 | integration test |
"""

VALID_BRIEF = """# Wave 1 — Create item

## References

- Decisions: D-001
- User needs: UN-001
- Behaviour: F-001
- Technical design: T-001

## Exit criterion

> Owner creates an item through the documented interface.

## Slices

### W1-S1 — Create item end to end

- **Outcome:** the owner creates an item and sees it attributed
- **Serves:** F-001, UN-001
- **Why:** nothing is recordable until the create path exists
- **Usable when done:** the owner records one item unaided
- **Depends on:** none
- **Tests:** integration test over the create path
- **Acceptance evidence:** recorded run of an owner creating an item
"""


INFRASTRUCTURE_BRIEF = VALID_BRIEF.replace(
    "- **Outcome:** the owner creates an item and sees it attributed",
    "- **Kind:** infrastructure\n"
    "- **Outcome:** the item store exists and is migrated\n"
    "- **Unlocks:** F-001",
)


def run(command: list[str], cwd: Path, *, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=AUTHOR_ENV,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def ctl(repo: Path, command: str, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(RUNTIME), "--repo", str(repo), "--json", command, *arguments],
        repo,
        check=check,
    )


def write_governance_docs(repo: Path, *, concept: bool = False) -> None:
    """Write a governance repository that validates clean.

    With `concept=True` the need authority moves to a CON and the FSD drops its baseline,
    because a CON alongside a 'User needs baseline' is duplicate authority.
    """
    docs = repo / "docs"
    docs.mkdir(exist_ok=True)
    (repo / "DECISIONS.md").write_text("| D-001 | accepted |\n", encoding="utf-8")
    (docs / "repo-FSD.md").write_text(CON_FSD if concept else VALID_FSD, encoding="utf-8")
    (docs / "repo-TSD.md").write_text(VALID_TSD, encoding="utf-8")
    if concept:
        (docs / "repo-CON.md").write_text(WARNING_CON, encoding="utf-8")
    for name in ["AGENTS.md", "CLAUDE.md", "design.md", "Implementations.md", "README.md"]:
        (repo / name).write_text(f"# {name}\n", encoding="utf-8")
    waves = docs / "waves"
    waves.mkdir(exist_ok=True)
    (waves / "README.md").write_text(f"# Waves\n\nLegend: {LEGEND}\n", encoding="utf-8")
    (waves / "PR-CHECKLIST.md").write_text("# Checklist\n", encoding="utf-8")
    (waves / "wave-1-create-item.md").write_text(VALID_BRIEF, encoding="utf-8")


class GovernanceRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="governance-runtime-")
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        run(["git", "init", "-q"], self.repo)
        (self.repo / "app.txt").write_text("base\n", encoding="utf-8")
        run(["git", "add", "app.txt"], self.repo)
        run(["git", "commit", "-q", "-m", "test: initialize fixture"], self.repo)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def common_state(self, repo: Path | None = None) -> Path:
        repo = repo or self.repo
        raw = run(["git", "rev-parse", "--git-common-dir"], repo).stdout.strip()
        path = Path(raw)
        if not path.is_absolute():
            path = repo / path
        return path.resolve() / "governance"

    def commit_all(self, message: str, repo: Path | None = None) -> None:
        repo = repo or self.repo
        run(["git", "add", "-A"], repo)
        run(["git", "commit", "-q", "-m", message], repo)

    def add_sibling(self, name: str = "agent-worktree", branch: str = "agent") -> Path:
        sibling = Path(self.temp.name) / name
        run(["git", "branch", branch], self.repo)
        run(["git", "worktree", "add", "-q", str(sibling), branch], self.repo)
        return sibling

    def resolutions(self) -> list[dict]:
        return json.loads((self.common_state() / "resolutions.json").read_text(encoding="utf-8"))["records"]

    def run_state(self) -> dict:
        return json.loads((self.common_state() / "run-state.json").read_text(encoding="utf-8"))

    # --- baseline behaviour -------------------------------------------------

    def test_discover_creates_shared_state(self) -> None:
        result = ctl(self.repo, "discover")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["worktree_count"], 1)
        self.assertTrue((self.repo / ".governance" / "config.json").is_file())
        self.assertTrue((self.common_state() / "registry.json").is_file())
        self.assertTrue((self.common_state() / "discovery.json").is_file())
        self.assertTrue((self.common_state() / "run-state.json").is_file())
        self.assertTrue((self.common_state() / "canonical.json").is_file())
        config = json.loads((self.repo / ".governance" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["schema_version"], 3)
        self.assertNotIn("canonical_worktree", config)
        self.assertNotIn(str(self.repo), json.dumps(config))

    def test_overlap_snapshot_resolution_and_close(self) -> None:
        sibling = self.add_sibling()
        (self.repo / "app.txt").write_text("canonical change\n", encoding="utf-8")
        (sibling / "app.txt").write_text("agent change\n", encoding="utf-8")
        (sibling / ".env").write_text("SECRET_VALUE=not-for-output\n", encoding="utf-8")

        ctl(self.repo, "discover")
        reconcile = ctl(self.repo, "reconcile", check=False)
        self.assertEqual(reconcile.returncode, 4)
        payload = json.loads(reconcile.stdout)
        self.assertGreaterEqual(payload["unresolved"], 1)

        overlaps = [item for item in self.resolutions() if item["kind"] == "overlapping-paths"]
        self.assertEqual(len(overlaps), 1)
        self.assertIn("app.txt", overlaps[0]["paths"])

        manifests = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (self.common_state() / "snapshots").glob("*.json")
        ]
        sibling_manifest = next(item for item in manifests if item["worktree"] == str(sibling))
        self.assertIn(".env", sibling_manifest["untracked_excluded_sensitive"])
        self.assertNotIn(".env", sibling_manifest["untracked_included"])

        for record in self.resolutions():
            ctl(
                self.repo,
                "resolve",
                "--id",
                record["id"],
                "--choice",
                "keep-canonical",
                "--note",
                "Fixture owner selected canonical content after snapshot review.",
            )
        validate = json.loads(ctl(self.repo, "validate").stdout)
        self.assertTrue(validate["valid"])
        self.assertEqual(validate["unresolved_resolution_count"], 0)
        closed = json.loads(ctl(self.repo, "close-stage", "--owner-approved").stdout)
        self.assertTrue(closed["closed"])

    def test_validation_detects_stale_canonical_head(self) -> None:
        ctl(self.repo, "discover")
        (self.repo / "later.txt").write_text("later\n", encoding="utf-8")
        self.commit_all("test: advance canonical head")
        result = ctl(self.repo, "validate", check=False)
        self.assertEqual(result.returncode, 3)
        payload = json.loads(result.stdout)
        self.assertIn("Canonical HEAD changed after the last inventory", payload["errors"])

    def test_governance_validation_runs_spec_and_plan_chain(self) -> None:
        ctl(self.repo, "discover")
        write_governance_docs(self.repo)
        result = ctl(self.repo, "validate")
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"], payload["errors"])

        # Break the specification only: governancectl must surface the spec validator.
        (self.repo / "docs" / "repo-TSD.md").write_text(
            VALID_TSD.replace("## Product deltas surfaced\nNone\n", ""), encoding="utf-8"
        )
        result = ctl(self.repo, "validate", check=False)
        self.assertEqual(result.returncode, 3)
        errors = json.loads(result.stdout)["errors"]
        self.assertTrue(any(error.startswith("Specification:") for error in errors), errors)
        self.assertTrue(any("Product deltas surfaced" in error for error in errors), errors)
        (self.repo / "docs" / "repo-TSD.md").write_text(VALID_TSD, encoding="utf-8")

        # Break the plan only: governancectl must surface the planning validator.
        (self.repo / "docs" / "waves" / "wave-1-create-item.md").write_text(
            "# Wave 1 — Create item\n\nReferences: D-001, F-001, T-001\n", encoding="utf-8"
        )
        result = ctl(self.repo, "validate", check=False)
        self.assertEqual(result.returncode, 3)
        errors = json.loads(result.stdout)["errors"]
        self.assertTrue(any(error.startswith("Planning:") for error in errors), errors)

    def test_validation_relays_backward_explainability_breaks(self) -> None:
        ctl(self.repo, "discover")
        write_governance_docs(self.repo)
        # A T-ID that realizes only a decision reaches no F, so the chain to a user breaks.
        (self.repo / "docs" / "repo-TSD.md").write_text(
            VALID_TSD.replace("- **Realizes:** F-001, D-001", "- **Realizes:** D-001"),
            encoding="utf-8",
        )
        result = ctl(self.repo, "validate", check=False)
        self.assertEqual(result.returncode, 3)
        errors = json.loads(result.stdout)["errors"]
        self.assertTrue(any(error.startswith("Trace:") for error in errors), errors)
        self.assertTrue(any("T-001" in error and "realizes no F-ID" in error for error in errors), errors)

    def test_sibling_validator_warnings_are_relayed_without_becoming_errors(self) -> None:
        ctl(self.repo, "discover")
        # The CON accepts C-001 on an assumption: a structural warning, not a defect.
        write_governance_docs(self.repo, concept=True)
        result = ctl(self.repo, "validate", check=False)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, payload)
        self.assertTrue(payload["valid"], payload["errors"])
        self.assertEqual(payload["errors"], [])
        relayed = [item for item in payload["warnings"] if item.startswith("Specification: ")]
        self.assertTrue(relayed, payload["warnings"])
        self.assertTrue(
            any("C-001" in item and "assumption" in item for item in relayed), payload["warnings"]
        )

    def test_planning_warnings_are_relayed_without_becoming_errors(self) -> None:
        ctl(self.repo, "discover")
        write_governance_docs(self.repo)
        # A wave built only of infrastructure slices is valid but demonstrates no outcome.
        (self.repo / "docs" / "waves" / "wave-1-create-item.md").write_text(
            INFRASTRUCTURE_BRIEF, encoding="utf-8"
        )
        result = ctl(self.repo, "validate", check=False)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, payload)
        self.assertTrue(payload["valid"], payload["errors"])
        self.assertEqual(payload["errors"], [])
        relayed = [item for item in payload["warnings"] if item.startswith("Planning: ")]
        self.assertTrue(relayed, payload["warnings"])
        self.assertTrue(any("only infrastructure slices" in item for item in relayed), relayed)

    def test_non_overlapping_dirty_worktree_requires_disposition(self) -> None:
        sibling = self.add_sibling()
        (sibling / "agent-only.txt").write_text("unfinished\n", encoding="utf-8")
        ctl(self.repo, "discover")
        reconcile = ctl(self.repo, "reconcile", check=False)
        self.assertEqual(reconcile.returncode, 4)
        variants = [item for item in self.resolutions() if item["kind"] == "unfinished-variant"]
        self.assertEqual(len(variants), 1)
        self.assertIn("agent-only.txt", variants[0]["paths"])
        close = ctl(self.repo, "close-stage", "--owner-approved", check=False)
        self.assertEqual(close.returncode, 4)

    def test_hook_installation_is_idempotent_and_gates_destructive_git(self) -> None:
        ctl(self.repo, "discover")
        ctl(self.repo, "install-hooks")
        ctl(self.repo, "install-hooks")
        cursor_config = json.loads((self.repo / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
        claude_config = json.loads((self.repo / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(len(cursor_config["hooks"]["preToolUse"]), 1)
        self.assertEqual(len(claude_config["hooks"]["PreToolUse"]), 1)
        self.assertNotIn("failClosed", cursor_config["hooks"]["stop"][0])
        self.assertNotIn("matcher", cursor_config["hooks"]["preToolUse"][0])

        cursor_hook = self.repo / ".cursor" / "hooks" / "governance-hook.py"
        cursor = run(
            [sys.executable, str(cursor_hook), "pre-tool-use"],
            self.repo,
            input_text=json.dumps({"command": "git reset --hard HEAD"}),
        )
        self.assertEqual(json.loads(cursor.stdout)["permission"], "ask")

        claude_hook = self.repo / ".claude" / "hooks" / "governance-hook.py"
        claude = run(
            [sys.executable, str(claude_hook), "pre-tool-use"],
            self.repo,
            input_text=json.dumps({"tool_input": {"command": "git reset --hard HEAD"}}),
        )
        self.assertEqual(
            json.loads(claude.stdout)["hookSpecificOutput"]["permissionDecision"],
            "ask",
        )

    def test_hook_upgrade_replaces_stale_governance_entry(self) -> None:
        ctl(self.repo, "discover")
        ctl(self.repo, "install-hooks")
        hooks_path = self.repo / ".cursor" / "hooks.json"
        stale = json.loads(hooks_path.read_text(encoding="utf-8"))
        # Simulate an entry written by an earlier suite version plus a foreign hook.
        stale["hooks"]["stop"][0]["failClosed"] = True
        stale["hooks"]["stop"].append({"command": "python3 .cursor/hooks/other.py stop"})
        hooks_path.write_text(json.dumps(stale), encoding="utf-8")
        ctl(self.repo, "install-hooks")
        upgraded = json.loads(hooks_path.read_text(encoding="utf-8"))
        governance = [item for item in upgraded["hooks"]["stop"] if "governance-hook.py" in item["command"]]
        self.assertEqual(len(governance), 1)
        self.assertNotIn("failClosed", governance[0])
        self.assertEqual(len(upgraded["hooks"]["stop"]), 2)

    # --- regressions from the vetting probe ---------------------------------

    def test_committed_config_is_valid_in_a_fresh_clone(self) -> None:
        ctl(self.repo, "discover")
        self.commit_all("chore: enable governance")
        clone = Path(self.temp.name) / "clone"
        run(["git", "clone", "-q", str(self.repo), str(clone)], Path(self.temp.name))
        doctor = json.loads(ctl(clone, "doctor").stdout)
        self.assertTrue(doctor["configured"])
        self.assertEqual(doctor["config_schema"], 3)
        status = json.loads(ctl(clone, "status").stdout)
        self.assertTrue(status["configured"])
        discover = json.loads(ctl(clone, "discover").stdout)
        self.assertEqual(discover["worktree_count"], 1)
        canonical = json.loads((self.common_state(clone) / "canonical.json").read_text(encoding="utf-8"))
        self.assertEqual(Path(canonical["canonical_worktree"]).resolve(), clone.resolve())

    def test_legacy_v2_config_is_migrated_in_place(self) -> None:
        legacy = {
            "schema_version": 2,
            "suite_version": "2.0.0",
            "repository_id": "path-derived-hash",
            "enabled": True,
            "hooks_enabled": False,
            "project_slug": "custom-slug",
            "canonical_worktree": str(self.repo),
            "canonical_branch": "main",
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        (self.repo / ".governance").mkdir()
        (self.repo / ".governance" / "config.json").write_text(json.dumps(legacy), encoding="utf-8")
        doctor = json.loads(ctl(self.repo, "doctor").stdout)
        self.assertEqual(doctor["config_schema"], 3)
        migrated = json.loads((self.repo / ".governance" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(migrated["project_slug"], "custom-slug")
        self.assertNotIn("canonical_worktree", migrated)
        self.assertEqual(Path(doctor["canonical_worktree"]).resolve(), self.repo.resolve())

    def test_stop_hook_warns_but_never_denies(self) -> None:
        ctl(self.repo, "discover")
        ctl(self.repo, "install-hooks")
        (self.repo / "work.txt").write_text("work\n", encoding="utf-8")
        self.commit_all("feat: work")

        neutral = json.loads(ctl(self.repo, "hook", "stop", check=False).stdout)
        self.assertEqual(neutral["permission"], "allow")
        # HEAD drift is self-healed rather than reported.
        self.assertNotIn("Canonical HEAD changed", neutral["reason"])

        (self.repo / "AGENTS.md").write_text("# Guide\n\nRun `<install-command>` first.\n", encoding="utf-8")
        for name in ["CLAUDE.md", "design.md", "DECISIONS.md", "Implementations.md", "README.md"]:
            (self.repo / name).write_text(f"# {name}\n", encoding="utf-8")
        (self.repo / "docs" / "waves").mkdir(parents=True)
        (self.repo / "docs" / "waves" / "README.md").write_text(f"# Waves\n\nLegend: {LEGEND}\n", encoding="utf-8")

        claude_hook = self.repo / ".claude" / "hooks" / "governance-hook.py"
        warned = json.loads(run([sys.executable, str(claude_hook), "stop"], self.repo, input_text="{}").stdout)
        self.assertNotIn("decision", warned)
        self.assertIn("governance-warning", warned["systemMessage"])
        self.assertIn("<install-command>", warned["systemMessage"])

        silent = json.loads(
            run([sys.executable, str(claude_hook), "stop"], self.repo, input_text=json.dumps({"stop_hook_active": True})).stdout
        )
        self.assertEqual(silent, {})

        cursor_hook = self.repo / ".cursor" / "hooks" / "governance-hook.py"
        cursor = json.loads(run([sys.executable, str(cursor_hook), "stop"], self.repo, input_text="{}").stdout)
        self.assertIn("governance-warning", cursor["followup_message"])

    def test_committed_sibling_branch_requires_disposition(self) -> None:
        sibling = self.add_sibling()
        (sibling / "agent.txt").write_text("committed agent work\n", encoding="utf-8")
        self.commit_all("agent: work", sibling)
        ctl(self.repo, "discover")
        reconcile = ctl(self.repo, "reconcile", check=False)
        self.assertEqual(reconcile.returncode, 4)
        divergent = [item for item in self.resolutions() if item["kind"] == "divergent-base"]
        self.assertEqual(len(divergent), 1)
        self.assertEqual(divergent[0]["ahead"], 1)
        self.assertEqual(divergent[0]["snapshots"], [])
        self.assertEqual(divergent[0]["status"], "needs-owner")

    def test_adopt_stays_pending_until_variant_is_gone(self) -> None:
        sibling = self.add_sibling()
        (sibling / "agent-only.txt").write_text("unfinished\n", encoding="utf-8")
        ctl(self.repo, "discover")
        ctl(self.repo, "reconcile", check=False)
        record = self.resolutions()[0]
        resolved = json.loads(
            ctl(self.repo, "resolve", "--id", record["id"], "--choice", "adopt", "--note", "Owner will adopt.").stdout
        )
        self.assertEqual(resolved["status"], "pending")
        close = ctl(self.repo, "close-stage", "--owner-approved", check=False)
        self.assertEqual(close.returncode, 4)

        (sibling / "agent-only.txt").unlink()
        closed = json.loads(ctl(self.repo, "close-stage", "--owner-approved").stdout)
        self.assertTrue(closed["closed"])
        carried = next(item for item in self.resolutions() if item["id"] == record["id"])
        self.assertEqual(carried["status"], "resolved")
        self.assertIn("variant no longer present", carried["note"])

    def test_notes_and_phase_survive_rediscovery(self) -> None:
        ctl(self.repo, "discover")
        note = json.loads(
            ctl(
                self.repo, "note", "--kind", "observation", "--provenance", "code",
                "--evidence", "app.txt", "--text", "Fixture stores base content",
            ).stdout
        )
        self.assertEqual(note["id"], "N-001")
        missing_evidence = ctl(self.repo, "note", "--kind", "observation", "--text", "no evidence", check=False)
        self.assertEqual(missing_evidence.returncode, 2)
        ctl(self.repo, "phase", "planning", "--next-action", "Author wave briefs")
        ctl(self.repo, "discover")
        ctl(self.repo, "reconcile")
        packet = json.loads((self.common_state() / "discovery.json").read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in packet["observations"]], ["N-001"])
        state = self.run_state()
        self.assertEqual(state["phase"], "planning")
        self.assertEqual(state["next_action"], "Author wave briefs")

    def test_evidence_class_is_stored_and_merged_into_the_packet(self) -> None:
        ctl(self.repo, "discover")
        # An explicit class outranks the derived default, which here would be 'assumption'.
        explicit = json.loads(
            ctl(
                self.repo, "note", "--kind", "needs-owner", "--provenance", "owner",
                "--evidence-class", "observed-behavior",
                "--text", "Owner confirmed the create step is performed by hand today",
            ).stdout
        )
        self.assertEqual(explicit["evidence_class"], "observed-behavior")
        # Omitting the flag derives a class from kind and provenance; it is never dropped.
        derived_from_code = json.loads(
            ctl(
                self.repo, "note", "--kind", "observation", "--provenance", "code",
                "--evidence", "app.txt", "--text", "Fixture stores base content",
            ).stdout
        )
        self.assertEqual(derived_from_code["evidence_class"], "observed-behavior")
        derived_from_kind = json.loads(
            ctl(self.repo, "note", "--kind", "hypothesis", "--text", "The store is append-only").stdout
        )
        self.assertEqual(derived_from_kind["evidence_class"], "hypothesis")

        stored = json.loads((self.common_state() / "discovery-notes.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {item["id"]: item.get("evidence_class") for item in stored["notes"]},
            {"N-001": "observed-behavior", "N-002": "observed-behavior", "N-003": "hypothesis"},
        )

        # The class travels unchanged into the merged packet and survives rediscovery.
        ctl(self.repo, "discover")
        packet = json.loads((self.common_state() / "discovery.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [(item["id"], item.get("evidence_class")) for item in packet["needs_owner"]],
            [("N-001", "observed-behavior")],
        )
        self.assertEqual(
            [(item["id"], item.get("evidence_class")) for item in packet["observations"]],
            [("N-002", "observed-behavior")],
        )
        self.assertEqual(
            [(item["id"], item.get("evidence_class")) for item in packet["hypotheses"]],
            [("N-003", "hypothesis")],
        )

        off_enum = ctl(
            self.repo, "note", "--kind", "observation", "--provenance", "code",
            "--evidence", "app.txt", "--evidence-class", "rumour",
            "--text", "Off-enum classes must not reach the packet",
            check=False,
        )
        # argparse rejects the choice before command_note runs, so the diagnostic reaches
        # stderr rather than the JSON payload; either path exits EXIT_USAGE (2).
        self.assertEqual(off_enum.returncode, 2, off_enum.stderr)
        self.assertIn("rumour", off_enum.stdout + off_enum.stderr)
        unchanged = json.loads((self.common_state() / "discovery-notes.json").read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in unchanged["notes"]], ["N-001", "N-002", "N-003"])

    def test_lazy_template_fill_is_rejected(self) -> None:
        ctl(self.repo, "discover")
        write_governance_docs(self.repo)
        (self.repo / "AGENTS.md").write_text(
            "# Demo Agent Guide\n\n```bash\n<install-command>\n<test-command>\n```\n", encoding="utf-8"
        )
        (self.repo / "DECISIONS.md").write_text("| D-001 | <YYYY-MM-DD> | accepted |\n", encoding="utf-8")
        result = ctl(self.repo, "validate", check=False)
        self.assertEqual(result.returncode, 3)
        errors = json.loads(result.stdout)["errors"]
        self.assertTrue(any("AGENTS.md" in error and "<install-command>" in error for error in errors), errors)
        self.assertTrue(any("DECISIONS.md" in error and "<YYYY-MM-DD>" in error for error in errors), errors)

    def test_set_canonical_switches_authoritative_worktree(self) -> None:
        sibling = self.add_sibling()
        ctl(self.repo, "discover")
        result = json.loads(ctl(self.repo, "set-canonical", "--path", str(sibling)).stdout)
        self.assertEqual(Path(result["canonical_worktree"]).resolve(), sibling.resolve())
        status = json.loads(ctl(self.repo, "status").stdout)
        self.assertEqual(Path(status["registry_summary"]["canonical_worktree"]).resolve(), sibling.resolve())
        outside = ctl(self.repo, "set-canonical", "--path", self.temp.name, check=False)
        self.assertEqual(outside.returncode, 2)


if __name__ == "__main__":
    unittest.main()
