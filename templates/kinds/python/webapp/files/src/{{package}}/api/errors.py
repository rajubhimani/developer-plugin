"""One error format for every failure: problem details (media type application/problem+json).

Responses carry a title, a status and a short detail, never a stack trace, a query
or any internal value (see the api-design and error-handling skills).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from {{package}}.domain.items import InvalidItem

PROBLEM = "application/problem+json"


def problem(status: int, title: str, detail: str | None = None, **extra: object) -> JSONResponse:
    """Build a problem-details response."""
    body: dict[str, object] = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM)


def install(app: FastAPI) -> None:
    """Register the handlers that turn exceptions into problem responses."""

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return problem(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [
            {"field": ".".join(str(part) for part in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return problem(422, "Invalid request", errors=fields)

    @app.exception_handler(InvalidItem)
    async def invalid_item(_: Request, exc: InvalidItem) -> JSONResponse:
        return problem(422, "Invalid item", str(exc))
