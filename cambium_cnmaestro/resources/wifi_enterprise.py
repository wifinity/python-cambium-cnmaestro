from __future__ import annotations

from typing import Any, List

from ..errors import CnMaestroError, CnMaestroNotFoundError
from ..http import CnMaestroHTTPClient
from ..paging import extract_single_item
from ..results import UpsertResult


class WLANsResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", "/wifi_enterprise/wlans", params=params)

    def get(self, *, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/wifi_enterprise/wlans/{name}", params=params)

    def create(self, *, wlan: dict[str, Any]) -> Any:
        return self._http.request("POST", "/wifi_enterprise/wlans", json=wlan)

    def update(self, *, name: str, wlan: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/wifi_enterprise/wlans/{name}", json=wlan)

    def find(self, *, name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            page = self.get(name=name, params=params)
        except CnMaestroNotFoundError:
            return None
        if not isinstance(page, dict):
            raise CnMaestroError("Expected JSON object response for wlan get")
        return extract_single_item(page)

    def upsert(self, *, wlan: dict[str, Any]) -> UpsertResult:
        name = wlan.get("name")
        if not isinstance(name, str) or not name:
            raise CnMaestroError('wlan["name"] is required for upsert')

        exists = self.find(name=name) is not None
        if exists:
            self.update(name=name, wlan=wlan)
            return UpsertResult(created=False, name=name, status=200)

        self.create(wlan=wlan)
        return UpsertResult(created=True, name=name, status=200)


class APGroupsResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", "/wifi_enterprise/ap_groups", params=params)

    def get(self, *, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/wifi_enterprise/ap_groups/{name}", params=params)

    def create(self, *, ap_group: dict[str, Any]) -> Any:
        return self._http.request("POST", "/wifi_enterprise/ap_groups", json=ap_group)

    def update(self, *, name: str, ap_group: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/wifi_enterprise/ap_groups/{name}", json=ap_group)

    def find(self, *, name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            page = self.get(name=name, params=params)
        except CnMaestroNotFoundError:
            return None
        if not isinstance(page, dict):
            raise CnMaestroError("Expected JSON object response for ap group get")
        return extract_single_item(page)

    def upsert(
        self,
        *,
        ap_group: dict[str, Any],
        wlans: List[str] | None = None,
    ) -> UpsertResult:
        payload = dict(ap_group)
        if wlans is not None:
            payload["wlans"] = wlans

        name = payload.get("name")
        if not isinstance(name, str) or not name:
            raise CnMaestroError('ap_group["name"] is required for upsert')

        exists = self.find(name=name) is not None
        if exists:
            self.update(name=name, ap_group=payload)
            return UpsertResult(created=False, name=name, status=200)

        self.create(ap_group=payload)
        return UpsertResult(created=True, name=name, status=200)


class WiFiEnterpriseResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self.wlans = WLANsResource(http)
        self.ap_groups = APGroupsResource(http)
