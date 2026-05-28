from __future__ import annotations

from typing import Any

from ..errors import CnMaestroError, CnMaestroNotFoundError
from ..http import CnMaestroHTTPClient
from ..paging import extract_single_item
from ..results import UpsertResult


class SitesResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def get(self, *, network_id: str, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/networks/{network_id}/sites/{name}", params=params)

    def create(self, *, network_id: str, site: dict[str, Any]) -> Any:
        return self._http.request("POST", f"/networks/{network_id}/sites", json=site)

    def update(self, *, network_id: str, name: str, site: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/networks/{network_id}/sites/{name}", json=site)

    def find(
        self,
        *,
        network_id: str,
        name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        try:
            page = self.get(network_id=network_id, name=name, params=params)
        except CnMaestroNotFoundError:
            return None
        if not isinstance(page, dict):
            raise CnMaestroError("Expected JSON object response for site get")
        return extract_single_item(page)

    def upsert(self, *, network_id: str, site: dict[str, Any]) -> UpsertResult:
        name = site.get("name")
        if not isinstance(name, str) or not name:
            raise CnMaestroError('site["name"] is required for upsert')

        exists = self.find(network_id=network_id, name=name) is not None
        if exists:
            self.update(network_id=network_id, name=name, site=site)
            return UpsertResult(created=False, name=name, status=200)

        self.create(network_id=network_id, site=site)
        return UpsertResult(created=True, name=name, status=200)
