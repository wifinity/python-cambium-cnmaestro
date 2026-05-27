# Endpoint checklist (StackStorm pack → SDK)

This checklist is derived from the existing StackStorm pack at `/Users/johan/git/st2/cnmaestro` and cross-checked against the OpenAPI spec in `cambium-cnmaestro-6.1.0-bundled.yaml`.

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
- [x] `PUT /networks/{name}` (StackStorm pack avoided update; validate server behavior in real env)

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

## Non-cnMaestro leftovers (do not port)

- [ ] `DELETE /dcim/cables/{{ id }}/` (NetBox-looking leftover in StackStorm pack; not in cnMaestro spec)

