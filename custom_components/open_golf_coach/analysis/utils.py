"""Utility helpers for Open Golf Coach analysis."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JsonLoadResult:
    """Result of loading JSON with optional sanitization."""

    data: dict[str, Any]
    sanitized: bool = False


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _sanitize_json_text(raw: str) -> tuple[str, bool]:
    """Remove raw newlines inside JSON strings and strip comments."""
    in_string = False
    escaped = False
    sanitized = False
    out_chars: list[str] = []
    i = 0
    length = len(raw)

    while i < length:
        ch = raw[i]
        if in_string:
            if escaped:
                escaped = False
                out_chars.append(ch)
                i += 1
                continue
            if ch == "\\":
                escaped = True
                out_chars.append(ch)
                i += 1
                continue
            if ch in ("\n", "\r"):
                sanitized = True
                i += 1
                continue
            if ch == '"':
                in_string = False
            out_chars.append(ch)
            i += 1
            continue

        if ch == '"' and not in_string:
            in_string = True
            out_chars.append(ch)
            i += 1
            continue

        if ch == "/" and i + 1 < length:
            nxt = raw[i + 1]
            if nxt == "/":
                sanitized = True
                i += 2
                while i < length and raw[i] not in ("\n", "\r"):
                    i += 1
                continue
            if nxt == "*":
                sanitized = True
                i += 2
                while i + 1 < length and not (raw[i] == "*" and raw[i + 1] == "/"):
                    i += 1
                i += 2
                continue

        out_chars.append(ch)
        i += 1

    return "".join(out_chars), sanitized


def load_json_resource(path: Path) -> JsonLoadResult:
    """Load a JSON file, sanitizing invalid newlines inside strings if needed."""
    raw = path.read_text(encoding="utf-8")
    sanitized_text, sanitized = _sanitize_json_text(raw)
    data = json.loads(sanitized_text)
    return JsonLoadResult(data=data, sanitized=sanitized)
