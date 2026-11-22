"""Layer 2: deterministic behavioural properties derived from the specification."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def _finding(check: str, requirement: str, message: str) -> dict[str, str]:
    return {"layer": "property", "check": check, "requirement": requirement, "message": message}


def _parse(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.utcoffset() is not None else None


def evaluate_properties(case: dict[str, Any], output: dict[str, Any]) -> list[dict[str, str]]:
    """`output` has already passed structural validation."""
    findings: list[dict[str, str]] = []
    req = case["requirement"]
    intent = output["intent"]
    allowed = case.get("allowed_intents") or [case["expected_intent"]]
    if intent not in allowed:
        findings.append(
            _finding("intent_expected", req, f"intent {intent!r} not in allowed {allowed}")
        )

    now = _parse(case["input"]["now"])
    when = _parse(output["datetime"]) if output["datetime"] is not None else None

    if intent in ("create", "reschedule"):
        if not (output["title"] or "").strip():
            findings.append(_finding("title_non_empty", "FR-006", "title is empty or null"))
        if when is None:
            findings.append(_finding("datetime_present", "FR-006", "datetime is null"))
        elif now is not None and when <= now:
            findings.append(_finding("datetime_in_future", "FR-006", f"{output['datetime']} <= now"))
        for field in ("snooze_minutes", "clarification_question"):
            if output[field] is not None:
                findings.append(_finding("unused_fields_null", "FR-007", f"{field} should be null"))
    elif intent == "snooze":
        if output["snooze_minutes"] is None:
            findings.append(_finding("snooze_present", "FR-009", "snooze_minutes is null"))
        for field in ("datetime", "clarification_question"):
            if output[field] is not None:
                findings.append(_finding("unused_fields_null", "FR-009", f"{field} should be null"))
    elif intent == "clarify":
        if not (output["clarification_question"] or "").strip():
            findings.append(_finding("question_non_empty", "FR-010", "question is empty or null"))
        if output["datetime"] is not None:
            findings.append(_finding("no_invented_time", "FR-012", "datetime must be null"))
        if output["snooze_minutes"] is not None:
            findings.append(_finding("unused_fields_null", "FR-010", "snooze_minutes should be null"))
    elif intent == "refuse":
        for field in ("title", "datetime", "snooze_minutes", "clarification_question"):
            if output[field] is not None:
                findings.append(_finding("refuse_all_null", "FR-011", f"{field} must be null"))

    expected_when = case.get("expected_datetime")
    if expected_when and intent in ("create", "reschedule") and when is not None:
        expected = _parse(expected_when)
        tolerance = timedelta(minutes=case.get("tolerance_minutes", 0))
        if expected is not None and abs(when - expected) > tolerance:
            findings.append(
                _finding("datetime_matches", req, f"{output['datetime']} vs expected {expected_when}")
            )
    expected_minutes = case.get("expected_snooze_minutes")
    if expected_minutes is not None and output["snooze_minutes"] != expected_minutes:
        findings.append(
            _finding(
                "snooze_matches", "FR-009", f"{output['snooze_minutes']} vs expected {expected_minutes}"
            )
        )
    return findings
