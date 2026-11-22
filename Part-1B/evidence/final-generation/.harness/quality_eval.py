"""Layer 3: semantic/quality scoring (title similarity). Never replaces layers 1 and 2."""

from __future__ import annotations

from typing import Any

STOPWORDS = frozenset(
    {"a", "an", "the", "to", "my", "me", "for", "of", "about", "remind", "reminder", "please"}
)


def tokens(text: str) -> set[str]:
    words: list[str] = []
    current: list[str] = []
    for char in text.lower():
        if char.isalnum():
            current.append(char)
        elif current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))
    return {word for word in words if word not in STOPWORDS}


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
