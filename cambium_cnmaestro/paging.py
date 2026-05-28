from __future__ import annotations

from typing import Any

from .errors import CnMaestroError


def _extract_total(value: Any) -> int | None:
    if not isinstance(value, dict):
        return None
    paging = value.get("paging")
    if not isinstance(paging, dict):
        return None
    total = paging.get("total")
    if isinstance(total, int):
        return total
    return None


def extract_data_items(page: dict[str, Any]) -> list[dict[str, Any]]:
    data = page.get("data")
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def extract_single_item(page: dict[str, Any]) -> dict[str, Any] | None:
    total = _extract_total(page)
    if total != 1:
        return None
    items = extract_data_items(page)
    if len(items) != 1:
        return None
    return items[0]


def assert_single_item(page: dict[str, Any]) -> dict[str, Any]:
    total = _extract_total(page)
    if total is None:
        raise CnMaestroError("Response did not include paging.total")
    if total != 1:
        raise CnMaestroError(f"Expected exactly one item, got {total}")

    item = extract_single_item(page)
    if item is None:
        raise CnMaestroError("Expected exactly one item in data")
    return item
