"""The SQL adapter against an in-memory database, through the port it implements."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from {{package}}.adapters.sql import Base, SqlItemRepository, driver_url


@pytest.fixture
def repository() -> SqlItemRepository:
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)  # tests only; production uses migrations
    return SqlItemRepository(engine)


def test_add_assigns_ids_and_all_lists_in_order(repository: SqlItemRepository) -> None:
    first = repository.add("pen")
    second = repository.add("ink")
    assert (first.id, second.id) == (1, 2)
    assert [item.name for item in repository.all()] == ["pen", "ink"]


def test_ping_succeeds_when_the_database_answers(repository: SqlItemRepository) -> None:
    repository.ping()


def test_a_plain_postgresql_url_names_the_installed_driver() -> None:
    assert driver_url("postgresql://u:p@db/app") == "postgresql+psycopg://u:p@db/app"
    assert driver_url("sqlite:///x.db") == "sqlite:///x.db"
