from __future__ import annotations

from typing import Any

from ..errors import CnMaestroError, CnMaestroNotFoundError
from ..http import CnMaestroHTTPClient
from ..paging import extract_single_item
from ..results import UpsertResult


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

    def find(self, *, name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            page = self.get(name=name, params=params)
        except CnMaestroNotFoundError:
            return None
        if not isinstance(page, dict):
            raise CnMaestroError("Expected JSON object response for network get")
        return extract_single_item(page)

    def upsert(self, *, network: dict[str, Any]) -> UpsertResult:
        name = network.get("name")
        if not isinstance(name, str) or not name:
            raise CnMaestroError('network["name"] is required for upsert')

        exists = self.find(name=name) is not None
        if exists:
            # cnMaestro network update is unreliable; StackStorm no-ops when the network exists.
            return UpsertResult(created=False, name=name, status=200)

        self.create(network=network)
        return UpsertResult(created=True, name=name, status=200)
