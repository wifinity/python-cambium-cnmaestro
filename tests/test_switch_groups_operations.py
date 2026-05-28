from __future__ import annotations

import pytest

from cambium_cnmaestro import CnMaestroClient
from cambium_cnmaestro.errors import CnMaestroError

BASE_URL = "https://cnmaestro.example.test"


def _mock_token(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/access/token",
        json={"access_token": "token", "expires_in": 3600},
        headers={"Content-Type": "application/json"},
    )


def test_switch_groups_find_returns_item(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups/building-a",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    sg = client.cnmatrix.switch_groups.find(name="building-a")
    assert sg is not None
    assert sg["name"] == "building-a"


def test_switch_groups_upsert_creates_when_missing(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups/building-a",
        status_code=404,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.cnmatrix.switch_groups.upsert(switch_group={"name": "building-a", "description": "x"})
    assert result.created is True
    assert result.name == "building-a"


def test_switch_groups_upsert_updates_when_exists(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups/building-a",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/cnmatrix/switch_groups/building-a",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.cnmatrix.switch_groups.upsert(switch_group={"name": "building-a", "description": "y"})
    assert result.created is False
    assert result.name == "building-a"


def test_switch_groups_upsert_requires_name(httpx_mock) -> None:
    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroError):
        client.cnmatrix.switch_groups.upsert(switch_group={})
