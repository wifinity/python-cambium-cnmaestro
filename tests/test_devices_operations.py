from __future__ import annotations

import pytest

from cambium_cnmaestro import CnMaestroClient
from cambium_cnmaestro.errors import CnMaestroError, CnMaestroNotFoundError

BASE_URL = "https://cnmaestro.example.test"


def _mock_token(httpx_mock) -> None:  # pytest-httpx fixture
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/access/token",
        json={"access_token": "token", "expires_in": 3600},
        headers={"Content-Type": "application/json"},
    )


def test_devices_find_by_mac_returns_single_item(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc", "online": True}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    device = client.devices.find(mac="aa:bb:cc")
    assert device is not None
    assert device["mac"] == "aa:bb:cc"


def test_devices_find_by_msn_returns_none_when_not_found(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices",
        match_params={"search": "MSN123"},
        json={"paging": {"total": 0}, "data": []},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    assert client.devices.find(msn="MSN123") is None


def test_devices_find_by_msn_raises_when_multiple_returned(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices",
        match_params={"search": "MSN123"},
        json={"paging": {"total": 2}, "data": [{"mac": "m1"}, {"mac": "m2"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroError):
        client.devices.find(msn="MSN123")


def test_devices_get_status_projects_fields(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={
            "paging": {"total": 1},
            "data": [
                {
                    "mac": "aa:bb:cc",
                    "online": True,
                    "profile_attached": "building-a",
                    "config": {"sync_status": "IN_SYNC"},
                }
            ],
        },
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    status = client.devices.get_status(mac="aa:bb:cc")
    assert status.mac == "aa:bb:cc"
    assert status.online is True
    assert status.profile_attached == "building-a"
    assert status.sync_status == "IN_SYNC"


def test_devices_upsert_creates_when_missing(httpx_mock) -> None:
    _mock_token(httpx_mock)
    # Missing by mac -> 404
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/api/v2/devices/aa:bb:cc", status_code=404)
    # Missing by msn search -> 0 results
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices",
        match_params={"search": "MSN123"},
        json={"paging": {"total": 0}, "data": []},
        headers={"Content-Type": "application/json"},
    )
    # Create
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/devices",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.devices.upsert(mac="aa:bb:cc", msn="MSN123", device={"type": "cnmatrix", "name": "sw1"})
    assert result.created is True
    assert result.mac == "aa:bb:cc"


def test_devices_upsert_updates_when_exists(httpx_mock) -> None:
    _mock_token(httpx_mock)
    # Exists by mac
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.devices.upsert(mac="aa:bb:cc", device={"name": "sw1"})
    assert result.created is False
    assert result.status == 200
    assert result.mac == "aa:bb:cc"


def test_devices_upsert_returns_423_soft_success_on_known_server_error(httpx_mock) -> None:
    _mock_token(httpx_mock)
    # Exists by mac
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        status_code=500,
        text="Device is already in approved state",
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.devices.upsert(mac="aa:bb:cc", device={"name": "sw1"})
    assert result.created is False
    assert result.status == 423


def test_devices_get_status_raises_not_found(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/api/v2/devices/aa:bb:cc", status_code=404)

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroNotFoundError):
        client.devices.get_status(mac="aa:bb:cc")


def test_devices_bulk_upsert_processes_each_update(httpx_mock) -> None:
    _mock_token(httpx_mock)
    # First device exists
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc"}]},
        headers={"Content-Type": "application/json"},
    )
    # Second device missing
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/api/v2/devices/bb:cc:dd", status_code=404)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices",
        match_params={"search": "MSN456"},
        json={"paging": {"total": 0}, "data": []},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/devices",
        json={"paging": {"total": 1}, "data": [{"mac": "bb:cc:dd"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    results = client.devices.bulk_upsert(
        updates=[
            {"mac": "aa:bb:cc", "config": {"name": "sw1"}},
            {"mac": "bb:cc:dd", "msn": "MSN456", "config": {"type": "cnmatrix", "name": "sw2"}},
        ]
    )

    assert len(results) == 2
    assert results[0].created is False
    assert results[0].mac == "aa:bb:cc"
    assert results[1].created is True
    assert results[1].mac == "bb:cc:dd"
