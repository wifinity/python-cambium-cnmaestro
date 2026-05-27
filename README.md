# cambium-cnmaestro

Python SDK for Cambium cnMaestro.

## Installation

```bash
pip install cambium-cnmaestro
```

## Quickstart

```python
from cambium_cnmaestro import CnMaestroClient

client = CnMaestroClient(
    base_url="https://cnmaestro.example.com",
    client_id="...",
    client_secret="...",
)

devices = client.devices.list()
```

