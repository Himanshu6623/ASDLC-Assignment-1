"""Prompt construction, model call and output parsing for the Reminder Agent."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .contract import parse_offset_datetime, validate_result

PROMPT_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "system_prompt.md"
_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


class Provider(Protocol):
    def generate(self, system: str, user: str) -> str: ...


class InputError(ValueError):
    """The request violates the input contract (FR-001)."""


class InvalidModelOutput(ValueError):
    """The model reply could not be used because it broke the output contract."""


@dataclass
class AgentOutput:
    raw_text: str
    parsed: Any | None
    parse_error: str | None


def load_system_prompt(path: Path | None = None) -> str:
    return (path or PROMPT_PATH).read_text(encoding="utf-8")


def build_user_message(text: str, now: str) -> str:
    """The user text is passed as JSON data, never concatenated into instructions."""
    return json.dumps({"now": now, "text": text}, ensure_ascii=False)


def extract_json(raw: str) -> tuple[Any | None, str | None]:
    candidate = raw.strip()
    fenced = _FENCE.match(candidate)
    if fenced:
        candidate = fenced.group(1)
    try:
        return json.loads(candidate), None
    except json.JSONDecodeError as exc:
        return None, f"reply is not valid JSON: {exc.msg}"


def interpret(text: str, now: str, provider: Provider, system_prompt: str) -> AgentOutput:
    """Call the model and parse its reply. ServiceError from the provider propagates."""
    if not isinstance(text, str):
        raise InputError("text must be a string")
    if parse_offset_datetime(now) is None:
        raise InputError("now must be ISO-8601 with a UTC offset")
    raw = provider.generate(system_prompt, build_user_message(text, now))
    parsed, error = extract_json(raw)
    return AgentOutput(raw_text=raw, parsed=parsed, parse_error=error)


def safe_result(output: AgentOutput) -> dict[str, Any]:
    """Return the parsed result only if it satisfies the output contract."""
    if output.parse_error is not None:
        raise InvalidModelOutput(output.parse_error)
    problems = validate_result(output.parsed)
    if problems:
        raise InvalidModelOutput("; ".join(problems))
    return output.parsed  # type: ignore[no-any-return]
