from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UpsertResult:
    created: bool
    name: str | None = None
    mac: str | None = None
    status: int = 200
    message: str | None = None


@dataclass(frozen=True)
class DeviceStatus:
    online: bool | None
    profile_attached: str | None
    sync_status: str | None
    mac: str | None
    raw: dict[str, Any]
    onboarding_state: str | None = None


@dataclass(frozen=True)
class InterfaceMac:
    name: str
    mac_address: str


@dataclass(frozen=True)
class Interface:
    name: str
    is_up: bool | None = None
    is_enabled: bool | None = None
    description: str | None = None
    last_flapped: float | None = None
    speed: float | None = None
    mtu: int | None = None
    mac_address: str | None = None


@dataclass(frozen=True)
class LldpNeighbor:
    local_interface: str
    remote_system_name: str
    remote_port_id: str
    chassis_id: str
