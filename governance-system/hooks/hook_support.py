"""Shared installed adapter transport; policy remains in governancectl.

Disabled projects do not invoke the runtime. An enabled pre-action transport failure
denies; passive failures warn. No payload, environment or child stderr is echoed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable


MAX_PAYLOAD = 1024 * 1024


def repository_root(adapter: str) -> Path | None:
    installed = Path(adapter).resolve().parents[2]
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                                text=True, check=False, timeout=1,
                                env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.SubprocessError):
        pass
    return installed if (installed / ".git").exists() else None


def runtime_path(preferred_host: str = "cursor") -> Path | None:
    override = os.environ.get("GOVERNANCECTL")
    if override:
        candidate = Path(override).expanduser()
        # An explicit stale override is a configuration error, not permission to
        # fall back to a different installed runtime with different policy.
        return candidate.resolve() if candidate.is_file() else None
    hosts = ("claude", "cursor") if preferred_host == "claude" else ("cursor", "claude")
    candidates = [Path("~/.local/share/agent-skills/governance-system/scripts/governancectl").expanduser(),
                  *(Path(f"~/.{host}/skills/governance-system/scripts/governancectl").expanduser() for host in hosts)]
    return next((p.resolve() for p in candidates if p.is_file()), None)


def failure(event: str) -> dict[str, str]:
    return {"permission": "deny" if event == "pre-tool-use" else "allow",
            "reason": "governance-warning: guard unavailable; repair governance configuration/runtime and retry"}


def neutral(payload: bytes, event: str, root_lookup: Callable, runtime_lookup: Callable) -> dict[str, str]:
    try:
        root = root_lookup()
        if root is None:
            return failure(event)
        config_path = root / ".governance/config.json"
        if not config_path.exists() and not config_path.is_symlink():
            return {"permission": "allow", "reason": "governance-disabled"}
        if config_path.is_symlink() or config_path.parent.is_symlink():
            return failure(event)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(config, dict) or any(key in config and type(config[key]) is not bool for key in ("enabled", "hooks_enabled")):
            return failure(event)
        if not config.get("enabled") or not config.get("hooks_enabled"):
            return {"permission": "allow", "reason": "governance-disabled"}
        if len(payload) > MAX_PAYLOAD:
            return failure(event)
        parsed = json.loads(payload.decode("utf-8"))
        if not isinstance(parsed, dict) or ("tool_input" in parsed and not isinstance(parsed["tool_input"], dict)):
            return failure(event)
        if "stop_hook_active" in parsed and type(parsed["stop_hook_active"]) is not bool:
            return failure(event)
        if event == "stop" and parsed.get("stop_hook_active"):
            return {"permission": "allow", "reason": "governance-stop-hook-active"}
        runtime = runtime_lookup()
        if runtime is None:
            return failure(event)
        result = subprocess.run([sys.executable, str(runtime), "--repo", str(root), "--json", "hook", event],
                                input=payload, capture_output=True, check=False, timeout=7)
        if result.returncode != 0:
            return failure(event)
        decision = json.loads(result.stdout.decode("utf-8"))
        if (not isinstance(decision, dict) or decision.get("permission") not in {"allow", "ask", "deny"}
                or not isinstance(decision.get("reason"), str) or not 0 < len(decision["reason"]) <= 4096):
            return failure(event)
        if event in {"stop", "subagent-stop"} and decision["permission"] != "allow":
            return failure(event)
        return {"permission": decision["permission"], "reason": decision["reason"]}
    except (OSError, UnicodeError, ValueError, TypeError, subprocess.SubprocessError):
        return failure(event)
