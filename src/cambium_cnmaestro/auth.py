from __future__ import annotations

import base64
import time
from dataclasses import dataclass

import httpx

from .errors import CnMaestroAuthError, CnMaestroHTTPError


@dataclass
class OAuthToken:
    access_token: str
    expires_at_monotonic: float


class ClientCredentialsTokenProvider:
    def __init__(
        self,
        *,
        base_url: str,
        client_id: str,
        client_secret: str,
        ssl_verify: bool = True,
        timeout_seconds: float = 30.0,
        refresh_buffer_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._ssl_verify = ssl_verify
        self._timeout_seconds = timeout_seconds
        self._refresh_buffer_seconds = refresh_buffer_seconds
        self._token: OAuthToken | None = None

    def clear_cache(self) -> None:
        self._token = None

    def get_access_token(self) -> str:
        now = time.monotonic()
        if self._token is not None and (self._token.expires_at_monotonic - self._refresh_buffer_seconds) > now:
            return self._token.access_token

        token = self._fetch_token()
        self._token = token
        return token.access_token

    def _fetch_token(self) -> OAuthToken:
        token_url = f"{self._base_url}/api/v2/access/token"

        basic = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode("ascii")
        headers = {
            "Authorization": f"Basic {basic}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}

        with httpx.Client(verify=self._ssl_verify, timeout=self._timeout_seconds) as client:
            resp = client.post(token_url, headers=headers, data=data)

        if resp.status_code in (401, 403):
            raise CnMaestroAuthError(f"Token request unauthorized ({resp.status_code})")
        if resp.status_code >= 400:
            raise CnMaestroHTTPError(
                f"Token request failed ({resp.status_code})",
                status_code=resp.status_code,
                response_text=resp.text,
            )

        payload = resp.json()
        access_token = payload.get("access_token")
        expires_in = payload.get("expires_in")
        if not isinstance(access_token, str) or not access_token:
            raise CnMaestroAuthError("Token response missing access_token")
        if not isinstance(expires_in, (int, float)) or expires_in <= 0:
            raise CnMaestroAuthError("Token response missing/invalid expires_in")

        # StackStorm pack caches token until half of expires_in; we replicate that behavior.
        expires_at = time.monotonic() + (float(expires_in) / 2.0)
        return OAuthToken(access_token=access_token, expires_at_monotonic=expires_at)
