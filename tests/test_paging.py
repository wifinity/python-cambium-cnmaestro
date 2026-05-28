from __future__ import annotations

import pytest

from cambium_cnmaestro.errors import CnMaestroError
from cambium_cnmaestro.paging import assert_single_item, extract_single_item


def test_extract_single_item_returns_item_when_total_1() -> None:
    page = {"paging": {"total": 1}, "data": [{"mac": "aa:bb:cc:dd:ee:ff"}]}
    assert extract_single_item(page) == {"mac": "aa:bb:cc:dd:ee:ff"}


def test_extract_single_item_returns_none_when_total_0() -> None:
    page = {"paging": {"total": 0}, "data": []}
    assert extract_single_item(page) is None


def test_assert_single_item_raises_when_total_gt_1() -> None:
    page = {"paging": {"total": 2}, "data": [{"id": 1}, {"id": 2}]}
    with pytest.raises(CnMaestroError):
        assert_single_item(page)
