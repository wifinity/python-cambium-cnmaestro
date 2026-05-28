from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..errors import CnMaestroError


def poll_cli_until_complete(
    get_cli: Callable[[], Any],
    *,
    initial_delay_seconds: float = 10.0,
    poll_interval_seconds: float = 15.0,
    max_attempts: int = 3,
) -> str:
    time.sleep(initial_delay_seconds)

    for attempt in range(max_attempts):
        response = get_cli()
        raw_output = _extract_cli_output(response)
        if raw_output is not None:
            return raw_output

        if attempt < max_attempts - 1:
            time.sleep(poll_interval_seconds)

    raise CnMaestroError("CLI command did not complete within the polling window")


def _extract_cli_output(response: Any) -> str | None:
    if not isinstance(response, dict):
        raise CnMaestroError("Expected JSON object response for device CLI get")

    message = response.get("message")
    if not isinstance(message, dict):
        raise CnMaestroError("Expected message object in CLI response")

    status = message.get("status")
    if status != "complete":
        return None

    data = message.get("data")
    if isinstance(data, list):
        return "\n".join(str(line) for line in data)
    if isinstance(data, str):
        return data

    raise CnMaestroError("Expected message.data in completed CLI response")
