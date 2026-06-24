from __future__ import annotations

import time
from typing import Any, List

from ..errors import CnMaestroError, CnMaestroHTTPError, CnMaestroNotFoundError
from ..http import CnMaestroHTTPClient
from ..operations.cli import poll_cli_until_complete
from ..operations.cnmatrix_interfaces import parse_cnmatrix_show_interfaces_output
from ..operations.cnmatrix_lldp import parse_cnmatrix_show_lldp_neighbors_output
from ..paging import extract_single_item
from ..results import DeviceStatus, Interface, LldpNeighbor, UpsertResult


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

    def _resolve_existing_mac(self, *, mac: str | None, msn: str | None) -> str | None:
        if mac and self.find(mac=mac) is not None:
            return mac

        if msn:
            found = self.find(msn=msn)
            if found is not None:
                value = found.get("mac")
                if isinstance(value, str) and value:
                    return value

        return None

    def _is_approved_but_not_online_error(self, e: CnMaestroHTTPError) -> bool:
        msg = e.response_text or str(e)
        return e.status_code == 500 and ("Device is already in approved state" in msg or "currently in updating" in msg)

    def _build_update_payload(self, *, device: dict[str, Any]) -> dict[str, Any]:
        # PUT /devices/{mac} schema has additionalProperties: false; `type` is not an allowed field.
        payload = dict(device)
        payload.pop("type", None)
        return payload

    def _build_create_payload(self, *, device: dict[str, Any], msn: str | None) -> tuple[dict[str, Any], str]:
        create_payload = dict(device)
        create_type = create_payload.pop("type", None)
        create_overrides = create_payload.pop("overrides", None)
        _ = create_overrides  # documented create-only quirk; intentionally dropped

        create_msn = msn
        if isinstance(create_payload.get("msn"), str):
            create_msn = create_payload.get("msn")

        if not isinstance(create_type, str) or not create_type:
            raise CnMaestroError("Cant create device without knowing type")
        if not isinstance(create_msn, str) or not create_msn:
            raise CnMaestroError("Cant create device without knowing MSN")

        payload = dict(create_payload)
        payload.update({"type": create_type, "msn": create_msn, "approved": True})
        return payload, create_msn

    def _extract_mac_from_create_response(self, created_page: Any) -> str | None:
        if not isinstance(created_page, dict):
            return None
        created_item = extract_single_item(created_page)
        if created_item is None:
            return None
        value = created_item.get("mac")
        if isinstance(value, str) and value:
            return value
        return None

    def find(
        self,
        *,
        mac: str | None = None,
        msn: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if mac:
            try:
                page = self.get(mac=mac, params=params)
            except CnMaestroNotFoundError:
                return None
            if not isinstance(page, dict):
                raise CnMaestroError("Expected JSON object response for device get")
            return extract_single_item(page)

        if msn:
            search_params = dict(params or {})
            search_params["search"] = msn
            page = self.list(params=search_params)
            if not isinstance(page, dict):
                raise CnMaestroError("Expected JSON object response for device search")
            item = extract_single_item(page)
            if item is None:
                total = page.get("paging", {}).get("total")
                if isinstance(total, int) and total > 1:
                    raise CnMaestroError("Attempted to get single device record, but multiple were returned.")
            return item

        raise ValueError("Either mac or msn must be provided (use list() for collection queries).")

    def get_status(self, *, mac: str | None = None, msn: str | None = None) -> DeviceStatus:
        device = self.find(mac=mac, msn=msn)
        if device is None:
            raise CnMaestroNotFoundError("Device not found")

        online = device.get("online") if isinstance(device.get("online"), bool) else None
        profile_attached = device.get("profile_attached") if isinstance(device.get("profile_attached"), str) else None

        sync_status: str | None = None
        config = device.get("config")
        if isinstance(config, dict):
            value = config.get("sync_status")
            if isinstance(value, str):
                sync_status = value

        device_mac = device.get("mac") if isinstance(device.get("mac"), str) else None

        onboarding_state: str | None = None
        onboarding = device.get("onboarding")
        if isinstance(onboarding, dict):
            value = onboarding.get("state")
            if isinstance(value, str):
                onboarding_state = value

        return DeviceStatus(
            online=online,
            profile_attached=profile_attached,
            sync_status=sync_status,
            mac=device_mac,
            onboarding_state=onboarding_state,
            raw=device,
        )

    def upsert(
        self,
        *,
        device: dict[str, Any],
        mac: str | None = None,
        msn: str | None = None,
    ) -> UpsertResult:
        """
        StackStorm parity helper for cnmaestro.upsert.devices:
        - Resolve by mac if provided; else search by msn (if provided).
        - Create when missing (requires type + msn, sets approved=True, strips overrides).
        - Update when found (strips type — not accepted by PUT /devices/{mac}).
        - Treat certain \"approved but not online\" server errors as a 423 soft-success.
        """
        resolved_mac = self._resolve_existing_mac(mac=mac, msn=msn)
        if resolved_mac is not None:
            update_payload = self._build_update_payload(device=device)
            try:
                self.update(mac=resolved_mac, device=update_payload)
            except CnMaestroHTTPError as e:
                if self._is_approved_but_not_online_error(e):
                    return UpsertResult(
                        created=False,
                        mac=resolved_mac,
                        status=423,
                        message="Device approved, but not online yet, can't change config",
                    )
                raise
            return UpsertResult(created=False, mac=resolved_mac, status=200)

        payload, _create_msn = self._build_create_payload(device=device, msn=msn)
        created_page = self.create(device=payload)
        created_mac = self._extract_mac_from_create_response(created_page)
        return UpsertResult(created=True, mac=created_mac, status=200)

    def bulk_upsert(self, *, updates: List[dict[str, Any]]) -> List[UpsertResult]:
        results: List[UpsertResult] = []
        for item in updates:
            config = item.get("config", item.get("device"))
            if not isinstance(config, dict):
                raise CnMaestroError('bulk_upsert item requires "config" or "device" dict')

            mac = item.get("mac")
            msn = item.get("msn")
            results.append(
                self.upsert(
                    device=config,
                    mac=mac if isinstance(mac, str) else None,
                    msn=msn if isinstance(msn, str) else None,
                )
            )
        return results

    def run_cli_command_and_wait(
        self,
        *,
        mac: str | None = None,
        msn: str | None = None,
        command: str,
        trigger_retry_delay_seconds: float = 60.0,
        trigger_max_attempts: int = 20,
        initial_delay_seconds: float = 10.0,
        poll_interval_seconds: float = 15.0,
        poll_max_attempts: int = 3,
    ) -> str:
        resolved_mac = mac
        if resolved_mac is None:
            if msn is None:
                raise ValueError("Either mac or msn must be provided.")
            found = self.find(msn=msn)
            if found is None:
                raise CnMaestroNotFoundError("Device not found")
            value = found.get("mac")
            if not isinstance(value, str) or not value:
                raise CnMaestroError("Resolved device is missing mac address")
            resolved_mac = value

        self._run_cli_with_retry(
            mac=resolved_mac,
            command=command,
            retry_delay_seconds=trigger_retry_delay_seconds,
            max_attempts=trigger_max_attempts,
        )

        raw_output = poll_cli_until_complete(
            lambda: self.get_cli(mac=resolved_mac),
            initial_delay_seconds=initial_delay_seconds,
            poll_interval_seconds=poll_interval_seconds,
            max_attempts=poll_max_attempts,
        )
        return raw_output

    def get_interfaces(
        self,
        *,
        mac: str | None = None,
        msn: str | None = None,
        command: str = "show interfaces",
        trigger_retry_delay_seconds: float = 60.0,
        trigger_max_attempts: int = 20,
        initial_delay_seconds: float = 10.0,
        poll_interval_seconds: float = 15.0,
        poll_max_attempts: int = 3,
    ) -> List[Interface]:
        raw_output = self.run_cli_command_and_wait(
            mac=mac,
            msn=msn,
            command=command,
            trigger_retry_delay_seconds=trigger_retry_delay_seconds,
            trigger_max_attempts=trigger_max_attempts,
            initial_delay_seconds=initial_delay_seconds,
            poll_interval_seconds=poll_interval_seconds,
            poll_max_attempts=poll_max_attempts,
        )
        return parse_cnmatrix_show_interfaces_output(raw_interface_output=raw_output)

    def get_lldp_neighbors(
        self,
        *,
        mac: str | None = None,
        msn: str | None = None,
        command: str = "show lldp neighbors detail",
        trigger_retry_delay_seconds: float = 60.0,
        trigger_max_attempts: int = 20,
        initial_delay_seconds: float = 10.0,
        poll_interval_seconds: float = 15.0,
        poll_max_attempts: int = 3,
    ) -> List[LldpNeighbor]:
        raw_output = self.run_cli_command_and_wait(
            mac=mac,
            msn=msn,
            command=command,
            trigger_retry_delay_seconds=trigger_retry_delay_seconds,
            trigger_max_attempts=trigger_max_attempts,
            initial_delay_seconds=initial_delay_seconds,
            poll_interval_seconds=poll_interval_seconds,
            poll_max_attempts=poll_max_attempts,
        )
        return parse_cnmatrix_show_lldp_neighbors_output(raw_output=raw_output)

    def _run_cli_with_retry(
        self,
        *,
        mac: str,
        command: str,
        retry_delay_seconds: float,
        max_attempts: int,
    ) -> None:
        last_exc: Exception | None = None
        for attempt in range(max_attempts):
            try:
                self.run_cli(mac=mac, command=command)
                return
            except CnMaestroHTTPError as e:
                last_exc = e
                if attempt >= max_attempts - 1:
                    raise
                time.sleep(retry_delay_seconds)

        if last_exc is not None:
            raise last_exc
        raise CnMaestroError("Failed to trigger CLI command")
