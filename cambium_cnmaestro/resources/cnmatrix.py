from __future__ import annotations

from typing import Any

from ..errors import CnMaestroError, CnMaestroNotFoundError
from ..http import CnMaestroHTTPClient
from ..paging import extract_single_item
from ..results import UpsertResult


class SwitchGroupsResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", "/cnmatrix/switch_groups", params=params)

    def get(self, *, name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/cnmatrix/switch_groups/{name}", params=params)

    def create(self, *, switch_group: dict[str, Any]) -> Any:
        return self._http.request("POST", "/cnmatrix/switch_groups", json=switch_group)

    def update(self, *, name: str, switch_group: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/cnmatrix/switch_groups/{name}", json=switch_group)

    def find(self, *, name: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            page = self.get(name=name, params=params)
        except CnMaestroNotFoundError:
            return None
        if not isinstance(page, dict):
            raise CnMaestroError("Expected JSON object response for switch group get")
        return extract_single_item(page)

    def upsert(self, *, switch_group: dict[str, Any]) -> UpsertResult:
        name = switch_group.get("name")
        if not isinstance(name, str) or not name:
            raise CnMaestroError('switch_group["name"] is required for upsert')

        exists = self.find(name=name) is not None
        if exists:
            self.update(name=name, switch_group=switch_group)
            return UpsertResult(created=False, name=name, status=200)

        self.create(switch_group=switch_group)
        return UpsertResult(created=True, name=name, status=200)


class SwitchGroupsPortsResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list_for_switch_group(self, *, switch_group_name: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/cnmatrix/switch_groups_ports/{switch_group_name}", params=params)

    def get_for_device(
        self,
        *,
        switch_group_name: str,
        device_mac: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._http.request(
            "GET",
            f"/cnmatrix/switch_groups_ports/{switch_group_name}/{device_mac}",
            params=params,
        )


class PortsResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def update(self, *, ports: list[dict[str, Any]]) -> Any:
        return self._http.request("PUT", "/cnmatrix/ports", json={"ports": ports})


class CnMatrixResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self.switch_groups = SwitchGroupsResource(http)
        self.switch_groups_ports = SwitchGroupsPortsResource(http)
        self.ports = PortsResource(http)
