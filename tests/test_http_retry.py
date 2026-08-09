"""Tests for Coasty HTTP retry / backoff."""

from __future__ import annotations

import httpx
import pytest

from offbook.http_retry import (
    CoastyHTTPError,
    backoff_seconds,
    request_with_retries,
    retry_after_seconds,
)


def test_backoff_respects_retry_after():
    delay = backoff_seconds(1, base=0.01, cap=0.02, retry_after=1.5)
    assert delay >= 1.5


def test_retry_after_parses_numeric_header():
    response = httpx.Response(429, headers={"Retry-After": "2"})
    assert retry_after_seconds(response) == 2.0


def test_retries_then_succeeds_on_503(monkeypatch: pytest.MonkeyPatch):
    sleeps: list[float] = []
    monkeypatch.setattr("offbook.http_retry.random.uniform", lambda _a, _b: 0.0)

    calls = {"n": 0}

    def send() -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, json={"ok": True})

    response = request_with_retries(send, max_attempts=5, base_seconds=0.01, cap_seconds=0.01, sleep=sleeps.append)
    assert response.status_code == 200
    assert calls["n"] == 3
    assert len(sleeps) == 2


def test_retries_transport_error_then_succeeds(monkeypatch: pytest.MonkeyPatch):
    sleeps: list[float] = []
    monkeypatch.setattr("offbook.http_retry.random.uniform", lambda _a, _b: 0.0)
    calls = {"n": 0}

    def send() -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("compute offline")
        return httpx.Response(200, json={"ok": True})

    response = request_with_retries(send, max_attempts=3, base_seconds=0.01, cap_seconds=0.01, sleep=sleeps.append)
    assert response.status_code == 200
    assert calls["n"] == 2
    assert sleeps


def test_non_retryable_4xx_raises_immediately():
    calls = {"n": 0}

    def send() -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, text="unauthorized")

    with pytest.raises(CoastyHTTPError) as exc:
        request_with_retries(send, max_attempts=5, sleep=lambda _s: None)
    assert exc.value.status_code == 401
    assert calls["n"] == 1


def test_exhausted_retries_raise():
    def send() -> httpx.Response:
        return httpx.Response(503, text="still down")

    with pytest.raises(CoastyHTTPError) as exc:
        request_with_retries(send, max_attempts=3, base_seconds=0.0, cap_seconds=0.0, sleep=lambda _s: None)
    assert exc.value.status_code == 503
