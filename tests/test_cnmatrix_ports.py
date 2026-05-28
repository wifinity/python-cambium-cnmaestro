from __future__ import annotations

from cambium_cnmaestro import CnMaestroClient

BASE_URL = "https://cnmaestro.example.test"


def _mock_token(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/access/token",
        json={"access_token": "token", "expires_in": 3600},
        headers={"Content-Type": "application/json"},
    )


def test_ports_update_sends_put_with_ports_body(httpx_mock) -> None:
    _mock_token(httpx_mock)
    ports = [{"mac": "A0:B0:C0:02:23:51", "config": {"basic": {"description": "test1"}}}]
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/cnmatrix/ports",
        json={"paging": {"total": 1}, "data": [{"status": "ok"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.cnmatrix.ports.update(ports=ports)
    assert result is not None

    request = httpx_mock.get_request(method="PUT", url=f"{BASE_URL}/api/v2/cnmatrix/ports")
    assert request is not None
    assert request.content is not None
    assert b'"ports"' in request.content
    assert b"A0:B0:C0:02:23:51" in request.content


def test_switch_groups_ports_list_for_switch_group(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups_ports/building-a",
        json={"paging": {"total": 1}, "data": [{"switch_group": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.cnmatrix.switch_groups_ports.list_for_switch_group(switch_group_name="building-a")
    assert result["data"][0]["switch_group"] == "building-a"


def test_switch_groups_ports_get_for_device(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups_ports/building-a/aa:bb:cc:dd:ee:ff",
        json={"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc:dd:ee:ff"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.cnmatrix.switch_groups_ports.get_for_device(
        switch_group_name="building-a",
        device_mac="aa:bb:cc:dd:ee:ff",
    )
    assert result["data"][0]["mac"] == "aa:bb:cc:dd:ee:ff"
