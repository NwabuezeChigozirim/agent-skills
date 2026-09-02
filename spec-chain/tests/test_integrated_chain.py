#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures import con, fsd, tsd  # noqa: E402

SKILLS = Path(__file__).resolve().parents[2]
SPEC_VALIDATOR = SKILLS / "spec-chain" / "scripts" / "validate_spec.py"
TRACER = SKILLS / "spec-chain" / "scripts" / "trace_chain.py"
PLAN_VALIDATOR = SKILLS / "plan-waves-slices" / "scripts" / "validate_plan.py"
LEGEND = "⏸ gated · 🟡 approved & in progress · ✅ done & signed off"

BRIEF = """# Wave 1 — Shortlist by proximity

## Why this wave

Retires the riskiest assumption: that distance text is enough for hirers to shortlist.

## References

- Decisions: D-001
- User needs: UN-001
- Behaviour: F-001
- Technical design: T-001

## Exit criterion

> A hirer shortlists a supplier using distance and area without a site visit.

## Slices

### W1-S1 — Distance in results

- **Outcome:** hirer sees distance and area on each result
- **Serves:** F-001, UN-001
- **Why:** proximity is the shortlisting decision
- **Usable when done:** shortlist from results without calling suppliers
- **Concrete work:** proximity computation, results field
- **Depends on:** none
- **Tests:** unit for computation; flow for results
- **Acceptance evidence:** recorded shortlist walkthrough
"""


# Placeholders in the shipped templates whose resolution must satisfy an ID, enum or
# path rule. Everything else resolves to prose the validators do not inspect.
ASSET_IDS = {
    "<project-slug>": "sample",
    "<Project Name>": "Sample",
    "<PREFIX>": "SMP",
    "<class>": "observed-behavior",
    "<accepted / hypothesis / rejected / deferred>": "accepted",
    "<high / medium / low, and what would raise it>": "high",
    "<capability / expose-information / remove-step / default-change / simplification / "
    "rule-change / representation-change / wording / do-nothing / defer>": "capability",
    "<page / endpoint / command / job / event / integration / admin / journey>": "endpoint",
    "<kind>": "endpoint",
    "<CON path, or \u201cconcept gate skipped \u2014 see User needs baseline\u201d>": "docs/sample-CON.md",
    "<CON path>": "docs/sample-CON.md",
    "<D-ID or named ratified source>": "D-001",
    "<D-IDs and O-IDs>": "D-001",
    "<Canonical O-ID references; each with what it blocks.>": "No blocking O-IDs remain.",
    "<UN-ID or none>": "UN-001",
    "<UN-IDs, if any>": "UN-001",
    "<UN/C IDs at risk if false>": "UN-001",
    "<UN-IDs and accepted C-IDs>": "UN-001, C-001",
    "<IDs>": "UN-001",
    "<F-IDs in order and what each yields>": "F-001 yields the recorded item",
    "<F-IDs, D-IDs and external behavior>": "F-001, D-001",
    "<F-IDs and D-IDs>": "F-001, D-001",
    "<F-IDs, and UN-IDs where helpful>": "F-001, UN-001",
    "<F-ID this makes possible>": "F-001",
    "<F-IDs>": "F-001",
    "<F-ID>": "F-001",
    "<T-IDs, services and platform constraints>": "T-001",
    "<T-IDs and TSD sections>": "T-001",
    "<F-IDs and FSD sections>": "F-001",
    "<D-IDs>": "D-001",
    "<UN-IDs>": "UN-001",
    "<RK-IDs or none>": "none",
    "<RK-IDs and non-blocking O-IDs>": "none",
    "<YYYY-MM-DD>": "2026-09-02",
    "<date>": "2026-09-02",
    "<URL or authoritative document>": "https://example.com/docs",
    "<N>": "1",
    "<Role>": "Owner",
    "<role>": "owner",
    "<roles>": "UR-001",
    "<Need name>": "Record a unit of work",
    "<Response name>": "Record the item explicitly",
    "<Name>": "Record item",
    "<Journey>": "Record and confirm",
    "<Capability>": "Recording",
    "<level>": "medium",
}

# With a CON present, the FSD's optional baseline section is duplicate need authority;
# the template itself instructs the author to replace its body.
BASELINE_REPLACED = (
    "## User needs baseline\n\nNot applicable \u2014 needs are defined in docs/sample-CON.md.\n\n"
)


