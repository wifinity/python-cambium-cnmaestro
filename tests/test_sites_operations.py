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


def test_sites_upsert_creates_when_missing(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/networks/net-a/sites/building-a",
        status_code=404,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/networks/net-a/sites",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.sites.upsert(network_id="net-a", site={"name": "building-a"})
    assert result.created is True
    assert result.name == "building-a"


def test_sites_upsert_updates_when_exists(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/networks/net-a/sites/building-a",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/networks/net-a/sites/building-a",
        json={"paging": {"total": 1}, "data": [{"name": "building-a"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.sites.upsert(network_id="net-a", site={"name": "building-a", "description": "updated"})
    assert result.created is False
    assert result.name == "building-a"


def test_sites_upsert_requires_name(httpx_mock) -> None:
    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroError):
        client.sites.upsert(network_id="net-a", site={})
