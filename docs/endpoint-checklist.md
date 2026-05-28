# Endpoint checklist (SDK scope)

This checklist tracks implemented SDK coverage and is cross-checked against the bundled OpenAPI spec in `cambium-cnmaestro-6.1.0-bundled.yaml`.

## Auth + base URL

- **Base URL**: `https://{base_url}/api/v2`
- **OAuth2 client credentials token**: `POST /access/token`
  - HTTP Basic: `client_id:client_secret`
  - Form body: `grant_type=client_credentials`
  - Response: `access_token`, `expires_in`

## Devices

- [x] `GET /devices`
- [x] `GET /devices/{mac}`
- [x] `POST /devices`
- [x] `PUT /devices/{mac}`
- [x] `DELETE /devices/{mac}`

## Device CLI

- [x] `GET /devices/{mac}/cli`
- [x] `POST /devices/{mac}/cli` (body includes `command`)

## Networks

- [x] `GET /networks`
- [x] `GET /networks/{name}`
- [x] `POST /networks`
- [x] `PUT /networks/{name}` (cnMaestro network update is unreliable; validate server behavior in real env)

## Sites (network scoped)

- [x] `GET /networks/{network_id}/sites/{name}`
- [x] `POST /networks/{network_id}/sites`
- [x] `PUT /networks/{network_id}/sites/{name}`

## WiFi enterprise

- [x] `GET /wifi_enterprise/wlans`
- [x] `GET /wifi_enterprise/wlans/{wlan_name}`
- [x] `POST /wifi_enterprise/wlans`
- [x] `PUT /wifi_enterprise/wlans/{wlan_name}`
- [x] `GET /wifi_enterprise/ap_groups`
- [x] `GET /wifi_enterprise/ap_groups/{ap_group_name}`
- [x] `POST /wifi_enterprise/ap_groups`
- [x] `PUT /wifi_enterprise/ap_groups/{ap_group_name}`

## cnMatrix

- [x] `GET /cnmatrix/switch_groups`
- [x] `GET /cnmatrix/switch_groups/{switch_group_name}`
- [x] `POST /cnmatrix/switch_groups`
- [x] `PUT /cnmatrix/switch_groups/{switch_group_name}`
- [x] `GET /cnmatrix/switch_groups_ports/{switch_group_name}`
- [x] `GET /cnmatrix/switch_groups_ports/{switch_group_name}/{device_mac}`
- [x] `PUT /cnmatrix/ports` (body includes `ports` array)

## Operations helpers

Higher-level helpers layered on top of CRUD wrappers (these are **SDK methods**, not REST endpoints):

- `client.devices.find(mac=..., msn=...)`
- `client.devices.get_status(mac=..., msn=...)`
- `client.devices.upsert(device=..., mac=..., msn=...)`
- `client.devices.bulk_upsert(updates=...)`
- `client.devices.get_interfaces(mac=..., msn=...)`
- `client.networks.upsert(network=...)`
- `client.sites.upsert(network_id=..., site=...)`
- `client.wifi_enterprise.wlans.upsert(wlan=...)`
- `client.wifi_enterprise.ap_groups.upsert(ap_group=..., wlans=...)`
- `client.cnmatrix.switch_groups.find(name=...)`
- `client.cnmatrix.switch_groups.upsert(switch_group=...)`
- `client.cnmatrix.ports.update(ports=...)`
- `client.cnmatrix.switch_groups_ports.list_for_switch_group(...)`

## Out-of-scope endpoints (do not add)

- [ ] `DELETE /dcim/cables/{{ id }}/` (NetBox-looking leftover; not in cnMaestro spec)

