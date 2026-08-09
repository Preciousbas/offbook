"""HTTP retries with exponential backoff for transient Coasty / network failures."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

T = TypeVar("T")

# Match Coasty cookbook conventions: retry transport + rate-limit / gateway errors.
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BASE_SECONDS = 0.5
DEFAULT_CAP_SECONDS = 8.0


class CoastyHTTPError(RuntimeError):
    """Non-retryable or exhausted Coasty HTTP failure."""

    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


def retry_after_seconds(response: httpx.Response) -> float | None:
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return max(0.0, float(header))
    except ValueError:
        return None


def backoff_seconds(
    attempt: int,
    *,
    base: float = DEFAULT_BASE_SECONDS,
    cap: float = DEFAULT_CAP_SECONDS,
    retry_after: float | None = None,
) -> float:
    """Full-jitter exponential backoff; Retry-After wins when larger."""
    exp = min(cap, base * (2 ** max(0, attempt - 1)))
    jittered = random.uniform(0.0, exp)
    if retry_after is not None:
        return max(jittered, retry_after)
    return jittered


def request_with_retries(
    send: Callable[[], httpx.Response],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    base_seconds: float = DEFAULT_BASE_SECONDS,
    cap_seconds: float = DEFAULT_CAP_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """
    Execute ``send`` until success or attempts are exhausted.

    Retries on transport errors and RETRYABLE_STATUS. Other 4xx raise immediately.
    """
    last_exc: Exception | None = None
    last_response: httpx.Response | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = send()
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break
            sleep(backoff_seconds(attempt, base=base_seconds, cap=cap_seconds))
            continue

        if response.status_code < 400:
            return response

        last_response = response
        if response.status_code not in RETRYABLE_STATUS or attempt >= max_attempts:
            body = response.text[:500]
            raise CoastyHTTPError(
                f"Coasty HTTP {response.status_code}: {body}",
                status_code=response.status_code,
                body=body,
            )

        sleep(
            backoff_seconds(
                attempt,
                base=base_seconds,
                cap=cap_seconds,
                retry_after=retry_after_seconds(response),
            )
        )

    if last_exc is not None:
        raise CoastyHTTPError(f"Coasty request failed after {max_attempts} attempts: {last_exc}") from last_exc
    if last_response is not None:
        body = last_response.text[:500]
        raise CoastyHTTPError(
            f"Coasty HTTP {last_response.status_code} after {max_attempts} attempts: {body}",
            status_code=last_response.status_code,
            body=body,
        )
    raise CoastyHTTPError(f"Coasty request failed after {max_attempts} attempts")
