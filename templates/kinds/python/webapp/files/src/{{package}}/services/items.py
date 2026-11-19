"""Item use cases and the port (interface) they need from storage."""

from __future__ import annotations

from typing import Protocol

from {{package}}.domain.items import Item, clean_name


class ItemRepository(Protocol):
    """What the service needs from storage. Adapters implement it."""

    def add(self, name: str) -> Item:
        """Store a new item and return it with its id."""
        ...

    def all(self) -> list[Item]:
        """Return every item."""
        ...


class ItemService:
    """Use cases for items."""

    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    def create(self, name: str) -> Item:
        """Validate and store a new item."""
        return self._repository.add(clean_name(name))

    def list_items(self) -> list[Item]:
        """Return all items."""
        return self._repository.all()
