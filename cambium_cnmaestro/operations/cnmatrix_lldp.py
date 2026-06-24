from __future__ import annotations

from ..operations.cnmatrix_interfaces import _parse_textfsm_template
from ..results import LldpNeighbor

_TEMPLATE = "cnmatrix_show_lldp_neighbors_detail.textfsm"


def parse_cnmatrix_show_lldp_neighbors_output(*, raw_output: str) -> list[LldpNeighbor]:
    records = _parse_textfsm_template(template_name=_TEMPLATE, raw_output=raw_output)
    neighbors: list[LldpNeighbor] = []
    for row in records:
        local_iface = (row.get("LOCAL_IFACE") or "").strip()
        chassis_id = (row.get("CHASSIS_ID") or "").strip()
        port_id = (row.get("PORT_ID") or "").strip()
        system_name = (row.get("SYSTEM_NAME") or "").strip()
        if not local_iface:
            continue
        neighbors.append(
            LldpNeighbor(
                local_interface=local_iface,
                remote_system_name=system_name,
                remote_port_id=port_id,
                chassis_id=chassis_id,
            )
        )
    return neighbors
