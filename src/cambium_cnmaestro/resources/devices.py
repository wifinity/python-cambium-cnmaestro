from __future__ import annotations

from typing import Any

from ..http import CnMaestroHTTPClient


class DevicesResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", "/devices", params=params)

    def get(self, *, mac: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/devices/{mac}", params=params)

    def create(self, *, device: dict[str, Any]) -> Any:
        return self._http.request("POST", "/devices", json=device)

    def update(self, *, mac: str, device: dict[str, Any]) -> Any:
        return self._http.request("PUT", f"/devices/{mac}", json=device)

    def delete(self, *, mac: str) -> Any:
        return self._http.request("DELETE", f"/devices/{mac}")

    def get_cli(self, *, mac: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/devices/{mac}/cli", params=params)

    def run_cli(self, *, mac: str, command: str) -> Any:
        return self._http.request("POST", f"/devices/{mac}/cli", json={"command": command})
