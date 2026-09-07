#!/usr/bin/env python3
"""Run deterministic suite checks without installing or upgrading anything."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-only", action="store_true", help="Skip renderer tests (which require npm ci, LibreOffice and Poppler)")
    args = parser.parse_args()
    commands = [
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", f"{skill}/tests", "-v"]
        for skill in ("governance-system", "spec-chain", "plan-waves-slices")
    ]
    commands += [[sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                 [sys.executable, "-B", "governance-system/scripts/validate_suite.py"]]
    if not args.python_only:
        commands.append(["npm", "--prefix", "spec-chain", "test"])
    failed = False
    for command in commands:
        print("Running: " + " ".join(command), flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
            failed |= result.returncode != 0
        except OSError as exc:
            print(f"Cannot run check: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
