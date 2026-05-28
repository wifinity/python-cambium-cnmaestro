# Cambium cnMaestro Python SDK

A Python client library for the Cambium cnMaestro API.

## Features

- **Client-Credentials Authentication**: Handles OAuth2 client credentials token acquisition.
- **Resource-Based API**: Exposes workflow-oriented resources from a single `CnMaestroClient` entry point.
- **Higher-Level Operations**: Includes `find`, `upsert`, `get_status`, and CLI-driven helpers for cnMatrix workflows.
- **Keyword-Only Public APIs**: Resource methods are keyword-only for clarity and call-site stability.

## Installation

```bash
uv venv
uv sync --extra dev
```

Or install the published package:

```bash
pip install cambium-cnmaestro
```

## Quick Start

```python
from cambium_cnmaestro import CnMaestroClient

with CnMaestroClient(
    base_url="https://cnmaestro.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
) as client:
    devices = client.devices.list()
    print(devices)
```

## Usage

### Client Initialization

```python
from cambium_cnmaestro import CnMaestroClient

client = CnMaestroClient(
    base_url="https://cnmaestro.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    # ssl_verify=True,
    # timeout_seconds=30.0,
    # api_prefix="/api/v2",
)
```

### Devices

Use `client.devices` for device CRUD and device-oriented helpers.

```python
# List devices (supports paging/search via params)
devices_page = client.devices.list(params={"page": 1, "pageSize": 100})

# Get a device by MAC
device_page = client.devices.get(mac="aa:bb:cc:dd:ee:ff")

# Find a single device:
# - by mac: uses GET /devices/{mac}
# - by msn: uses GET /devices?search=<msn> and requires a single match
device = client.devices.find(msn="MSN123")

# Project status fields commonly used by switch workflows
status = client.devices.get_status(msn="MSN123")
print(status.online, status.profile_attached, status.sync_status, status.mac)

# Create-or-update (idempotent helper):
# - resolves existing by mac (if given) else by msn search
# - creates when missing (requires type + msn; sets approved=True; strips create-only "overrides")
result = client.devices.upsert(
    msn="MSN123",
    device={
        "type": "cnmatrix",
        "name": "switch-1",
        # ... additional cnMaestro device fields ...
    },
)
print(result)
```

#### Device CLI helpers (cnMatrix)

`client.devices.get_interfaces(...)` triggers a CLI command on the device, polls for completion, and parses the output into structured interface rows (NAPALM-like fields).

```python
interfaces = client.devices.get_interfaces(msn="MSN123")
for iface in interfaces:
    print(iface.name, iface.mac_address, iface.is_up, iface.is_enabled, iface.mtu)
```

### Networks

Use `client.networks` for network CRUD and `upsert(...)`. cnMaestro network update is unreliable, so existing networks are treated as a no-op.

```python
# List and get by name
networks = client.networks.list()
corp = client.networks.get(name="corp")

# Create-or-no-op when it already exists
network_result = client.networks.upsert(
    network={
        "name": "corp",
        # ... network fields ...
    }
)
print(network_result)
```

### Sites

Sites are scoped under a network. Use `client.sites` with `network_id` (cnMaestro network name/id) and `site["name"]`.

```python
site_result = client.sites.upsert(
    network_id="corp",
    site={
        "name": "building-a",
        # ... site fields ...
    },
)
print(site_result)
```

### Wi-Fi Enterprise

Use `client.wifi_enterprise` for Wi-Fi Enterprise resources:

- `client.wifi_enterprise.wlans`
- `client.wifi_enterprise.ap_groups`

```python
# WLANs (SSIDs)
wlan_result = client.wifi_enterprise.wlans.upsert(
    wlan={
        "name": "Guest",
        # ... WLAN fields ...
    }
)

# AP Groups (optionally attach wlans list via upsert helper)
ap_group_result = client.wifi_enterprise.ap_groups.upsert(
    ap_group={
        "name": "building-a-aps",
        # ... AP group fields ...
    },
    wlans=["Guest"],
)
print(wlan_result, ap_group_result)
```

### cnMatrix

Use `client.cnmatrix` for cnMatrix switch group and port workflows:

- `client.cnmatrix.switch_groups`
- `client.cnmatrix.switch_groups_ports`
- `client.cnmatrix.ports`

```python
# Switch groups: find and upsert
sg = client.cnmatrix.switch_groups.find(name="building-a")
sg_result = client.cnmatrix.switch_groups.upsert(
    switch_group={"name": "building-a", "description": "Example"}
)

# Push port config to cnMatrix switches
client.cnmatrix.ports.update(
    ports=[
        {
            "mac": "aa:bb:cc:dd:ee:ff",
            "config": {"basic": {"description": "uplink"}},
        },
    ]
)

# Switch-group port lookups
ports_for_group = client.cnmatrix.switch_groups_ports.list_for_switch_group(switch_group_name="building-a")
ports_for_device = client.cnmatrix.switch_groups_ports.get_for_device(
    switch_group_name="building-a",
    device_mac="aa:bb:cc:dd:ee:ff",
)
print(sg, sg_result, ports_for_group, ports_for_device)
```

