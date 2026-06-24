from __future__ import annotations

import random
import time
from typing import Any

import httpx

from .auth import ClientCredentialsTokenProvider
from .errors import (
    CnMaestroAuthError,
    CnMaestroHTTPError,
    CnMaestroNotFoundError,
    CnMaestroRateLimitError,
)


def _strip_none_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_none_values(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_none_values(v) for v in value]
    return value


class CnMaestroHTTPClient:
    def __init__(
        self,
        *,
        base_url: str,
        token_provider: ClientCredentialsTokenProvider,
        ssl_verify: bool = True,
        timeout_seconds: float = 30.0,
        api_prefix: str = "/api/v2",
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_prefix = api_prefix.rstrip("/")
        self._token_provider = token_provider
        self._client = httpx.Client(verify=ssl_verify, timeout=timeout_seconds)
        self._max_retries = max_retries

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = True,
    ) -> Any:
        # Pre-fetch token before building the URL so redirect_uri is available.
        if auth:
            self._token_provider.get_access_token()
        url = self._build_url(path)
        req_headers = self._build_headers(headers=headers, auth=auth)

        payload_json = json
        if payload_json is not None and method.upper() != "GET":
            payload_json = _strip_none_values(payload_json)

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._send(
                    method=method,
                    url=url,
                    params=params,
                    json=payload_json,
                    data=data,
                    headers=req_headers,
                )
            except httpx.HTTPError as e:
                last_exc = e
                if attempt >= self._max_retries:
                    raise CnMaestroHTTPError(f"HTTP request failed: {e!s}") from e
                time.sleep(0.5 * (2**attempt))
                continue

            if resp.status_code == 429:
                retry_after = self._compute_retry_after_seconds(resp)
                if attempt >= self._max_retries:
                    raise CnMaestroRateLimitError("Rate limited (429)", retry_after_seconds=retry_after)
                time.sleep(retry_after)
                continue
            return self._parse_or_raise(resp)

        # Should be unreachable
        if last_exc is not None:
            raise CnMaestroHTTPError(f"HTTP request failed: {last_exc!s}") from last_exc
        raise CnMaestroHTTPError("HTTP request failed")

    def iter_continuation_pages(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        current_params: dict[str, Any] = dict(params or {})

        while True:
            page = self.request("GET", path, params=current_params)
            if not isinstance(page, dict):
                pages.append({"data": page})
                return pages

            pages.append(page)
            paging = page.get("paging")
            if not isinstance(paging, dict):
                return pages

            token = paging.get("next_continuation_token")
            if not isinstance(token, str) or not token:
                return pages

            current_params = dict(current_params)
            current_params["continuation_token"] = token

    def _build_url(self, path: str) -> str:
        path = path if path.startswith("/") else f"/{path}"
        base = self._token_provider.get_effective_base_url()
        return f"{base}{self._api_prefix}{path}"

    def _build_headers(self, *, headers: dict[str, str] | None, auth: bool) -> dict[str, str]:
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)
        if auth:
            token = self._token_provider.get_access_token()
            req_headers["Authorization"] = f"Bearer {token}"
        return req_headers

    def _send(
        self,
        *,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
        data: dict[str, Any] | None,
        headers: dict[str, str],
    ) -> httpx.Response:
        return self._client.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            data=data,
            headers=headers,
        )

    def _parse_or_raise(self, resp: httpx.Response) -> Any:
        if resp.status_code in (401, 403):
            self._token_provider.clear_cache()
            raise CnMaestroAuthError(f"Unauthorized ({resp.status_code})")

        if resp.status_code == 404:
            raise CnMaestroNotFoundError("Not found (404)")

        if resp.status_code >= 400:
            raise CnMaestroHTTPError(
                f"HTTP error ({resp.status_code})",
                status_code=resp.status_code,
                response_text=resp.text,
            )

        if resp.status_code == 204:
            return None

        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return resp.json()
        return resp.text

    def _compute_retry_after_seconds(self, resp: httpx.Response) -> float:
        reset = resp.headers.get("RateLimit-Reset")
        if reset:
            try:
                reset_epoch = int(reset)
                wait = max(0.0, float(reset_epoch) - time.time())
                return wait + random.random()
            except ValueError:
                pass
        retry_after = resp.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after) + random.random()
            except ValueError:
                pass
        return 1.0 + random.random()