def fill(template: str, *, drop_baseline: bool = False) -> str:
    """Resolve a shipped template the way an author would, so it can be validated."""
    if drop_baseline:
        template = re.sub(
            r"^## User needs baseline\n.*?(?=^## Scope baseline$)",
            BASELINE_REPLACED,
            template,
            flags=re.DOTALL | re.MULTILINE,
        )
    for placeholder, value in ASSET_IDS.items():
        template = template.replace(placeholder, value)
    return re.sub(r"(?<!\w)<(?!\w+://)([A-Za-z][^<>\n@]{0,120})>", "resolved", template)


def run(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *arguments, "--json"], capture_output=True, text=True, check=False
    )


class IntegratedChainTests(unittest.TestCase):
    def test_valid_chain_feeds_wave_traceability(self) -> None:
        with tempfile.TemporaryDirectory(prefix="integrated-spec-chain-") as temporary:
            repo = Path(temporary)
            waves = repo / "docs" / "waves"
            waves.mkdir(parents=True)
            (repo / "DECISIONS.md").write_text("| D-001 | accepted |\n", encoding="utf-8")
            (repo / "docs" / "sample-CON.md").write_text(con(), encoding="utf-8")
            (repo / "docs" / "sample-FSD.md").write_text(fsd(), encoding="utf-8")
            (repo / "docs" / "sample-TSD.md").write_text(tsd(), encoding="utf-8")
            (waves / "README.md").write_text(f"# Waves\n\nLegend: {LEGEND}\n", encoding="utf-8")
            (waves / "PR-CHECKLIST.md").write_text("# Checklist\n", encoding="utf-8")
            (waves / "wave-1-shortlist.md").write_text(BRIEF, encoding="utf-8")

            spec = run(SPEC_VALIDATOR, "--repo", str(repo), "--project", "sample", "--mode", "governance")
            chain = run(TRACER, "--repo", str(repo), "--project", "sample")
            plan = run(PLAN_VALIDATOR, "--repo", str(repo), "--mode", "governance")
            self.assertEqual(spec.returncode, 0, spec.stdout)
            self.assertEqual(chain.returncode, 0, chain.stdout)
            self.assertEqual(plan.returncode, 0, plan.stdout)
            self.assertTrue(json.loads(spec.stdout)["valid"])
            self.assertTrue(json.loads(chain.stdout)["valid"])
            self.assertTrue(json.loads(plan.stdout)["valid"])

    def test_shipped_templates_validate_once_filled(self) -> None:
        # Couples the shipped assets to the validators that grade them: a template that
        # drops a required label, an inventory row or a traceability row fails here
        # rather than in the first project that fills it in.
        spec_assets = SKILLS / "spec-chain" / "assets"
        brief_asset = SKILLS / "plan-waves-slices" / "assets" / "wave-brief.md"
        with tempfile.TemporaryDirectory(prefix="integrated-assets-") as temporary:
            repo = Path(temporary)
            waves = repo / "docs" / "waves"
            waves.mkdir(parents=True)
            (repo / "DECISIONS.md").write_text(
                "| D-001 | accepted |\n| O-001 | open |\n", encoding="utf-8"
            )
            for kind in ["CON", "FSD", "TSD"]:
                (repo / "docs" / f"sample-{kind}.md").write_text(
                    fill(
                        (spec_assets / f"{kind}.md").read_text(encoding="utf-8"),
                        drop_baseline=(kind == "FSD"),
                    ),
                    encoding="utf-8",
                )
            (waves / "README.md").write_text(f"# Waves\n\nLegend: {LEGEND}\n", encoding="utf-8")
            (waves / "PR-CHECKLIST.md").write_text("# Checklist\n", encoding="utf-8")
            (waves / "wave-1-recording.md").write_text(
                fill(brief_asset.read_text(encoding="utf-8")), encoding="utf-8"
            )

            spec = run(SPEC_VALIDATOR, "--repo", str(repo), "--project", "sample", "--mode", "governance")
            chain = run(TRACER, "--repo", str(repo), "--project", "sample")
            plan = run(PLAN_VALIDATOR, "--repo", str(repo), "--mode", "governance")
            self.assertEqual(spec.returncode, 0, spec.stdout)
            self.assertEqual(chain.returncode, 0, chain.stdout)
            self.assertEqual(plan.returncode, 0, plan.stdout)


if __name__ == "__main__":
    unittest.main()
