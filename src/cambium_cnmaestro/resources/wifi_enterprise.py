from __future__ import annotations

from typing import Any

from ..http import CnMaestroHTTPClient


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


class WiFiEnterpriseResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self.wlans = WLANsResource(http)
        self.ap_groups = APGroupsResource(http)
