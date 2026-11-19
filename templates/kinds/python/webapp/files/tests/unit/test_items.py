"""Unit tests: business rules and use cases, with no web framework and no database."""

import pytest

from {{package}}.adapters.memory import InMemoryItemRepository
from {{package}}.domain.items import InvalidItem, clean_name
from {{package}}.services.items import ItemService


def test_clean_name_trims() -> None:
    assert clean_name("  pen ") == "pen"


@pytest.mark.parametrize("bad", ["", "   ", "x" * 101])
def test_clean_name_rejects_bad_names(bad: str) -> None:
    with pytest.raises(InvalidItem):
        clean_name(bad)


def test_service_stores_and_lists() -> None:
    service = ItemService(InMemoryItemRepository())
    created = service.create(" pen ")
    assert created.name == "pen"
    assert service.list_items() == [created]
