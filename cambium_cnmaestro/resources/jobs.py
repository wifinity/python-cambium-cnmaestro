from __future__ import annotations

from typing import Any

from ..errors import CnMaestroError
from ..http import CnMaestroHTTPClient
from ..paging import extract_single_item
from ..results import JobStatus


def _job_item_to_status(item: dict[str, Any]) -> JobStatus:
    job_id = item.get("job_id")
    state = item.get("state")
    type_ = item.get("type")

    devices = item.get("devices")
    count = failed = remaining = skipped = success = None
    if isinstance(devices, dict):
        count = devices.get("count")
        failed = devices.get("failed")
        remaining = devices.get("remaining")
        skipped = devices.get("skipped")
        success = devices.get("success")

    return JobStatus(
        job_id=job_id if isinstance(job_id, str) else None,
        state=state if isinstance(state, str) else None,
        type=type_ if isinstance(type_, str) else None,
        count=count if isinstance(count, int) else None,
        failed=failed if isinstance(failed, int) else None,
        remaining=remaining if isinstance(remaining, int) else None,
        skipped=skipped if isinstance(skipped, int) else None,
        success=success if isinstance(success, int) else None,
        raw=item,
    )


class JobsResource:
    def __init__(self, http: CnMaestroHTTPClient) -> None:
        self._http = http

    def list(self, *, type: str, params: dict[str, Any] | None = None) -> Any:
        """List jobs by type. type is required: 'software' or 'configuration'."""
        query: dict[str, Any] = dict(params or {})
        query["type"] = type
        return self._http.request("GET", "/jobs", params=query)

    def get(self, *, job_id: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/jobs/{job_id}", params=params)

    def get_details(self, *, job_id: str, params: dict[str, Any] | None = None) -> Any:
        return self._http.request("GET", f"/jobs/{job_id}/details", params=params)

    def get_status(self, *, job_id: str) -> JobStatus:
        page = self.get(job_id=job_id)
        if not isinstance(page, dict):
            raise CnMaestroError("Expected JSON object response for job get")
        item = extract_single_item(page)
        if item is None:
            raise CnMaestroError(f"Job {job_id!r}: unexpected response shape (total != 1)")
        return _job_item_to_status(item)
