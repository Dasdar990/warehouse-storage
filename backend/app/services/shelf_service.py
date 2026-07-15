"""
Builds the warehouse-map grid (shelf numbers x level letters) and
aggregates item data per shelf so the frontend can color/label each cell
without pulling the entire inventory on every page load.

Also manages the user-drawn, freeform map layout: `Zone` areas and `Shelf`
rows (each a rack/"scaffale" with one or more levels/"mensole") placed via
the drag-and-drop config page, merged with live stock aggregates.

Hierarchy on the freeform map: Zone (visual grouping only) -> Shelf/rack
(clickable, e.g. rack "12") -> mensola/level (clickable, e.g. "12B") ->
items. Mensole are not a DB table: they're derived by combining a rack's
`rack_code` with each letter in its `levels` column, and matched against
`Item.shelf_position` (free text, e.g. "12B").
"""
import re

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.item import Item
from app.models.shelf import Shelf
from app.schemas.shelf import (
    MensolaSummary,
    RackLevelsResponse,
    ShelfMapNode,
    ShelfNodeBase,
    ShelfNodeOut,
    ShelfSummary,
    WarehouseLayout,
)
from app.services.zone_service import list_zones

settings = get_settings()

_SHELF_SPLIT_PATTERN = re.compile(r"^(\d+)([A-Za-z])$")


def _split_shelf_position(shelf_position: str) -> tuple[int, str]:
    match = _SHELF_SPLIT_PATTERN.match(shelf_position)
    if not match:
        # Defensive fallback -- data is validated on write, but don't let a
        # legacy/odd value crash the whole map.
        return 0, "?"
    number, level = match.groups()
    return int(number), level.upper()


def _levels_to_str(levels: list[str]) -> str:
    return ",".join(levels)


def _levels_from_str(raw: str) -> list[str]:
    return [lvl for lvl in (raw or "").split(",") if lvl]


def list_shelf_nodes(db: Session) -> list[Shelf]:
    """All rack boxes saved from the drag-and-drop config page, in creation order."""
    return list(db.execute(select(Shelf).order_by(Shelf.id)).scalars().all())


def _shelf_to_node_out(shelf: Shelf) -> ShelfNodeOut:
    """Converts the ORM row (levels stored as a comma string) to the API schema (levels as a list)."""
    return ShelfNodeOut(
        id=shelf.id,
        rack_code=shelf.rack_code,
        label=shelf.label,
        x=shelf.x,
        y=shelf.y,
        width=shelf.width,
        height=shelf.height,
        levels=_levels_from_str(shelf.levels),
        zone_id=shelf.zone_id,
        rotation=shelf.rotation,
    )


def list_shelf_nodes_out(db: Session) -> list[ShelfNodeOut]:
    """API-shaped version of `list_shelf_nodes`, for the /shelves/config endpoints."""
    return [_shelf_to_node_out(shelf) for shelf in list_shelf_nodes(db)]


def get_shelf_node(db: Session, rack_code: str) -> Shelf | None:
    return db.execute(
        select(Shelf).where(Shelf.rack_code == rack_code.strip().upper())
    ).scalar_one_or_none()


def replace_shelf_layout(db: Session, nodes: list[ShelfNodeBase]) -> list[ShelfNodeOut]:
    """
    Persist the full map layout in one shot: whatever the editor's canvas
    holds when "Save layout" is clicked becomes the new layout, replacing
    whatever was saved before. Passing an empty list clears the custom
    layout and reverts the map to the auto-generated grid.
    """
    codes = [node.rack_code for node in nodes]
    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate rack codes are not allowed on the map")

    zone_ids = {z.id for z in list_zones(db)}
    for node in nodes:
        if node.zone_id is not None and node.zone_id not in zone_ids:
            raise ValueError(f'Rack "{node.rack_code}" references an unknown zone')

    db.execute(delete(Shelf))
    db.flush()

    created: list[Shelf] = []
    for node in nodes:
        shelf = Shelf(
            rack_code=node.rack_code,
            label=node.label,
            x=node.x,
            y=node.y,
            width=node.width,
            height=node.height,
            levels=_levels_to_str(node.levels),
            zone_id=node.zone_id,
            rotation=node.rotation,
        )
        db.add(shelf)
        created.append(shelf)

    db.commit()
    for shelf in created:
        db.refresh(shelf)
    return [_shelf_to_node_out(shelf) for shelf in created]


