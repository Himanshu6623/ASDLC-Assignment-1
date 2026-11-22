"""Google Gemini REST client (standard library only).

The API key is read from the environment and is never logged or included in errors.
Failures of the model service raise ServiceError so callers can keep them separate
from application or evaluation failures (constitution principle VII).
"""

from __future__ import annotations

import http.client
import json
import os
import time
from collections.abc import Callable
from typing import Any

HOST = "generativelanguage.googleapis.com"
DEFAULT_MODEL = "gemini-flash-latest"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class ServiceError(Exception):
    """The model service failed (network, quota, configuration, blocked or empty reply)."""

    def __init__(self, kind: str, message: str, status: int | None = None) -> None:
        super().__init__(f"{kind}: {message}")
        self.kind = kind
        self.message = message
        self.status = status


class GeminiProvider:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.0,
        timeout: float = 30.0,
        max_attempts: int = 4,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_attempts = max_attempts
        self._sleep = sleeper

    @classmethod
    def from_env(cls) -> GeminiProvider:
        key = os.environ.get("LLM_API_KEY", "").strip()
        if not key:
            raise ServiceError("config", "environment variable LLM_API_KEY is not set")
        model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODEL
        return cls(api_key=key, model=model)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}
        body = json.dumps(payload) if payload is not None else None
        last = ServiceError("network", "no request attempted")
        for attempt in range(1, self.max_attempts + 1):
            conn = http.client.HTTPSConnection(HOST, timeout=self.timeout)
            try:
                conn.request(method, path, body=body, headers=headers)
                response = conn.getresponse()
                raw = response.read()
                status = response.status
            except OSError as exc:
                last = ServiceError("network", type(exc).__name__)
            else:
                if status == 200:
                    try:
                        return json.loads(raw)  # type: ignore[no-any-return]
                    except json.JSONDecodeError as exc:
                        raise ServiceError("bad_response", "service reply was not JSON") from exc
                if status not in RETRY_STATUSES:
                    raise ServiceError("http", f"HTTP {status}", status)
                last = ServiceError("rate_limit" if status == 429 else "server", f"HTTP {status}", status)
            finally:
                conn.close()
            if attempt < self.max_attempts:
                self._sleep(2.0 * (2 ** (attempt - 1)))
        raise last

    def generate(self, system: str, user: str) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "responseMimeType": "application/json",
                "maxOutputTokens": 1024,
            },
        }
        data = self._request("POST", f"/v1beta/models/{self.model}:generateContent", payload)
        if data.get("promptFeedback", {}).get("blockReason"):
            raise ServiceError("blocked", "the service blocked the request")
        texts: list[str] = []
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if isinstance(part.get("text"), str):
                    texts.append(part["text"])
            if texts:
                break
        if not texts:
            raise ServiceError("empty_response", "the service returned no text")
        return "".join(texts)

    def list_models(self) -> list[str]:
        data = self._request("GET", "/v1beta/models?pageSize=100", None)
        names = []
        for model in data.get("models", []):
            if "generateContent" in model.get("supportedGenerationMethods", []):
                names.append(str(model.get("name", "")).removeprefix("models/"))
        return sorted(names)
