"""Composition root: the one place that builds the app and wires the layers together.

Run with `uvicorn --factory {{package}}.main:create_app`. A factory does no work at
import time, so tests and tools can import this module freely.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI

from {{package}}.adapters.sql import SqlItemRepository, make_engine
from {{package}}.api import errors, health, items
from {{package}}.services.items import ItemRepository, ItemService
from {{package}}.settings import Settings, get_settings


def create_app(
    settings: Settings | None = None, repository: ItemRepository | None = None
) -> FastAPI:
    """Build the application.

    Tests pass settings and an in-memory repository; production reads the settings from the
    environment and stores items in the database. Swap the adapter here without touching
    services or domain.
    """
    settings = settings or get_settings()
    app = FastAPI(title="{{title}}")
    app.state.settings = settings
    checks: list[Callable[[], None]] = []
    if repository is None:
        sql = SqlItemRepository(make_engine(settings.database_url.get_secret_value()))
        repository = sql
        checks.append(sql.ping)  # readiness fails while the database is unreachable
    app.state.readiness_checks = checks
    app.state.items = ItemService(repository)
    errors.install(app)
    app.include_router(health.router)
    app.include_router(items.router)
    return app
