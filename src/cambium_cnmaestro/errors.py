from __future__ import annotations


class CnMaestroError(Exception):
    pass


class CnMaestroAuthError(CnMaestroError):
    pass


class CnMaestroRateLimitError(CnMaestroError):
    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class CnMaestroNotFoundError(CnMaestroError):
    pass


class CnMaestroHTTPError(CnMaestroError):
    def __init__(self, message: str, *, status_code: int | None = None, response_text: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
