"""Health routes for the orchestrator's probes.

Liveness answers "is the process stuck?" and checks nothing else. Readiness answers
"can it take traffic now?": it runs the checks the composition root registered (the
database ping). Never put a dependency check in liveness: an outage elsewhere would
restart healthy pods (see the kubernetes skill).
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from {{package}}.api.errors import problem

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/healthz")
def liveness() -> dict[str, str]:
    """The process is up."""
    return {"status": "ok"}


@router.get("/readyz")
def readiness(request: Request) -> JSONResponse:
    """The service can take traffic; 503 while a dependency is unavailable."""
    checks: list[Callable[[], None]] = request.app.state.readiness_checks
    for check in checks:
        try:
            check()
        except Exception:
            # Any failure means not ready; the detail goes to the log, not the response.
            logger.warning("readiness check failed", exc_info=True)
            return problem(503, "Not ready", "a dependency is unavailable")
    return JSONResponse({"status": "ready"})
