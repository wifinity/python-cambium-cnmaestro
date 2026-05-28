from __future__ import annotations

from unittest.mock import patch

from cambium_cnmaestro import CnMaestroClient

BASE_URL = "https://cnmaestro.example.test"

SAMPLE_CLI_OUTPUT = """\
Gi0/1 up, line protocol is up (connected)
Hardware Address is bc:e6:7c:b7:91:a1
Last transition: Wed May 20 14:07:23 UTC 2026
MTU  1500 bytes, Full duplex, 1 Gbps, Auto-Negotiation

Gi0/2 up, line protocol is down (not connect)
Hardware Address is bc:e6:7c:b7:91:a2
Last transition: Wed May 20 15:07:23 UTC 2026
MTU  1500 bytes, Full duplex, 100 Mbps, Auto-Negotiation
"""


def _mock_token(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/access/token",
        json={"access_token": "token", "expires_in": 3600},
        headers={"Content-Type": "application/json"},
    )


@patch("cambium_cnmaestro.operations.cli.time.sleep")
def test_get_interfaces_by_mac(mock_sleep, httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc:dd:ee:ff/cli",
        json={"message": {"status": "in_progress"}},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc:dd:ee:ff/cli",
        json={"message": {"status": "in_progress", "data": []}},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc:dd:ee:ff/cli",
        json={"message": {"status": "complete", "data": [SAMPLE_CLI_OUTPUT]}},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    interfaces = client.devices.get_interfaces(
        mac="aa:bb:cc:dd:ee:ff",
        initial_delay_seconds=0,
        poll_interval_seconds=0,
    )

    assert len(interfaces) == 2
    assert interfaces[0].name == "Gi0/1"
    assert interfaces[0].is_enabled is True
    assert interfaces[0].is_up is True
    assert interfaces[0].mac_address == "bc:e6:7c:b7:91:a1"
    assert interfaces[0].mtu == 1500
    assert interfaces[0].speed == 1000.0

    assert interfaces[1].name == "Gi0/2"
    assert interfaces[1].is_enabled is True
    assert interfaces[1].is_up is False
    assert interfaces[1].mac_address == "bc:e6:7c:b7:91:a2"
    assert interfaces[1].mtu == 1500
    assert interfaces[1].speed == 100.0


@patch("cambium_cnmaestro.operations.cli.time.sleep")
@patch("cambium_cnmaestro.resources.devices.time.sleep")
def test_get_interfaces_by_msn_retries_cli_trigger(mock_device_sleep, mock_cli_sleep, httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices",
        match_params={"search": "MSN123"},
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc:dd:ee:ff/cli",
        status_code=500,
        text="temporary failure",
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc:dd:ee:ff/cli",
        json={"message": {"status": "in_progress"}},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/devices/aa:bb:cc:dd:ee:ff/cli",
        json={"message": {"status": "complete", "data": [SAMPLE_CLI_OUTPUT]}},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    interfaces = client.devices.get_interfaces(
        msn="MSN123",
        trigger_retry_delay_seconds=0,
        initial_delay_seconds=0,
        poll_interval_seconds=0,
    )

    assert len(interfaces) == 2
    assert interfaces[1].name == "Gi0/2"
