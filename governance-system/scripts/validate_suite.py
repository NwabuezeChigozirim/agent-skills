#!/usr/bin/env python3
"""Validate the canonical governance skill suite structure."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
import json
import os
from pathlib import Path
import re
import subprocess


LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

SKILLS = ["governance-system", "plan-waves-slices", "spec-chain"]

# Files whose absence makes the suite structurally invalid, per skill. The need-first
# philosophy is stated once in spec-chain and cited by the other two packages.
REQUIRED_FILES: dict[str, list[str]] = {
    "spec-chain": ["references/need-first.md", "scripts/specification_graph.py"],
    "governance-system": ["scripts/engineering_policy.py", "scripts/artifact_contracts.py", "scripts/stage_contracts.py"],
    "plan-waves-slices": ["scripts/planning_graph.py"],
}


def validate_skill(root: Path, required_files: Iterable[str] = ()) -> list[str]:
    errors: list[str] = []
    for relative in required_files:
        required = root / relative
        if not required.is_file():
            errors.append(f"{root}: missing {relative}")
        elif not required.read_text(encoding="utf-8").strip():
            errors.append(f"{root}: {relative} is empty")
    skill_file = root / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"Missing {skill_file}")
        return errors
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 500:
        errors.append(f"{skill_file}: SKILL.md exceeds 500 lines ({len(lines)})")
    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append(f"{skill_file}: missing YAML frontmatter")
    else:
        frontmatter = match.group(1)
        name = re.search(r"^name:\s*([a-z0-9-]+)\s*$", frontmatter, re.MULTILINE)
        if not name:
            errors.append(f"{skill_file}: invalid or missing name")
        if not re.search(r"^description:\s*[>|-]?", frontmatter, re.MULTILINE):
            errors.append(f"{skill_file}: missing description")
    for target in LINK_RE.findall(text):
        if "://" in target or target.startswith("#"):
            continue
        clean = target.split("#", 1)[0]
        if not (root / clean).exists():
            errors.append(f"{skill_file}: broken reference {target}")
    if (root / "templates").exists():
        errors.append(f"{root}: legacy templates/ directory remains; use assets/")
    for directory in ["references", "assets", "evals"]:
        if not (root / directory).is_dir():
            errors.append(f"{root}: missing {directory}/")
    return errors


def validate_evals(root: Path) -> list[str]:
    """Parse a skill's eval file and resolve the philosophy pointer it declares."""
    path = root / "evals" / "evals.json"
    if not path.is_file():
        return [f"{root}: missing evals/evals.json"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [f"{path}: invalid JSON ({exc})"]
    errors: list[str] = []
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append(f"{path}: no eval cases")
    philosophy = payload.get("philosophy")
    if not philosophy:
        errors.append(f"{path}: missing philosophy pointer")
    elif not (root / philosophy).is_file():
        errors.append(f"{path}: philosophy pointer does not resolve: {philosophy}")
    return errors


def validate_symlinks(canonical_root: Path) -> list[str]:
    errors: list[str] = []
    home = Path.home()
    for skill in SKILLS:
        expected = (canonical_root / skill).resolve()
        for host in [home / ".claude" / "skills", home / ".cursor" / "skills"]:
            active = host / skill
            if not active.is_symlink():
                errors.append(f"{active}: expected symlink to canonical skill")
                continue
            if active.resolve() != expected:
                errors.append(f"{active}: resolves to {active.resolve()}, expected {expected}")
    return errors


def validate_projections(canonical_root: Path, sync_script: str | None = None) -> list[str]:
    """Delegate projection parity to sync-skills.sh --check and relay its verdict."""
    script = (
        Path(sync_script).expanduser()
        if sync_script
        else canonical_root.parent / "scripts" / "sync-skills.sh"
    )
    if not script.is_file():
        return [f"{script}: sync-skills.sh not found; pass --sync-script PATH"]
    if not os.access(script, os.X_OK):
        return [f"{script}: sync-skills.sh is not executable; pass --sync-script PATH"]
    try:
        completed = subprocess.run(
            [str(script), "--check"],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return [f"{script} --check: timed out after 120s"]
    except OSError as exc:
        return [f"{script} --check: could not run ({exc})"]
    if completed.returncode == 0:
        return []
    headline = (
        "projection parity failed"
        if completed.returncode == 3
        else f"could not complete (exit {completed.returncode})"
    )
    errors = [f"{script} --check: {headline}"]
    output = completed.stdout + completed.stderr
    errors.extend(line.strip() for line in output.splitlines() if line.strip())
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Canonical agent-skills directory",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--check-symlinks",
        action="store_true",
        help="Also require ~/.claude/skills and ~/.cursor/skills entries to symlink to --root "
        "(host-specific installation layout; off by default)",
    )
    parser.add_argument(
        "--check-projections",
        action="store_true",
        help="Also require sync-skills.sh --check to pass, so the generated cursor/skills and "
        "claude/skills copies match the canonical tree (backup-repository layout; off by default)",
    )
    parser.add_argument(
        "--sync-script",
        help="sync-skills.sh to delegate --check-projections to "
        "(default: <root>/../scripts/sync-skills.sh; the script checks its own repository)",
    )
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    errors: list[str] = []
    for name in SKILLS:
        errors.extend(validate_skill(root / name, REQUIRED_FILES.get(name, [])))
        errors.extend(validate_evals(root / name))
    if args.check_symlinks:
        errors.extend(validate_symlinks(root))
    if args.check_projections:
        errors.extend(validate_projections(root, args.sync_script))
    result = {"valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("valid" if not errors else "\n".join(errors))
    return 0 if not errors else 3


if __name__ == "__main__":
    raise SystemExit(main())