def _aggregate(items: list[Item]) -> dict:
    return {
        "item_count": len(items),
        "total_quantity": sum(i.quantity for i in items),
        "categories": sorted({i.category for i in items}),
        "has_low_stock": any(i.quantity <= settings.low_stock_threshold for i in items),
    }


def build_warehouse_layout(db: Session) -> WarehouseLayout:
    items = db.execute(select(Item)).scalars().all()

    by_shelf: dict[str, list[Item]] = {}
    for item in items:
        by_shelf.setdefault(item.shelf_position, []).append(item)

    # The fallback grid always includes the configured default size, but
    # expands to cover any real data that falls outside of it (e.g. a shelf
    # 25C when only 20 shelves are configured).
    max_shelf_number = settings.warehouse_shelf_count
    levels = set(settings.warehouse_levels)

    parsed: dict[str, tuple[int, str]] = {}
    for shelf_position in by_shelf:
        number, level = _split_shelf_position(shelf_position)
        parsed[shelf_position] = (number, level)
        max_shelf_number = max(max_shelf_number, number)
        levels.add(level)

    shelf_numbers = list(range(1, max_shelf_number + 1))
    sorted_levels = sorted(levels)

    shelves: list[ShelfSummary] = []
    for shelf_position, shelf_items in by_shelf.items():
        number, level = parsed[shelf_position]
        agg = _aggregate(shelf_items)
        shelves.append(
            ShelfSummary(
                shelf_position=shelf_position,
                shelf_number=number,
                level=level,
                item_count=agg["item_count"],
                total_quantity=agg["total_quantity"],
                categories=agg["categories"],
                has_low_stock=agg["has_low_stock"],
            )
        )

    shelf_nodes = list_shelf_nodes(db)
    nodes: list[ShelfMapNode] = []
    for shelf in shelf_nodes:
        rack_levels = _levels_from_str(shelf.levels)
        rack_items = [
            item
            for lvl in rack_levels
            for item in by_shelf.get(f"{shelf.rack_code}{lvl}", [])
        ]
        agg = _aggregate(rack_items)
        nodes.append(
            ShelfMapNode(
                rack_code=shelf.rack_code,
                label=shelf.label,
                x=shelf.x,
                y=shelf.y,
                width=shelf.width,
                height=shelf.height,
                levels=rack_levels,
                zone_id=shelf.zone_id,
                rotation=shelf.rotation,
                item_count=agg["item_count"],
                total_quantity=agg["total_quantity"],
                categories=agg["categories"],
                has_low_stock=agg["has_low_stock"],
            )
        )

    zones = list_zones(db)

    return WarehouseLayout(
        shelf_numbers=shelf_numbers,
        levels=sorted_levels,
        low_stock_threshold=settings.low_stock_threshold,
        shelves=shelves,
        has_custom_layout=len(nodes) > 0,
        nodes=nodes,
        zones=zones,
    )


def build_rack_levels(db: Session, rack_code: str) -> RackLevelsResponse | None:
    """Per-level ("mensola") stock breakdown for one rack, shown after a rack is clicked."""
    shelf = get_shelf_node(db, rack_code)
    if shelf is None:
        return None

    rack_levels = _levels_from_str(shelf.levels)
    result: list[MensolaSummary] = []
    for level in rack_levels:
        shelf_position = f"{shelf.rack_code}{level}"
        shelf_items = list(
            db.execute(select(Item).where(Item.shelf_position == shelf_position)).scalars().all()
        )
        agg = _aggregate(shelf_items)
        result.append(
            MensolaSummary(
                shelf_position=shelf_position,
                level=level,
                item_count=agg["item_count"],
                total_quantity=agg["total_quantity"],
                categories=agg["categories"],
                has_low_stock=agg["has_low_stock"],
            )
        )

    return RackLevelsResponse(rack_code=shelf.rack_code, label=shelf.label, levels=result)
