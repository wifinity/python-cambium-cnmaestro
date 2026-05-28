from __future__ import annotations

from datetime import datetime, timezone

from cambium_cnmaestro.operations.cnmatrix_interfaces import parse_cnmatrix_show_interfaces_output

SAMPLE_CLI_OUTPUT = """\
Gi0/1 up, line protocol is up (connected)
Hardware Address is bc:e6:7c:b7:91:a1
Last transition: Wed May 20 14:07:23 UTC 2026
MTU  1500 bytes, Full duplex, 1 Gbps, Auto-Negotiation

Gi0/2 up, line protocol is down (not connect)
Hardware Address is bc:e6:7c:b7:91:a2
Last transition: Wed May 20 15:07:23 UTC 2026
MTU  1500 bytes, Full duplex, 100 Mbps, Auto-Negotiation
"""


def test_parse_cnmatrix_show_interfaces_output_extracts_name_mac_and_mtu() -> None:
    interfaces = parse_cnmatrix_show_interfaces_output(raw_interface_output=SAMPLE_CLI_OUTPUT)
    assert len(interfaces) == 2
    assert interfaces[0].name == "Gi0/1"
    assert interfaces[0].is_enabled is True
    assert interfaces[0].is_up is True
    assert interfaces[0].mac_address == "bc:e6:7c:b7:91:a1"
    assert interfaces[0].mtu == 1500
    assert interfaces[0].speed == 1000.0
    assert interfaces[0].last_flapped == datetime(2026, 5, 20, 14, 7, 23, tzinfo=timezone.utc).timestamp()

    assert interfaces[1].name == "Gi0/2"
    assert interfaces[1].is_enabled is True
    assert interfaces[1].is_up is False
    assert interfaces[1].mac_address == "bc:e6:7c:b7:91:a2"
    assert interfaces[1].mtu == 1500
    assert interfaces[1].speed == 100.0
    assert interfaces[1].last_flapped == datetime(2026, 5, 20, 15, 7, 23, tzinfo=timezone.utc).timestamp()


def test_parse_cnmatrix_show_interfaces_output_lenient_on_missing_fields() -> None:
    raw = """\
broken is up, line protocol is up
  MTU 1500 bytes
eth2 is up, line protocol is up
  Hardware Address is aa:bb:cc:dd:ee:03
"""
    interfaces = parse_cnmatrix_show_interfaces_output(raw_interface_output=raw)
    assert len(interfaces) == 2
    assert interfaces[0].name == "broken"
    assert interfaces[0].mac_address is None
    assert interfaces[0].mtu == 1500
    assert interfaces[1].name == "eth2"
    assert interfaces[1].mac_address == "aa:bb:cc:dd:ee:03"
    assert interfaces[1].mtu is None


def test_parse_cnmatrix_show_interfaces_output_lenient_on_unexpected_format() -> None:
    interfaces = parse_cnmatrix_show_interfaces_output(raw_interface_output="this is not interface output")
    assert interfaces == []
