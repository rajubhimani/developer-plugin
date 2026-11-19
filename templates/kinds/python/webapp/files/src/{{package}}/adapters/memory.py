"""In-memory storage: for tests and the first run. Replace with a database adapter."""

from __future__ import annotations

from {{package}}.domain.items import Item


class InMemoryItemRepository:
    """Implements ItemRepository with a list. Not shared between processes."""

    def __init__(self) -> None:
        self._items: list[Item] = []

    def add(self, name: str) -> Item:
        """Store a new item."""
        item = Item(id=len(self._items) + 1, name=name)
        self._items.append(item)
        return item

    def all(self) -> list[Item]:
        """Return every item."""
        return list(self._items)
