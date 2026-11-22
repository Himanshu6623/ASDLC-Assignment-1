"""Provider tests with a scripted connection: retries, error classification, no key leakage."""

import json

import pytest

from reminder_agent import provider as provider_module
from reminder_agent.provider import GeminiProvider, ServiceError


class Response:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def read(self):
        return self._body


class ScriptedConnection:
    script = []
    seen_headers = []

    def __init__(self, host, timeout=None):
        self.host = host

    def request(self, method, path, body=None, headers=None):
        ScriptedConnection.seen_headers.append(headers)
        step = ScriptedConnection.script.pop(0)
        if isinstance(step, Exception):
            raise step
        self._response = step

    def getresponse(self):
        return self._response

    def close(self):
        pass


@pytest.fixture
def scripted(monkeypatch):
    ScriptedConnection.script = []
    ScriptedConnection.seen_headers = []
    monkeypatch.setattr(provider_module.http.client, "HTTPSConnection", ScriptedConnection)
    return ScriptedConnection


def make(sleeps=None):
    return GeminiProvider("test-key-value", model="m", sleeper=(sleeps if sleeps is not None else []).append)


def ok_body(text):
    return json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode()


def test_success_returns_text(scripted):
    scripted.script = [Response(200, ok_body("hello"))]
    assert make().generate("s", "u") == "hello"
    assert scripted.seen_headers[0]["x-goog-api-key"] == "test-key-value"


def test_rate_limit_is_retried_then_succeeds(scripted):
    scripted.script = [Response(429, b""), Response(503, b""), Response(200, ok_body("ok"))]
    sleeps = []
    assert make(sleeps).generate("s", "u") == "ok"
    assert sleeps == [2.0, 4.0]


def test_persistent_rate_limit_raises_service_error(scripted):
    scripted.script = [Response(429, b"")] * 4
    with pytest.raises(ServiceError) as info:
        make().generate("s", "u")
    assert info.value.kind == "rate_limit" and info.value.status == 429


def test_network_error_is_a_service_error(scripted):
    scripted.script = [TimeoutError()] * 4
    with pytest.raises(ServiceError) as info:
        make().generate("s", "u")
    assert info.value.kind == "network"


def test_client_errors_are_not_retried(scripted):
    scripted.script = [Response(403, b"denied")]
    with pytest.raises(ServiceError) as info:
        make().generate("s", "u")
    assert info.value.kind == "http" and info.value.status == 403


def test_blocked_and_empty_replies_are_service_errors(scripted):
    scripted.script = [Response(200, json.dumps({"promptFeedback": {"blockReason": "SAFETY"}}).encode())]
    with pytest.raises(ServiceError) as blocked:
        make().generate("s", "u")
    assert blocked.value.kind == "blocked"
    scripted.script = [Response(200, json.dumps({"candidates": []}).encode())]
    with pytest.raises(ServiceError) as empty:
        make().generate("s", "u")
    assert empty.value.kind == "empty_response"


def test_constitution_ii_key_never_appears_in_errors(scripted):
    scripted.script = [Response(403, b"test-key-value")]
    with pytest.raises(ServiceError) as info:
        make().generate("s", "u")
    assert "test-key-value" not in str(info.value)


def test_from_env_requires_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ServiceError) as info:
        GeminiProvider.from_env()
    assert info.value.kind == "config"
    monkeypatch.setenv("LLM_API_KEY", "abc")
    monkeypatch.setenv("LLM_MODEL", "custom-model")
    assert GeminiProvider.from_env().model == "custom-model"


def test_list_models_keeps_generate_content_models(scripted):
    body = {"models": [
        {"name": "models/a", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/b", "supportedGenerationMethods": ["embedContent"]},
    ]}
    scripted.script = [Response(200, json.dumps(body).encode())]
    assert make().list_models() == ["a"]


def test_http_error_reports_service_reason_with_key_redacted(scripted):
    body = json.dumps({"error": {"message": "model test-key-value is not found for generateContent"}})
    scripted.script = [Response(404, body.encode())]
    with pytest.raises(ServiceError) as info:
        make().generate("s", "u")
    assert info.value.status == 404
    assert "is not found for generateContent" in info.value.message
    assert "test-key-value" not in str(info.value)
