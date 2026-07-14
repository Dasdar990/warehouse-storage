"""
Warehouse-map endpoints: the full grid + aggregates (for the homepage map),
per-rack mensole breakdown, per-mensola contents (for the click-through
drill-down), and the freeform rack layout CRUD used by the drag-and-drop
configuration page. Zone CRUD lives in routers/zones.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.item import Item
from app.schemas.item import ItemOut
from app.schemas.shelf import (
    RackLevelsResponse,
    ShelfItemsResponse,
    ShelfNodeOut,
    WarehouseLayout,
    WarehouseMapSave,
)
from app.services.shelf_service import (
    build_rack_levels,
    build_warehouse_layout,
    list_shelf_nodes_out,
    replace_shelf_layout,
)

router = APIRouter(prefix="/shelves", tags=["shelves"])


@router.get("", response_model=WarehouseLayout)
def get_warehouse_layout(db: Session = Depends(get_db)):
    """
    Grid dimensions plus per-shelf item counts/quantities/categories, used
    to render and color the interactive warehouse map. Includes the
    user-drawn freeform layout (zones + racks) if one has been saved.
    """
    return build_warehouse_layout(db)


@router.get("/config", response_model=list[ShelfNodeOut])
def get_shelf_layout(db: Session = Depends(get_db)):
    """Raw list of rack boxes as saved from the drag-and-drop config page."""
    return list_shelf_nodes_out(db)


@router.put("/config", response_model=list[ShelfNodeOut])
def save_shelf_layout(payload: WarehouseMapSave, db: Session = Depends(get_db)):
    """
    Replace the entire rack layout in one shot (what the config page's
    "Save layout" button sends). Saving an empty list of nodes clears the
    custom layout and reverts the homepage map to the auto-generated grid.
    """
    try:
        return replace_shelf_layout(db, payload.nodes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{rack_code}/levels", response_model=RackLevelsResponse)
def get_rack_levels(rack_code: str, db: Session = Depends(get_db)):
    """A rack's mensole with live stock aggregates (drill-down when a rack is clicked)."""
    result = build_rack_levels(db, rack_code)
    if result is None:
        raise HTTPException(status_code=404, detail=f'Rack "{rack_code}" is not on the saved map')
    return result


@router.get("/{shelf_position}/items", response_model=ShelfItemsResponse)
def get_shelf_items(shelf_position: str, db: Session = Depends(get_db)):
    """All items currently stored on a given mensola (drill-down when a level is clicked)."""
    items = (
        db.execute(select(Item).where(Item.shelf_position == shelf_position.upper()))
        .scalars()
        .all()
    )
    return ShelfItemsResponse(
        shelf_position=shelf_position.upper(),
        items=[ItemOut.model_validate(i) for i in items],
    )
