#!/usr/bin/env python3
"""Cursor project-hook adapter for governancectl."""

from __future__ import annotations

import json
from pathlib import Path
import sys


sys.dont_write_bytecode = True
EVENT = sys.argv[1] if len(sys.argv) > 1 else ""
# Installed wrappers load their sibling helper; source wrappers load hooks' helper.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE if (HERE / "hook_support.py").is_file() else HERE.parent))
try:
    import hook_support as support
except (ImportError, OSError, SyntaxError):
    support = None


def repository_root() -> Path | None:
    return support.repository_root(__file__) if support else Path(__file__).resolve().parents[2]


def runtime_path() -> Path | None:
    return support.runtime_path() if support else None


def neutral_decision(payload: bytes) -> dict[str, str]:
    if support:
        return support.neutral(payload, EVENT, repository_root, runtime_path)
    # A missing helper cannot silently disable an installed pre-action guard.
    try:
        config = repository_root() / ".governance/config.json"
        if not config.exists() and not config.is_symlink():
            return {"permission": "allow", "reason": "governance-disabled"}
        value = json.loads(config.read_text(encoding="utf-8"))
        if (isinstance(value, dict) and not config.is_symlink() and not config.parent.is_symlink()
                and all(type(value[k]) is bool for k in ("enabled", "hooks_enabled") if k in value)
                and (not value.get("enabled") or not value.get("hooks_enabled"))):
            return {"permission": "allow", "reason": "governance-disabled"}
        parsed = json.loads(payload.decode("utf-8"))
        if EVENT == "stop" and isinstance(parsed, dict) and parsed.get("stop_hook_active") is True:
            return {"permission": "allow", "reason": "governance-stop-hook-active"}
    except (OSError, ValueError, TypeError):
        pass
    return {"permission": "deny" if EVENT == "pre-tool-use" else "allow",
            "reason": "governance-warning: adapter helper unavailable; repair hook installation"}

def translate(decision: dict[str, str]) -> dict[str, str]:
    permission, reason = decision["permission"], decision["reason"]
    if EVENT == "pre-tool-use" and permission != "allow":
        # Cursor preToolUse does not enforce ask. Block for owner intervention.
        return {"permission": "deny", "user_message": reason, "agent_message": reason}
    if EVENT == "stop" and reason.startswith("governance-warning"):
        return {"followup_message": reason}
    if "warning" in reason:
        return {"additional_context": reason}
    return {}


def main() -> int:
    payload = sys.stdin.buffer.read(1024 * 1024 + 1)
    decision = neutral_decision(payload)
    print(json.dumps(translate(decision), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
