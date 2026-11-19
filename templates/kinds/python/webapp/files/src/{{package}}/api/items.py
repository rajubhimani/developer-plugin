"""Item routes: an example resource. Replace with your own, keeping routes thin."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from {{package}}.services.items import ItemService

router = APIRouter(prefix="/items", tags=["items"])


class ItemIn(BaseModel):
    """Request body for creating an item."""

    name: str


class ItemOut(BaseModel):
    """An item as the API returns it. Separate from the domain type on purpose."""

    id: int
    name: str


def get_service(request: Request) -> ItemService:
    """Provide the service built by the composition root."""
    service: ItemService = request.app.state.items
    return service


Service = Annotated[ItemService, Depends(get_service)]


@router.post("", status_code=201)
def create_item(body: ItemIn, service: Service) -> ItemOut:
    """Create an item."""
    item = service.create(body.name)
    return ItemOut(id=item.id, name=item.name)


@router.get("")
def list_items(service: Service) -> list[ItemOut]:
    """List items."""
    return [ItemOut(id=i.id, name=i.name) for i in service.list_items()]
