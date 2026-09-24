"""Machine-readable error envelope `{code, message, details?}` (T011) — contracts/control-api.md.

One `ApiError` subclasses carries the whole contract: `code` is the JSON `code`, `status` is the
HTTP status, and `details` is the optional extra bag. Handlers are registered in `api/app.py`;
nothing else in the codebase raises `HTTPException` for a control-API error.
"""

import enum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# contracts/control-api.md "Error codes" — exactly these strings, no more.
VALIDATION_ERROR = "validation_error"
UNSUPPORTED_OPERATION = "unsupported_operation"
INVALID_CREDENTIALS = "invalid_credentials"
NOT_FOUND = "not_found"
RATE_LIMITED = "rate_limited"
SCENARIO_INVALID = "scenario_invalid"
SESSION_REQUIRED = "session_required"


class ErrorCode(enum.StrEnum):
    """The closed set of `code` values the control API may emit."""

    validation_error = VALIDATION_ERROR
    unsupported_operation = UNSUPPORTED_OPERATION
    invalid_credentials = INVALID_CREDENTIALS
    not_found = NOT_FOUND
    rate_limited = RATE_LIMITED
    scenario_invalid = SCENARIO_INVALID
    session_required = SESSION_REQUIRED


class ApiError(Exception):
    """Raise from any handler; the registered handler renders the envelope."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        status: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details

    def envelope(self) -> dict[str, Any]:
        """`details` is omitted entirely when unset — the contract says `details?`."""
        body: dict[str, Any] = {"code": self.code.value, "message": self.message}
        if self.details is not None:
            body["details"] = self.details
        return body


def not_found(what: str) -> ApiError:
    """The only 404 in the read API, so it gets a helper instead of a call-site status."""
    return ApiError(ErrorCode.not_found, f"{what} not found", status=404)


# Starlette raises 404/405 for unmatched routes; map every status we can hit onto a code so no
# response ever escapes in FastAPI's default `{"detail": ...}` shape.
_STATUS_CODES = {
    400: ErrorCode.validation_error,
    401: ErrorCode.invalid_credentials,
    403: ErrorCode.session_required,
    404: ErrorCode.not_found,
    405: ErrorCode.unsupported_operation,
    429: ErrorCode.rate_limited,
}


def install_error_handlers(app: FastAPI) -> None:
    """Register the envelope handlers. Called once by `app.py` at import."""

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.envelope())

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        # `str(e)` on a pydantic error list is non-JSON-safe; errors() is.
        return JSONResponse(
            status_code=422,
            content={
                "code": VALIDATION_ERROR,
                "message": "request validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _STATUS_CODES.get(exc.status_code, ErrorCode.unsupported_operation)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": code.value, "message": str(exc.detail)},
        )
