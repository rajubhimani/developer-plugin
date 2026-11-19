"""The item concept and its rules."""

from __future__ import annotations

from dataclasses import dataclass

MAX_NAME_LENGTH = 100


class InvalidItem(ValueError):
    """An item broke a business rule."""


@dataclass(frozen=True, slots=True)
class Item:
    """A stored item."""

    id: int
    name: str


def clean_name(name: str) -> str:
    """Return the name trimmed, or raise InvalidItem if it breaks the rules."""
    cleaned = name.strip()
    if not cleaned:
        raise InvalidItem("name must not be empty")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise InvalidItem(f"name must be at most {MAX_NAME_LENGTH} characters")
    return cleaned
