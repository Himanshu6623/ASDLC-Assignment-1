"""Layer 3: semantic/quality scoring (title similarity). Never replaces layers 1 and 2."""

from __future__ import annotations

import re
from typing import Any

STOPWORDS = frozenset(
    {"a", "an", "the", "to", "my", "me", "for", "of", "about", "remind", "reminder", "please"}
)


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS}


def jaccard(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def evaluate_quality(
    case: dict[str, Any], output: dict[str, Any], minimum: float
) -> tuple[list[dict[str, str]], float | None]:
    """Return (findings, score). Score is None when the criterion does not apply."""
    expected_title = case.get("expected_title")
    if not expected_title or output["intent"] not in ("create", "reschedule"):
        return [], None
    score = jaccard(output["title"] or "", expected_title)
    if score < minimum:
        finding = {
            "layer": "semantic",
            "check": "title_similarity",
            "requirement": "FR-022",
            "message": f"similarity {score:.2f} < {minimum} ({output['title']!r} vs {expected_title!r})",
        }
        return [finding], score
    return [], score
