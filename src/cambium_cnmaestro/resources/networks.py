from __future__ import annotations

from typing import Any

from ..http import CnMaestroHTTPClient


class NetworksResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", "/networks", params=params)

    def get(self, *, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/networks/{name}", params=params)

    def create(self, *, network: dict[str, Any]) -> Any:
        return self._http.request("POST", "/networks", json=network)

    def update(self, *, name: str, network: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/networks/{name}", json=network)
