"""Run the database migrations: `python -m {{package}}.migrate [revision]`.

The migrations ship inside the package, so the same image that serves traffic can run
them as a one-shot job before a release (see the kubernetes skill). Migrations must be
backward compatible with the previous release (see the database-migrations skill).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from alembic import command
from alembic.config import Config

from {{package}}.adapters.sql import driver_url
from {{package}}.settings import get_migration_settings

MIGRATIONS = Path(__file__).parent / "migrations"


def alembic_config(url: str) -> Config:
    """Build the Alembic configuration in code; there is no alembic.ini to ship."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("sqlalchemy.url", driver_url(url).replace("%", "%%"))
    return config


def upgrade(url: str, revision: str = "head") -> None:
    """Bring the database at `url` up to `revision`."""
    command.upgrade(alembic_config(url), revision)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the migrations with the job's settings; return the exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    upgrade(get_migration_settings().database_url.get_secret_value(), args[0] if args else "head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
