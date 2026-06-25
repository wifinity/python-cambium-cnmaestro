from __future__ import annotations

from .auth import ClientCredentialsTokenProvider
from .http import CnMaestroHTTPClient
from .resources.cnmatrix import CnMatrixResource
from .resources.devices import DevicesResource
from .resources.jobs import JobsResource
from .resources.networks import NetworksResource
from .resources.sites import SitesResource
from .resources.wifi_enterprise import WiFiEnterpriseResource


class CnMaestroClient:
    def __init__(
        self,
        *,
        base_url: str,
        client_id: str,
        client_secret: str,
        ssl_verify: bool = True,
        timeout_seconds: float = 30.0,
        api_prefix: str = "/api/v2",
    ) -> None:
        token_provider = ClientCredentialsTokenProvider(
            base_url=base_url,
            client_id=client_id,
            client_secret=client_secret,
            ssl_verify=ssl_verify,
            timeout_seconds=timeout_seconds,
        )
        http = CnMaestroHTTPClient(
            base_url=base_url,
            token_provider=token_provider,
            ssl_verify=ssl_verify,
            timeout_seconds=timeout_seconds,
            api_prefix=api_prefix,
        )

        self._token_provider = token_provider
        self._http = http

        self.devices = DevicesResource(http)
        self.networks = NetworksResource(http)
        self.sites = SitesResource(http)
        self.wifi_enterprise = WiFiEnterpriseResource(http)
        self.cnmatrix = CnMatrixResource(http)
        self.jobs = JobsResource(http)

    def __enter__(self) -> CnMaestroClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.close()

    def close(self) -> None:
        self._http.close()
