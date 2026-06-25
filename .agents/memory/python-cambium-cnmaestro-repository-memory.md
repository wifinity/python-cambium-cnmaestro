# python-cambium-cnmaestro repository memory

## What this repo is

Minimal Python SDK for Cambium cnMaestro.

- **API base**: `https://{base_url}/api/v2`
- **Scope tracker**: `docs/endpoint-checklist.md` (cross-checked against the bundled OpenAPI spec)

## Architecture (layers)

- **Client entry point**: `cambium_cnmaestro/client.py`
  - `CnMaestroClient` wires the token provider + HTTP client + resources.
- **Auth**: `cambium_cnmaestro/auth.py`
  - OAuth2 client-credentials token:
    - `POST /access/token`
    - HTTP Basic auth using `client_id:client_secret`
    - form body `grant_type=client_credentials`
  - Token is cached in-memory; cleared on 401/403.
- **HTTP**: `cambium_cnmaestro/http.py`
  - `httpx.Client`
  - Retries on transport errors; exponential backoff
  - 429: uses `RateLimit-Reset` or `Retry-After` headers
  - Error mapping:
    - 401/403 -> `CnMaestroAuthError` (and clears token cache)
    - 404 -> `CnMaestroNotFoundError`
    - other >=400 -> `CnMaestroHTTPError` (includes status + response text)
    - 204 -> returns `None`
- **Errors**: `cambium_cnmaestro/errors.py`
- **Operations**: `cambium_cnmaestro/operations/*`
  - Pure helpers for CLI polling and cnMatrix CLI output parsing.
- **Resources**: `cambium_cnmaestro/resources/*`
  - Thin wrappers around REST endpoints; return raw decoded JSON (`Any`).

## Resource conventions

- Public resource methods are **keyword-only** (`def method(self, *, ...)`).
- CRUD names follow HTTP verbs: `list`, `get`, `create`, `update`, `delete`.
- Request bodies are passed as a single dict argument named after the entity:
  - `device`, `network`, `site`, `wlan`, `ap_group`, `switch_group`, `ports`, etc.
- Do not introduce Pydantic/dataclass models unless doing so consistently across the SDK.
- “Operations” helpers (e.g. lookup by alternate key, create-or-update) should be added explicitly
  on top of CRUD without changing CRUD semantics.

## Operation helpers

Higher-level helpers layered on top of REST CRUD wrappers:

- Devices:
  - `DevicesResource.find(mac=..., msn=...)` (unwraps single-item paging envelope; raises on ambiguous MSN)
  - `DevicesResource.get_status(mac=..., msn=...)` (projects `online`, `profile_attached`, `config.sync_status`)
  - `DevicesResource.upsert(device=..., mac=..., msn=...)`
    - resolve by MAC first, then MSN search
    - create requires `type` + `msn`, sets `approved=True`, strips `overrides` on create (cnMaestro quirk)
    - soft-success: some HTTP 500 messages are returned as `UpsertResult(status=423, ...)`
  - `DevicesResource.bulk_upsert(updates=...)` (each item: `config`/`device`, optional `mac`/`msn`)
  - `DevicesResource.get_interfaces(mac=..., msn=...)`
    - triggers `show interfaces` CLI, polls until complete, parses into NAPALM-like interface fields
    - TextFSM template in `textfsm_templates/cnmatrix_show_interfaces.textfsm`
    - `Interface.speed`: float Mbit (e.g. `1 Gbps` -> `1000.0`, `100 Mbps` -> `100.0`)
    - `Interface.last_flapped`: `-1.0` when unknown/never; otherwise UNIX timestamp float from `Last transition: ... UTC ...`
    - poll helper in `operations/cli.py`
- Networks:
  - `NetworksResource.find(name=...)`
  - `NetworksResource.upsert(network=...)` (no-op when network exists; cnMaestro update is unreliable)
- Sites:
  - `SitesResource.find(network_id=..., name=...)`
  - `SitesResource.upsert(network_id=..., site=...)`
- WiFi enterprise:
  - `WLANsResource.find(name=...)` + `WLANsResource.upsert(wlan=...)`
  - `APGroupsResource.find(name=...)` + `APGroupsResource.upsert(ap_group=..., wlans=...)`
    - optional `wlans` list merged into request body for call-site convenience
- Switch groups / cnMatrix ports:
  - `SwitchGroupsResource.find(name=...)`
  - `SwitchGroupsResource.upsert(switch_group=...)` (GET then PUT/POST)
  - `PortsResource.update(ports=...)` (maps to `cnmaestro.put.cnmatrix.ports`)
  - `SwitchGroupsPortsResource.list_for_switch_group(...)` / `get_for_device(...)`
- Jobs:
  - `JobsResource.list(type=...)` (type is required: 'software'|'configuration')
  - `JobsResource.get(job_id=...)`
  - `JobsResource.get_details(job_id=...)`
  - `JobsResource.get_status(job_id=...)` → `JobStatus` (state, type, device counts, raw)
  - `JobStatus.state` observed values: 'Processing', 'Running', 'Completed', 'Failed'
  - `PUT /devices/{mac}` returns a `device.commit` body with `job_id`/`state` — only device config push spawns a pollable job; ports and switch_group PUTs return only `{message: "Success"}`

## Implemented REST endpoint groups (as of today)

See `docs/endpoint-checklist.md` for the authoritative list. Current resources include:

- `devices.py`: `/devices` + `/devices/{mac}` + `/devices/{mac}/cli`
- `networks.py`: `/networks` + `/networks/{name}`
- `sites.py`: `/networks/{network_id}/sites/*`
- `wifi_enterprise.py`: `/wifi_enterprise/wlans/*`, `/wifi_enterprise/ap_groups/*`
- `cnmatrix.py`:
  - `/cnmatrix/switch_groups/*`
  - `/cnmatrix/switch_groups_ports/*`
  - `PUT /cnmatrix/ports`
- `jobs.py`: `GET /jobs` (requires `type` param), `GET /jobs/{job_id}`, `GET /jobs/{job_id}/details`

## Tests

- `tests/test_smoke.py` contains a minimal smoke test.
- Operation helper tests live in:
  - `tests/test_paging.py`
  - `tests/test_devices_operations.py`
  - `tests/test_devices_interface_macs.py`
  - `tests/test_switch_groups_operations.py`
  - `tests/test_cnmatrix_ports.py`
  - `tests/test_cnmatrix_interface_parse.py`
  - `tests/test_networks_operations.py`
  - `tests/test_sites_operations.py`
  - `tests/test_wifi_enterprise_operations.py`
  - `tests/test_jobs_operations.py`
- When adding tests, prefer **pytest-httpx** (already included in `pyproject.toml` dev extras) to mock:
  - token acquisition (`POST /api/v2/access/token`)
  - each endpoint request/response
  - error conditions (401/403, 404, 429, 5xx)
