"""Output contract of the Reminder Agent and a light, stdlib-only validator.

The evaluation harness has its own, independent JSON Schema in .harness/schema/.
This validator exists so the application never uses unvalidated model output
(constitution principle IV).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

INTENTS = ("create", "reschedule", "snooze", "clarify", "refuse")
FIELDS = ("intent", "title", "datetime", "snooze_minutes", "clarification_question")
MAX_TITLE_LEN = 100
MIN_SNOOZE = 1
MAX_SNOOZE = 1440


def parse_offset_datetime(value: Any) -> datetime | None:
    """Parse an ISO-8601 string that carries a UTC offset; return None otherwise."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def validate_result(parsed: Any) -> list[str]:
    """Return a list of problems; an empty list means the result is acceptable."""
    if not isinstance(parsed, dict):
        return ["output is not a JSON object"]
    problems: list[str] = []
    if set(parsed) != set(FIELDS):
        problems.append(f"fields must be exactly {', '.join(FIELDS)}")
        return problems
    if parsed["intent"] not in INTENTS:
        problems.append("intent is not an allowed value")
    title = parsed["title"]
    if title is not None and (not isinstance(title, str) or len(title) > MAX_TITLE_LEN):
        problems.append("title must be a string of at most 100 characters or null")
    when = parsed["datetime"]
    if when is not None and parse_offset_datetime(when) is None:
        problems.append("datetime must be ISO-8601 with a UTC offset or null")
    minutes = parsed["snooze_minutes"]
    if minutes is not None and (
        isinstance(minutes, bool)
        or not isinstance(minutes, int)
        or not MIN_SNOOZE <= minutes <= MAX_SNOOZE
    ):
        problems.append("snooze_minutes must be an integer from 1 to 1440 or null")
    question = parsed["clarification_question"]
    if question is not None and not isinstance(question, str):
        problems.append("clarification_question must be a string or null")
    intent = parsed["intent"]
    if intent in ("create", "reschedule"):
        if not isinstance(title, str) or not title.strip():
            problems.append("create/reschedule title must be a non-empty string")
        if parse_offset_datetime(when) is None:
            problems.append("create/reschedule datetime must be offset-bearing")
        if parsed["snooze_minutes"] is not None or parsed["clarification_question"] is not None:
            problems.append("create/reschedule unused fields must be null")
    elif intent == "snooze":
        if minutes is None or isinstance(minutes, bool) or not isinstance(minutes, int):
            problems.append("snooze intent requires an integer snooze_minutes")
        if title is not None or when is not None or parsed["clarification_question"] is not None:
            problems.append("snooze unused fields must be null")
    elif intent == "clarify":
        if not isinstance(question, str) or not question.strip():
            problems.append("clarify intent requires a non-empty clarification_question")
        if title is not None or when is not None or minutes is not None:
            problems.append("clarify unused fields must be null")
    elif intent == "refuse":
        payload_fields = ("title", "datetime", "snooze_minutes", "clarification_question")
        if any(parsed[field] is not None for field in payload_fields):
            problems.append("refuse payload fields must be null")
    return problems
