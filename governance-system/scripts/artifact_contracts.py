"""Small read-only Markdown contracts shared by policy-2 graph checks.

Not a Markdown renderer or an authority store. Definitions come from item headings
and table identity cells; a citation in prose never defines an engineering object.
"""

from __future__ import annotations

import re
from typing import Any

ID = re.compile(r"(?<![\w-])(?:F-NFR|UR|UN|C|F|T|D|O|RK)-\d{3,}(?![\w-])")
ITEM = re.compile(r"^###\s+((?:UR|UN|C|F|T)-\d{3,})\s+[—–-]\s+(.+)$", re.MULTILINE)
LABEL = re.compile(r"^[ \t]*-[ \t]+\*\*([^*\n]+):\*\*[ \t]*(.*)$")
EMPTY = {"", "-", "—", "–", "none", "n/a", "not applicable", "tbd", "todo", "pending", "?"}


def visible(text: str) -> str:
    """Mask examples/comments, preserving line numbers for diagnostics."""
    text = re.sub(r"<!--[\s\S]*?-->", lambda m: "\n" * m[0].count("\n"), text)
    result = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            result.append("\n" if line.endswith("\n") else "")
        elif marker:
            fence = marker[1]
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(line)
    return "".join(result)


def clean(value: str) -> str:
    return value.strip().strip("`*").strip()


def meaningful(value: str) -> bool:
    return clean(value).casefold() not in EMPTY


def ids(value: str, *prefixes: str) -> set[str]:
    return {item for item in ID.findall(value) if not prefixes or item.rsplit("-", 1)[0] in prefixes}


def labels(body: str) -> tuple[dict[str, str], list[str]]:
    fields: dict[str, str] = {}
    duplicates = []
    current = None
    for line in body.splitlines():
        match = LABEL.match(line)
        if match:
            current = match[1].casefold()
            if current in fields:
                duplicates.append(current)
            fields[current] = match[2].strip()
        elif current and re.match(r"^ {2,}\S", line) and not re.match(r"^\s*[-*#]", line):
            fields[current] = (fields[current] + " " + line.strip()).strip()
        elif line.strip():
            current = None
    return fields, duplicates


def items(text: str) -> list[dict[str, Any]]:
    result = []
    for match in ITEM.finditer(text):
        rest = text[match.end():]
        cut = re.search(r"^#{1,3}\s", rest, re.MULTILINE)
        body = rest[:cut.start()] if cut else rest
        fields, duplicates = labels(body)
        result.append({"id": match[1], "name": match[2], "fields": fields,
                       "duplicate_labels": duplicates, "line": text.count("\n", 0, match.start()) + 1})
    return result


def section(text: str, title: str) -> tuple[str, int]:
    match = re.search(rf"^##\s+(?:\d+(?:\.\d+)*\.?\s+)?{re.escape(title)}\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return "", 0
    rest = text[match.end():]
    cut = re.search(r"^#{1,2}\s", rest, re.MULTILINE)
    return (rest[:cut.start()] if cut else rest), text.count("\n", 0, match.end())


def rows(text: str, offset: int = 0) -> list[dict[str, Any]]:
    result = []
    header: list[str] = []
    previous: list[str] | None = None
    for line_number, line in enumerate(text.splitlines(), offset + 1):
        if not line.strip().startswith("|"):
            header, previous = [], None
            continue
        cells = [clean(cell.replace(r"\|", "|")) for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            header = [cell.casefold() for cell in (previous or [])]
            if result and result[-1]["line"] == line_number - 1:
                result.pop()  # The preceding row was the table header, not a definition.
        else:
            result.append({"cells": cells, "fields": dict(zip(header, cells)), "line": line_number})
        previous = cells
    return result


def decisions(text: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    result = {}
    duplicates = []
    for row in rows(visible(text)):
        cells = row["cells"]
        if not cells or not re.fullmatch(r"D-\d{3,}", cells[0]):
            continue
        identifier = cells[0]
        if identifier in result:
            duplicates.append(identifier)
        # Also support the established compact | D-ID | status | decision | register.
        status = row["fields"].get("status", cells[1] if len(cells) > 1 and not row["fields"] else "")
        result[identifier] = {**row, "status": clean(status).casefold()}
    return result, duplicates


def diagnostic(code: str, message: str, path: str, line: int = 1, identifier: str = "", severity: str = "error") -> dict[str, Any]:
    return {"code": code, "message": message, "path": path, "line": line, "id": identifier, "severity": severity}


def messages(report: dict[str, Any], severity: str = "error") -> list[str]:
    return [f"{d['path']}:{d['line']}: [{d['code']}] {d['id']} {d['message']}".strip()
            for d in report["diagnostics"] if d["severity"] == severity]
