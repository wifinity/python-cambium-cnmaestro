from __future__ import annotations

from typing import Any

from ..http import CnMaestroHTTPClient


class SitesResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def get(self, *, network_id: str, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/networks/{network_id}/sites/{name}", params=params)

    def create(self, *, network_id: str, site: dict[str, Any]) -> Any:
        return self._http.request("POST", f"/networks/{network_id}/sites", json=site)

    def update(self, *, network_id: str, name: str, site: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/networks/{network_id}/sites/{name}", json=site)
