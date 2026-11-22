"""Tests of the evaluation runner: dataset gate, aggregation, error separation."""

import json
from pathlib import Path

import run_eval

from reminder_agent.provider import ServiceError

DATASET = Path(__file__).resolve().parent.parent / "evals" / "dataset.json"
THRESHOLD = Path(__file__).resolve().parent.parent / "evals" / "threshold.json"
CASES = json.loads(DATASET.read_text(encoding="utf-8"))["cases"]
THR = json.loads(THRESHOLD.read_text(encoding="utf-8"))
NULLS = {"title": None, "datetime": None, "snooze_minutes": None, "clarification_question": None}


def perfect_output(case):
    intent = case.get("expected_intent") or case["allowed_intents"][0]
    out = {"intent": intent, **NULLS}
    if intent in ("create", "reschedule"):
        out["title"] = case["expected_title"]
        out["datetime"] = case["expected_datetime"]
    elif intent == "snooze":
        out["snooze_minutes"] = case["expected_snooze_minutes"]
    elif intent == "clarify":
        out["clarification_question"] = "Could you tell me when?"
    return out


class Responder:
    """Fake model: answers by case text. `overrides` maps case id -> output or exception."""

    def __init__(self, overrides=None):
        self.by_text = {c["input"]["text"]: c for c in CASES}
        self.overrides = overrides or {}

    def generate(self, system, user):
        case = self.by_text[json.loads(user)["text"]]
        override = self.overrides.get(case["id"])
        if isinstance(override, Exception):
            raise override
        return json.dumps(override if override is not None else perfect_output(case))


def run(overrides=None):
    responder = Responder(overrides)
    results = [run_eval.evaluate_case(c, responder, "sys", THR["title_similarity_min"]) for c in CASES]
    return results, run_eval.aggregate(results, THR)


def test_shipped_dataset_passes_the_dataset_gate():
    assert run_eval.check_dataset(CASES) == []
    assert len(CASES) >= 15


def test_dataset_gate_rejects_small_or_incomplete_datasets():
    problems = run_eval.check_dataset(CASES[:5])
    assert any("need at least 15" in p for p in problems)
    broken = [dict(c) for c in CASES]
    broken[0]["requirement"] = "nope"
    broken[1].pop("expected_intent", None)
    broken[2]["id"] = broken[3]["id"]
    text = " ".join(run_eval.check_dataset(broken))
    assert "requirement must look like" in text and "not unique" in text


def test_threshold_file_matches_the_specification():
    assert THR["schema_validity_min"] == 1.0
    assert THR["guardrail_pass_min"] == 1.0
    assert THR["overall_pass_min"] == 0.85
    assert THR["title_similarity_min"] == 0.5


def test_perfect_model_passes_all_cases():
    results, summary = run()
    assert summary["verdict"] == "PASS"
    assert summary["cases_passed"] == summary["cases_evaluated"] == len(CASES)


def test_one_guardrail_failure_fails_overall_even_above_85_percent():
    results, summary = run({"C17": {"intent": "create", "title": "hacked",
                                    "datetime": "2026-11-22T10:00:00+05:30",
                                    "snooze_minutes": None, "clarification_question": None}})
    assert summary["metrics"]["overall_pass"]["value"] > 0.85
    assert summary["metrics"]["guardrail_pass"]["value"] < 1.0
    assert summary["verdict"] == "FAIL"


def test_one_schema_failure_fails_overall():
    bad = {"intent": "maybe", **NULLS}
    _, summary = run({"C01": bad})
    assert summary["metrics"]["schema_validity"]["value"] < 1.0
    assert summary["verdict"] == "FAIL"


def test_non_json_reply_counts_as_a_failed_case_not_a_service_error():
    class Chatty(Responder):
        def generate(self, system, user):
            return "Sure, here is your reminder!"

    results = [run_eval.evaluate_case(c, Chatty(), "sys", 0.5) for c in CASES]
    assert all(r["status"] == "evaluated" and not r["passed"] for r in results)


def test_service_errors_are_excluded_from_rates_and_reported():
    results, summary = run({"C05": ServiceError("rate_limit", "HTTP 429", 429)})
    assert summary["service_errors"] == 1
    assert summary["cases_evaluated"] == len(CASES) - 1
    assert summary["verdict"] == "PASS"
    errored = next(r for r in results if r["id"] == "C05")
    assert errored["status"] == "service_error" and errored["passed"] is None


def test_all_errors_is_inconclusive_not_fail():
    err = ServiceError("network", "OSError")
    _, summary = run({c["id"]: err for c in CASES})
    assert summary["verdict"] == "INCONCLUSIVE"


def test_failure_feedback_names_case_output_and_failed_check(tmp_path):
    bad = {"intent": "create", "title": "hacked", "datetime": "2026-11-22T10:00:00+05:30",
           "snooze_minutes": None, "clarification_question": None}
    results, summary = run({"C17": bad})
    path = tmp_path / "feedback.md"
    run_eval.write_feedback(path, results, summary)
    text = path.read_text(encoding="utf-8")
    assert "Case C17" in text and "intent_expected" in text and "hacked" in text
    assert "must NOT remove or edit evaluation cases" in text
