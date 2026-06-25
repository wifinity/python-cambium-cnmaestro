# Agent guide — python-cambium-cnmaestro

## What this repo is

Minimal Python SDK for Cambium cnMaestro REST API (`/api/v2`). Thin resource
wrappers return raw decoded JSON; higher-level operation helpers sit on top for
workflow-friendly upsert/find/poll patterns. Does **not** own workflows or
NetBox integration.

## Package layout (`cambium_cnmaestro/`)

| Path | Purpose |
|------|---------|
| `cambium_cnmaestro/client.py` | `CnMaestroClient` — wires auth, HTTP, resources |
| `cambium_cnmaestro/auth.py` | OAuth2 client-credentials token (in-memory cache) |
| `cambium_cnmaestro/http.py` | `httpx` client, retries, error mapping |
| `cambium_cnmaestro/errors.py` | `CnMaestroAuthError`, `CnMaestroNotFoundError`, etc. |
| `cambium_cnmaestro/resources/` | Thin REST wrappers (`devices`, `networks`, `sites`, `wifi_enterprise`, `cnmatrix`, `jobs`) |
| `cambium_cnmaestro/operations/` | CLI polling and cnMatrix interface parsing helpers |
| `cambium_cnmaestro/paging.py` | Paging envelope helpers |
| `cambium_cnmaestro/textfsm_templates/` | TextFSM for cnMatrix `show interfaces` |

Repo root: `tests/`, `docs/`, `Makefile`, `pyproject.toml`.

## Conventions

- **Resources are thin wrappers** over cnMaestro REST endpoints; return raw JSON (`Any`).
- **Public methods are keyword-only** (`def method(self, *, ...)`) with one explicit body argument (`device`, `network`, `site`, etc.).
- **Method naming aligns to HTTP verbs**: `list`, `get`, `create`, `update`, `delete`.
- **Avoid SDK-wide modeling** unless introduced consistently across the entire SDK.
- **Keep CRUD semantics stable**; add lookup/upsert as explicit operation methods on top.

## Operations helpers

When changing these, update `docs/endpoint-checklist.md` (Operations helpers),
`.agents/memory/python-cambium-cnmaestro-repository-memory.md`, and tests.

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
- `client.jobs.get_status(job_id=...)` → `JobStatus` (state, type, device counts, raw)

## Where to look

- **Endpoint scope:** [endpoint-checklist.md](endpoint-checklist.md)
- **Index:** [INDEX.md](INDEX.md)
- **Memory:** [.agents/memory/python-cambium-cnmaestro-repository-memory.md](../.agents/memory/python-cambium-cnmaestro-repository-memory.md)
- **ADR:** [adr/0001-repo-structure-to-date.md](adr/0001-repo-structure-to-date.md)

## Starting a new task

1. Read `.agents/memory/python-cambium-cnmaestro-repository-memory.md`.
2. Check `docs/endpoint-checklist.md` for implemented endpoints.
3. Run `make tests` before opening a PR.

## Testing

- Full suite: `make tests` (alias `make test`); targets: `make lint`, `make typecheck`, `make unit-tests`.
- Tests in `tests/` with `pytest`; prefer **pytest-httpx** for HTTP mocking.
- Cover token acquisition, happy path, and error mapping (401/403, 404, 429, 4xx/5xx).
