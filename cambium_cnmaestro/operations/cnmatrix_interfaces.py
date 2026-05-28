from __future__ import annotations

from datetime import datetime, timezone
from importlib import resources
from io import StringIO
from typing import Any

import textfsm  # type: ignore[import-untyped]

from ..results import Interface


def parse_cnmatrix_show_interfaces_output(*, raw_interface_output: str, now: datetime | None = None) -> list[Interface]:
    records = _parse_textfsm_template(
        template_name="cnmatrix_show_interfaces.textfsm",
        raw_output=raw_interface_output,
    )

    interfaces: list[Interface] = []
    for row in records:
        name = _get_str(row, "NAME")
        if not name:
            continue

        admin = _get_str(row, "ADMIN_STATUS")
        line_proto = _get_str(row, "LINE_PROTOCOL_STATUS")

        mtu = _get_int(row, "MTU")
        mac = _get_str(row, "MAC_ADDRESS")

        speed = _speed_to_mbit(_get_str(row, "SPEED_VALUE"), _get_str(row, "SPEED_UNIT"))
        last_flapped = _last_transition_to_last_flapped_unix_timestamp(_get_str(row, "LAST_TRANSITION"))

        interfaces.append(
            Interface(
                name=name,
                is_enabled=_status_to_bool(admin),
                is_up=_status_to_bool(line_proto),
                description=None,
                last_flapped=last_flapped,
                speed=speed,
                mtu=mtu,
                mac_address=mac or None,
            )
        )

    return interfaces


def _parse_textfsm_template(*, template_name: str, raw_output: str) -> list[dict[str, Any]]:
    """
    Returns list of dict rows. Parsing is lenient: on template load/parse failure, returns [].
    """
    try:
        template_text = (
            resources.files("cambium_cnmaestro.textfsm_templates").joinpath(template_name).read_text(encoding="utf-8")
        )
    except Exception:
        return []

    try:
        fsm = textfsm.TextFSM(StringIO(template_text))
    except Exception:
        return []

    # Ensure final record is emitted by template.
    text = raw_output.rstrip("\n") + "\n__TEXTFSM_EOF__\n"

    try:
        parsed = fsm.ParseText(text)
    except Exception:
        return []

    headers = [h.strip() for h in getattr(fsm, "header", [])]
    rows: list[dict[str, Any]] = []
    for record in parsed:
        row = {headers[i]: record[i] for i in range(min(len(headers), len(record)))}
        rows.append(row)
    return rows


def _status_to_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    v = value.strip().lower()
    if v == "up":
        return True
    if v == "down":
        return False
    return None


def _get_str(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key)
    return value if isinstance(value, str) else None


def _get_int(row: dict[str, Any], key: str) -> int | None:
    value = row.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _speed_to_mbit(value: str | None, unit: str | None) -> float | None:
    if value is None or unit is None:
        return None
    try:
        v = float(value)
    except ValueError:
        return None
    u = unit.strip()
    if u == "Gbps":
        return v * 1000.0
    if u == "Mbps":
        return v
    return None


def _last_transition_to_last_flapped_unix_timestamp(value: str | None) -> float:
    if value is None:
        return -1.0
    v = value.strip()

    # Example: "Wed May 20 14:07:23 UTC 2026"
    try:
        dt = datetime.strptime(v, "%a %b %d %H:%M:%S %Z %Y")
    except ValueError:
        return -1.0

    # strptime with %Z yields naive datetime for UTC on many platforms; force UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()
