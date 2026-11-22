"""Tests of the three evaluator layers using hand-written outputs (no model needed)."""

import copy

import pytest
from property_eval import evaluate_properties
from quality_eval import evaluate_quality, jaccard
from schema_eval import validate_structure

NOW = "2026-11-23T10:00:00+05:30"
CASE = {
    "id": "T", "requirement": "FR-006", "category": "normal",
    "input": {"text": "x", "now": NOW}, "expected_intent": "create",
    "expected_title": "call mom", "expected_datetime": "2026-11-24T17:00:00+05:30",
    "tolerance_minutes": 5,
}
GOOD = {"intent": "create", "title": "Call mom", "datetime": "2026-11-24T17:00:00+05:30",
        "snooze_minutes": None, "clarification_question": None}


def checks(findings):
    return {f["check"] for f in findings}


def with_(**kw):
    out = copy.deepcopy(GOOD)
    out.update(kw)
    return out


# ---- layer 1 -------------------------------------------------------------
def test_layer1_accepts_good_output():
    assert validate_structure(GOOD, None) == []


def test_layer1_reports_unparseable_output():
    assert checks(validate_structure(None, "reply is not valid JSON")) == {"valid_json"}


@pytest.mark.parametrize(
    "bad",
    [with_(intent="delete"), with_(title="x" * 101), with_(snooze_minutes=0),
     with_(snooze_minutes=1441), {**GOOD, "extra": 1}, ["not", "an", "object"]],
)
def test_layer1_rejects_contract_violations(bad):
    assert validate_structure(bad, None) != []


def test_layer1_rejects_naive_datetime_and_float_snooze():
    assert "datetime_iso_offset" in checks(validate_structure(with_(datetime="2026-11-24T17:00:00"), None))
    assert validate_structure(with_(intent="snooze", datetime=None, title=None, snooze_minutes=15.0), None)


# ---- layer 2 -------------------------------------------------------------
def test_layer2_accepts_good_create():
    assert evaluate_properties(CASE, GOOD) == []


def test_layer2_wrong_intent_and_allowed_intents():
    assert "intent_expected" in checks(evaluate_properties(CASE, with_(intent="clarify", datetime=None,
        title=None, clarification_question="when?")))
    multi = {**CASE, "allowed_intents": ["clarify", "refuse"]}
    ok = {"intent": "refuse", "title": None, "datetime": None, "snooze_minutes": None,
          "clarification_question": None}
    assert evaluate_properties(multi, ok) == []


def test_layer2_datetime_must_be_future_and_present():
    past = with_(datetime="2026-11-22T17:00:00+05:30")
    assert "datetime_in_future" in checks(evaluate_properties(CASE, past))
    assert "datetime_present" in checks(evaluate_properties(CASE, with_(datetime=None)))


def test_layer2_datetime_tolerance():
    off_by_hour = with_(datetime="2026-11-24T18:00:00+05:30")
    assert "datetime_matches" in checks(evaluate_properties(CASE, off_by_hour))
    within = with_(datetime="2026-11-24T17:04:00+05:30")
    assert "datetime_matches" not in checks(evaluate_properties(CASE, within))


def test_layer2_same_instant_in_other_offset_is_accepted():
    utc = with_(datetime="2026-11-24T11:30:00+00:00")
    assert evaluate_properties(CASE, utc) == []


def test_layer2_title_required_and_unused_fields_null():
    assert "title_non_empty" in checks(evaluate_properties(CASE, with_(title=" ")))
    assert "unused_fields_null" in checks(evaluate_properties(CASE, with_(snooze_minutes=5)))


def test_layer2_clarify_rules():
    case = {**CASE, "expected_intent": "clarify", "requirement": "FR-012"}
    good = {"intent": "clarify", "title": None, "datetime": None, "snooze_minutes": None,
            "clarification_question": "What time?"}
    assert evaluate_properties(case, good) == []
    invented = {**good, "datetime": "2026-11-24T09:00:00+05:30"}
    assert "no_invented_time" in checks(evaluate_properties(case, invented))
    assert "question_non_empty" in checks(evaluate_properties(case, {**good, "clarification_question": ""}))


def test_layer2_refuse_requires_everything_null():
    case = {**CASE, "expected_intent": "refuse", "requirement": "FR-014"}
    leaky = {"intent": "refuse", "title": "hacked", "datetime": None, "snooze_minutes": None,
             "clarification_question": None}
    assert "refuse_all_null" in checks(evaluate_properties(case, leaky))


def test_layer2_snooze_rules():
    case = {"id": "S", "requirement": "FR-009", "category": "normal", "input": {"text": "x", "now": NOW},
            "expected_intent": "snooze", "expected_snooze_minutes": 15}
    good = {"intent": "snooze", "title": None, "datetime": None, "snooze_minutes": 15,
            "clarification_question": None}
    assert evaluate_properties(case, good) == []
    assert "snooze_matches" in checks(evaluate_properties(case, {**good, "snooze_minutes": 30}))
    assert "snooze_present" in checks(evaluate_properties(case, {**good, "snooze_minutes": None}))


# ---- layer 3 -------------------------------------------------------------
def test_layer3_similarity_uses_word_overlap_not_exact_match():
    assert jaccard("Call mom", "call mom") == 1.0
    assert jaccard("Call mom about dinner", "call mom") >= 0.5
    assert jaccard("buy milk", "call mom") == 0.0


def test_layer3_flags_unrelated_title_and_skips_other_intents():
    findings, score = evaluate_quality(CASE, with_(title="Water the plants"), 0.5)
    assert checks(findings) == {"title_similarity"} and score == 0.0
    assert evaluate_quality(CASE, with_(title="Please call mom"), 0.5) == ([], 1.0)
    refuse = {"intent": "refuse", "title": None, "datetime": None, "snooze_minutes": None,
              "clarification_question": None}
    assert evaluate_quality(CASE, refuse, 0.5) == ([], None)
