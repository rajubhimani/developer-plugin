"""SQL storage with SQLAlchemy: implements the ItemRepository port.

The only module that knows the table layout. Schema changes go through a migration
(migrations/versions), never through create_all in production.
"""

from __future__ import annotations

from sqlalchemy import Engine, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from {{package}}.domain.items import MAX_NAME_LENGTH, Item


class Base(DeclarativeBase):
    """Base class of the table models; Alembic reads its metadata."""


class ItemRow(Base):
    """The items table. A storage detail: the rest of the app sees `Item`."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_NAME_LENGTH))


def driver_url(url: str) -> str:
    """Name the PostgreSQL driver explicitly, so a plain `postgresql://` URL works."""
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def make_engine(url: str) -> Engine:
    """Create the engine. `pool_pre_ping` replaces connections the database dropped."""
    return create_engine(driver_url(url), pool_pre_ping=True)


class SqlItemRepository:
    """Implements ItemRepository on a SQLAlchemy engine."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._sessions = sessionmaker(engine, expire_on_commit=False)

    def add(self, name: str) -> Item:
        """Store a new item; the transaction commits when the block ends."""
        with self._sessions.begin() as session:
            row = ItemRow(name=name)
            session.add(row)
            session.flush()
            return Item(id=row.id, name=row.name)

    def all(self) -> list[Item]:
        """Return every item, oldest first."""
        with self._sessions() as session:
            rows = session.scalars(select(ItemRow).order_by(ItemRow.id))
            return [Item(id=row.id, name=row.name) for row in rows]

    def ping(self) -> None:
        """Raise if the database cannot be reached (used by the readiness route)."""
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))
