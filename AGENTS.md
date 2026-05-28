# python-cambium-cnmaestro agent instructions

This repository is a minimal Python SDK for Cambium cnMaestro.

## Where to start

- **SDK entry point**: `cambium_cnmaestro/client.py` (`CnMaestroClient`)
- **Auth**: `cambium_cnmaestro/auth.py` (OAuth2 client credentials token)
- **HTTP**: `cambium_cnmaestro/http.py` (`httpx`, retries, error mapping)
- **Resources**: `cambium_cnmaestro/resources/` (thin REST wrappers)
- **Endpoint scope**: `docs/endpoint-checklist.md` (authoritative checklist)

## Conventions

- **Resources are thin wrappers** over cnMaestro REST endpoints and return raw decoded JSON (`Any`).
- **Public methods are keyword-only** (`def method(self, *, ...)`) and prefer one explicit body argument:
  - `device: dict[str, Any]`, `network: dict[str, Any]`, `switch_group: dict[str, Any]`, etc.
- **Method naming aligns to HTTP verbs**: `list`, `get`, `create`, `update`, `delete`.
- **Avoid SDK-wide modeling** unless you introduce it consistently across the entire SDK.
- **Keep CRUD semantics stable**. If you add higher-level behavior (e.g. lookup, create-or-update),
  add it as an explicit “operations” method layered on top of CRUD.

## Operations helpers

Higher-level helpers exist to provide workflow-friendly operations layered on top of CRUD wrappers. When changing these, update:

- `docs/endpoint-checklist.md` **Operations helpers** section
- `.agents/memory/python-cambium-cnmaestro-repository-memory.md`
- tests under `tests/`

Current operation methods:

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

## Testing

- Tests live in `tests/` and use `pytest` (see `pyproject.toml`).
- Prefer `pytest-httpx` for unit tests that assert HTTP request/response behavior.
- When adding or changing endpoints, add tests that cover:
  - token acquisition (`POST /api/v2/access/token`)
  - happy path response parsing
  - error mapping (401/403, 404, 429, other 4xx/5xx)

## Memory / repo notes

- Canonical agent memory lives under `.agents/memory/`.
- `.cursor/` exists only as a shim pointing to `.agents/` (do not duplicate memory content there).

