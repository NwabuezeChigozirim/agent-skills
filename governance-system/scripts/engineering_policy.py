"""Governance-owned, read-only policy selection shared by the three packages.

Policy 2 is reserved, not released. Do not enable it until all enforcement and
migration gates in the reliability program have passed.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Iterable


LEGACY_POLICY = 1
CURRENT_POLICY = 2
CURRENT_POLICY_READY = False
DEFAULT_POLICY = CURRENT_POLICY if CURRENT_POLICY_READY else LEGACY_POLICY


def policy_version(value: Any) -> int:
    if type(value) is not int or value not in {LEGACY_POLICY, CURRENT_POLICY}:
        raise ValueError("policy_version must be 1 (legacy) or 2 (current)")
    return value


def document_policy(path: Path) -> int | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not frontmatter:
        return None
    values = re.findall(r"^policy_version:\s*([^\r\n]*)", frontmatter[1], re.MULTILINE)
    if not values:
        return None
    if len(values) != 1 or values[0].strip() not in {"1", "2"}:
        raise ValueError(f"{path.name}: expected one integer policy_version (1 or 2)")
    return policy_version(int(values[0]))


def evaluate_policy(
    repo: Path, documents: Iterable[Path] = (), requested: str = "auto"
) -> dict[str, Any]:
    """Resolve project authority before CLI preference; never silently downgrade."""
    errors: list[str] = []
    declared = LEGACY_POLICY
    source = "implicit-legacy"
    config_path = repo / ".governance" / "config.json"
    try:
        markers = {value for path in documents if (value := document_policy(path)) is not None}
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(config, dict):
                raise ValueError("Governance config must be a JSON object")
            declared = policy_version(config.get("policy_version", LEGACY_POLICY))
            source = "governance-config"
            if markers - {declared}:
                errors.append("Document policy conflicts with authoritative governance config")
        elif len(markers) > 1:
            errors.append("Conflicting document policy versions; reconcile the artifact set")
        elif markers:
            declared = markers.pop()
            source = "document-metadata"
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(str(exc))
    selected = {"auto": declared, "legacy": LEGACY_POLICY, "current": CURRENT_POLICY}[requested]
    if selected < declared:
        errors.append("Cannot downgrade declared project policy with --policy legacy")
        selected = declared
    ready = selected == LEGACY_POLICY or CURRENT_POLICY_READY
    if not ready:
        errors.append("Current policy 2 is not released; enforcement and migration gates remain incomplete")
    return {
        "policy_version": selected,
        "project_policy_version": declared,
        "policy_source": source,
        "policy_preview": selected != declared,
        "policy_enforcement_ready": ready,
        "policy_errors": errors,
    }
