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


def test_wlans_upsert_creates_when_missing(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/api/v2/wifi_enterprise/wlans/staff", status_code=404)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/wifi_enterprise/wlans",
        json={"paging": {"total": 1}, "data": [{"name": "staff"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.wifi_enterprise.wlans.upsert(wlan={"name": "staff"})
    assert result.created is True
    assert result.name == "staff"


def test_wlans_upsert_updates_when_exists(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/wifi_enterprise/wlans/staff",
        json={"paging": {"total": 1}, "data": [{"name": "staff"}]},
        headers={"Content-Type": "application/json"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{BASE_URL}/api/v2/wifi_enterprise/wlans/staff",
        json={"paging": {"total": 1}, "data": [{"name": "staff"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.wifi_enterprise.wlans.upsert(wlan={"name": "staff", "enabled": True})
    assert result.created is False
    assert result.name == "staff"


def test_ap_groups_upsert_merges_wlans(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(method="GET", url=f"{BASE_URL}/api/v2/wifi_enterprise/ap_groups/default", status_code=404)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/wifi_enterprise/ap_groups",
        json={"paging": {"total": 1}, "data": [{"name": "default"}]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    result = client.wifi_enterprise.ap_groups.upsert(
        ap_group={"name": "default"},
        wlans=["staff", "guest"],
    )
    assert result.created is True
    assert result.name == "default"

    request = httpx_mock.get_request(method="POST", url=f"{BASE_URL}/api/v2/wifi_enterprise/ap_groups")
    assert request is not None
    assert request.content is not None
    assert b'"wlans"' in request.content
    assert b"staff" in request.content


def test_ap_groups_upsert_requires_name(httpx_mock) -> None:
    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroError):
        client.wifi_enterprise.ap_groups.upsert(ap_group={})
