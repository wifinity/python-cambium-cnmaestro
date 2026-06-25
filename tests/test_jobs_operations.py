from __future__ import annotations

import pytest

from cambium_cnmaestro import CnMaestroClient
from cambium_cnmaestro.errors import CnMaestroError, CnMaestroNotFoundError

BASE_URL = "https://cnmaestro.example.test"

_JOB_ID = "bd4c8f62e89c4633ac9370862b4b1ec4"

_JOB_ITEM = {
    "job_id": _JOB_ID,
    "display_id": 359,
    "creation_time": "2026-06-25T08:35:18+00:00",
    "completion_time": "2026-06-25T08:46:32+00:00",
    "created_by": "Auto-Sync",
    "managed_account": "NA",
    "description": "1 device(s)",
    "type": "configuration",
    "state": "Completed",
    "details": {"device_limit": 15, "stop_on_error": False},
    "devices": {"count": 1, "failed": 0, "remaining": 0, "skipped": 0, "success": 1},
}

_JOB_PAGE = {"paging": {"total": 1, "limit": 100, "offset": 0}, "data": [_JOB_ITEM]}

_JOB_DETAILS_PAGE = {
    "paging": {"total": 1, "limit": 100, "offset": 0},
    "data": [
        {
            "name": "cnmatrix-01",
            "mac": "aa:bb:cc:dd:ee:ff",
            "job_id": _JOB_ID,
            "state": "complete",
            "status": "online",
            "message": "Config applied successfully",
            "last_update_time": "2026-06-25T08:46:32+00:00",
            "managed_account": "NA",
        }
    ],
}


def _mock_token(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/api/v2/access/token",
        json={"access_token": "token", "expires_in": 3600},
        headers={"Content-Type": "application/json"},
    )


def test_jobs_list_sends_type_param(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs",
        match_params={"type": "configuration"},
        json={"paging": {"total": 2, "limit": 100, "offset": 0}, "data": [_JOB_ITEM]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    resp = client.jobs.list(type="configuration")

    assert isinstance(resp, dict)
    assert resp["paging"]["total"] == 2


def test_jobs_list_software_type(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs",
        match_params={"type": "software"},
        json={"paging": {"total": 0, "limit": 100, "offset": 0}, "data": []},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    resp = client.jobs.list(type="software")

    assert resp["paging"]["total"] == 0


def test_jobs_list_merges_extra_params(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs",
        match_params={"type": "configuration", "limit": "10", "offset": "0"},
        json={"paging": {"total": 1, "limit": 10, "offset": 0}, "data": [_JOB_ITEM]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    resp = client.jobs.list(type="configuration", params={"limit": "10", "offset": "0"})

    assert resp["paging"]["total"] == 1


def test_jobs_get_hits_correct_url(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs/{_JOB_ID}",
        json=_JOB_PAGE,
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    resp = client.jobs.get(job_id=_JOB_ID)

    assert resp["paging"]["total"] == 1
    assert resp["data"][0]["job_id"] == _JOB_ID


def test_jobs_get_details_hits_correct_url(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs/{_JOB_ID}/details",
        json=_JOB_DETAILS_PAGE,
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    resp = client.jobs.get_details(job_id=_JOB_ID)

    assert resp["data"][0]["mac"] == "aa:bb:cc:dd:ee:ff"
    assert resp["data"][0]["state"] == "complete"


def test_jobs_get_status_extracts_fields(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs/{_JOB_ID}",
        json=_JOB_PAGE,
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    status = client.jobs.get_status(job_id=_JOB_ID)

    assert status.job_id == _JOB_ID
    assert status.state == "Completed"
    assert status.type == "configuration"
    assert status.count == 1
    assert status.success == 1
    assert status.failed == 0
    assert status.remaining == 0
    assert status.skipped == 0
    assert status.raw == _JOB_ITEM


def test_jobs_get_status_processing_state(httpx_mock) -> None:
    _mock_token(httpx_mock)
    processing_item = {
        **_JOB_ITEM,
        "state": "Processing",
        "devices": {**_JOB_ITEM["devices"], "remaining": 1, "success": 0},
    }
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs/{_JOB_ID}",
        json={"paging": {"total": 1, "limit": 100, "offset": 0}, "data": [processing_item]},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    status = client.jobs.get_status(job_id=_JOB_ID)

    assert status.state == "Processing"
    assert status.remaining == 1
    assert status.success == 0


def test_jobs_get_status_raises_on_404(httpx_mock) -> None:
    _mock_token(httpx_mock)
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs/{_JOB_ID}",
        status_code=404,
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroNotFoundError):
        client.jobs.get_status(job_id=_JOB_ID)


def test_jobs_get_status_raises_on_unexpected_shape(httpx_mock) -> None:
    _mock_token(httpx_mock)
    # total != 1 → extract_single_item returns None → CnMaestroError
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE_URL}/api/v2/jobs/{_JOB_ID}",
        json={"paging": {"total": 0, "limit": 100, "offset": 0}, "data": []},
        headers={"Content-Type": "application/json"},
    )

    client = CnMaestroClient(base_url=BASE_URL, client_id="id", client_secret="secret")
    with pytest.raises(CnMaestroError, match="unexpected response shape"):
        client.jobs.get_status(job_id=_JOB_ID)
