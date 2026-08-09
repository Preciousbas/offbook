"""Thin Coasty Computer Use API client (tasks / runs)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from offbook.config import coasty_api_key, coasty_base_url
from offbook.http_retry import request_with_retries

TERMINAL_STATUSES = frozenset(
    {"succeeded", "success", "completed", "done", "failed", "cancelled", "canceled", "error"}
)


@dataclass
class TaskResult:
    run_id: str
    status: str
    result_text: str | None
    raw: dict[str, Any]
    dry_run: bool = False


class CoastyClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
        *,
        max_retries: int = 5,
    ) -> None:
        self.api_key = api_key if api_key is not None else coasty_api_key()
        self.base_url = (base_url or coasty_base_url()).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._http: httpx.Client | None = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def __enter__(self) -> CoastyClient:
        self._http = httpx.Client(timeout=self.timeout)
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=self.timeout)
        return self._http

    def close(self) -> None:
        if self._http is not None:
            self._http.close()
            self._http = None

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("COASTY_API_KEY is not set")
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "offbook/0.1.0",
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = self._headers(idempotency_key)

        def send() -> httpx.Response:
            return self._client().request(method, url, headers=headers, json=json)

        response = request_with_retries(send, max_attempts=self.max_retries)
        return response.json()

    def create_task(
        self,
        task: str,
        *,
        max_steps: int = 80,
        instructions: str | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"task": task, "max_steps": max_steps}
        if instructions:
            body["instructions"] = instructions
        if metadata:
            body["metadata"] = metadata
        # Stable key so POST retries never double-provision a machine.
        key = idempotency_key or f"offbook-{uuid.uuid4()}"
        return self._request("POST", "/tasks", json=body, idempotency_key=key)

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._request("GET", f"/runs/{run_id}")

    def wait_for_run(
        self,
        run_id: str,
        *,
        poll_seconds: float = 3.0,
        timeout_seconds: float = 900.0,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {}
        while time.time() < deadline:
            last = self.get_run(run_id)
            status = str(last.get("status") or last.get("state") or "").lower()
            if status in TERMINAL_STATUSES:
                return last
            time.sleep(poll_seconds)
        raise TimeoutError(f"Run {run_id} did not finish within {timeout_seconds}s; last={last}")

    def run_task(
        self,
        task: str,
        *,
        dry_run: bool = False,
        dry_run_result: str | None = None,
        max_steps: int = 80,
        instructions: str | None = None,
        metadata: dict[str, Any] | None = None,
        wait: bool = True,
    ) -> TaskResult:
        if dry_run or not self.available:
            return TaskResult(
                run_id=f"dry_{uuid.uuid4().hex[:12]}",
                status="succeeded",
                result_text=dry_run_result
                or (
                    "[dry-run] Coasty task not executed. Set COASTY_API_KEY "
                    "and omit --dry-run to run against a live machine."
                ),
                raw={"dry_run": True, "task": task},
                dry_run=True,
            )

        created = self.create_task(
            task,
            max_steps=max_steps,
            instructions=instructions,
            metadata=metadata,
        )
        run_id = str(created.get("id") or created.get("run_id") or "")
        if not run_id:
            raise RuntimeError(f"Unexpected task response (no run id): {created}")

        raw = self.wait_for_run(run_id) if wait else created
        return TaskResult(
            run_id=run_id,
            status=str(raw.get("status") or raw.get("state") or "unknown"),
            result_text=_extract_result_text(raw),
            raw=raw,
            dry_run=False,
        )


def _extract_result_text(raw: dict[str, Any]) -> str | None:
    for key in ("result", "output", "summary", "message", "answer"):
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, dict):
            for nested in ("text", "content", "summary"):
                nested_val = val.get(nested)
                if isinstance(nested_val, str) and nested_val.strip():
                    return nested_val
    data = raw.get("data")
    return _extract_result_text(data) if isinstance(data, dict) else None
