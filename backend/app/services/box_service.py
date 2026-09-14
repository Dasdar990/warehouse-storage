"""
Manages storage boxes: containers for generic items that have no room for
their own printed label (e.g. loose cables). A box sits on one shelf level
and items inside it inherit that shelf_position, so every existing
shelf/map aggregate (build_warehouse_layout, build_rack_levels, the shelf
detail panel, ...) keeps working unmodified -- a boxed item still shows up
on its shelf, just tagged with which box it's actually in.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.box import Box
from app.models.item import Item
from app.schemas.box import BoxCreate, BoxUpdate
from app.services.movement_service import log_edit_item

CODE_DIGITS = 4


def _generate_unique_box_code(db: Session) -> str:
    max_id = db.execute(select(func.max(Box.id))).scalar()
    next_id = (max_id or 0) + 1
    return f"BOX-{next_id:0{CODE_DIGITS}d}"


def _aggregate(db: Session, box_id: int) -> tuple[int, int]:
    """(distinct item rows, total quantity) currently stored in this box."""
    row = db.execute(
        select(func.count(Item.id), func.coalesce(func.sum(Item.quantity), 0)).where(
            Item.box_id == box_id
        )
    ).one()
    return row[0], row[1]


def get_box_aggregate(db: Session, box_id: int) -> tuple[int, int]:
    """Public wrapper around `_aggregate` for callers outside this module (e.g. the router)."""
    return _aggregate(db, box_id)


def list_boxes(db: Session) -> list[tuple[Box, int, int]]:
    """Every box with its live item/quantity aggregates, newest first."""
    boxes = list(db.execute(select(Box).order_by(Box.id.desc())).scalars().all())
    return [(box, *_aggregate(db, box.id)) for box in boxes]


def get_box(db: Session, box_id: int) -> Box | None:
    return db.get(Box, box_id)


def create_box(db: Session, payload: BoxCreate) -> Box:
    box = Box(
        code=_generate_unique_box_code(db),
        name=payload.name,
        shelf_position=payload.shelf_position,
    )
    db.add(box)
    db.commit()
    db.refresh(box)
    return box


def update_box(db: Session, box: Box, payload: BoxUpdate, *, operator: str) -> Box:
    """
    Rename the box and/or move it (with everything inside it) to a
    different shelf level. Moving the box cascades its new shelf_position
    to every item currently inside it, each logged as its own EDIT
    movement -- from the Activity Log's point of view those items really
    did relocate, even though the operator only touched the box.
    """
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates:
        box.name = updates["name"]

    if "shelf_position" in updates and updates["shelf_position"] != box.shelf_position:
        old_shelf = box.shelf_position
        box.shelf_position = updates["shelf_position"]
        items = list(
            db.execute(select(Item).where(Item.box_id == box.id)).scalars().all()
        )
        for item in items:
            item.shelf_position = box.shelf_position
            log_edit_item(
                db,
                item,
                {"shelf_position": [old_shelf, box.shelf_position]},
                operator=operator,
            )

    db.commit()
    db.refresh(box)
    return box


def delete_box(db: Session, box: Box) -> None:
    """
    Refuses to delete a non-empty box -- silently orphaning its items'
    `box_id` would leave them pointing at nothing while still carrying the
    box's shelf_position, with no record of what happened to them. The
    caller should unassign (or relocate) the items first.
    """
    count, _ = _aggregate(db, box.id)
    if count > 0:
        raise ValueError(
            f'Box "{box.code}" still holds {count} item(s) -- remove them from the box first'
        )
    db.delete(box)
    db.commit()


def assign_item(db: Session, box: Box, item: Item, *, operator: str) -> Item:
    """Put `item` inside `box`, inheriting the box's shelf position and
    leaving any zone placement behind (boxes only live on shelves)."""
    changes: dict[str, list] = {}
    if item.box_id != box.id:
        changes["box"] = [item.box_id, box.id]
    if item.shelf_position != box.shelf_position:
        changes["shelf_position"] = [item.shelf_position, box.shelf_position]
    if item.zone_id is not None:
        changes["zone_id"] = [item.zone_id, None]

    item.box_id = box.id
    item.shelf_position = box.shelf_position
    item.zone_id = None

    if changes:
        log_edit_item(db, item, changes, operator=operator)
    db.commit()
    db.refresh(item)
    return item


def remove_item(db: Session, item: Item, *, operator: str) -> Item:
    """Take `item` out of its box. It stays on the same shelf_position the
    box was on -- it doesn't vanish, it's just loose on that shelf now."""
    if item.box_id is None:
        raise ValueError("This item isn't in a box")

    log_edit_item(db, item, {"box": [item.box_id, None]}, operator=operator)
    item.box_id = None

    db.commit()
    db.refresh(item)
    return item
