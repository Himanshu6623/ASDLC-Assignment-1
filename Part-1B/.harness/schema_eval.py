"""Layer 1: structural validation, independent of the application code."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "result.schema.json"
_VALIDATOR = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def _finding(check: str, requirement: str, message: str) -> dict[str, str]:
    return {"layer": "structural", "check": check, "requirement": requirement, "message": message}


def _has_offset(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.utcoffset() is not None


def validate_structure(parsed: Any, parse_error: str | None) -> list[dict[str, str]]:
    """Return findings; an empty list means the output satisfies the output contract."""
    if parse_error is not None or parsed is None:
        return [_finding("valid_json", "FR-002", parse_error or "no JSON output")]
    findings = [
        _finding("schema", "FR-002", f"{'/'.join(str(p) for p in err.path) or 'root'}: {err.message}")
        for err in sorted(_VALIDATOR.iter_errors(parsed), key=lambda e: list(map(str, e.path)))
    ]
    if findings or not isinstance(parsed, dict):
        return findings
    minutes = parsed["snooze_minutes"]
    if minutes is not None and (isinstance(minutes, bool) or not isinstance(minutes, int)):
        findings.append(_finding("snooze_integer", "FR-009", "snooze_minutes is not an integer"))
    when = parsed["datetime"]
    if when is not None and not _has_offset(when):
        findings.append(
            _finding("datetime_iso_offset", "FR-005", "datetime is not ISO-8601 with an offset")
        )
    return findings
