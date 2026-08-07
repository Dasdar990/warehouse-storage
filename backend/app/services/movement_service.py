"""
Stock movement logic: mutates an item's quantity and writes a matching
`Movement` audit-log row in the same transaction, so the two can never
drift apart.
"""
from datetime import date, datetime, time
import json

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.timezone import APP_TZ
from app.models.item import Item, ItemSize
from app.models.movement import Movement, MovementAction, MovementSource
from app.schemas.movement import BulkMoveRequest, RelocateItemRequest, StockMoveRequest
from app.services.shelf_service import get_shelf_node
from app.services.barcode_generator import generate_unique_barcode


def _get_item_by_barcode(db: Session, barcode: str) -> Item:
    item = db.execute(select(Item).where(
        Item.barcode == barcode)).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"No item found for barcode '{barcode}'")
    return item


def _find_or_create_destination(db: Session, source: Item, destination: str) -> Item:
    """
    Find the item that a cross-shelf deposit or partial move should land on
    at `destination`: an existing row for the same part number if one is
    already there, otherwise a freshly-created item (starting at quantity 0,
    topped up by the caller) so the stock has somewhere to go.

    Items with no P/N can't be reliably matched to "the same part" on
    another shelf, so those always get a brand-new row rather than risking
    a merge into an unrelated item that just happens to share a shelf.
    """
    target = None
    if source.pn:
        target = db.execute(
            select(Item).where(
                Item.shelf_position == destination,
                Item.pn == source.pn,
                Item.id != source.id,
            )
        ).scalar_one_or_none()

    if target is None:
        target = Item(
            name=source.name,
            pn=source.pn,
            # Deliberately not copied: a serial identifies one specific
            # physical unit, and that unit is staying with its original row.
            serial=None,
            barcode=generate_unique_barcode(db),
            category=source.category,
            program=source.program,
            size=source.size,
            shelf_position=destination,
            quantity=0,
        )
        db.add(target)
        db.flush()  # assign target.id so the audit-log row below can reference it

    return target


def _clear_shelf_if_empty(item: Item) -> None:
    """
    An item that's been fully withdrawn no longer occupies physical space,
    so free its shelf slot (empty string, same "unassigned" sentinel used
    elsewhere) rather than leaving a stale position on an empty item. It'll
    need an explicit Move once it's put away somewhere again.
    """
    if item.quantity <= 0:
        item.shelf_position = ""


def withdraw_stock(db: Session, payload: StockMoveRequest, *, operator: str) -> tuple[Item, Movement]:
    """Decrease stock; refuses to let quantity go negative."""
    item = _get_item_by_barcode(db, payload.barcode)

    if payload.quantity > item.quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock: requested {payload.quantity}, "
                f"only {item.quantity} available"
            ),
        )

    item.quantity -= payload.quantity
    movement = _log_movement(
        db, item, MovementAction.WITHDRAW, payload, operator=operator)
    _clear_shelf_if_empty(item)
    db.commit()
    db.refresh(item)
    db.refresh(movement)
    return item, movement


def deposit_stock(db: Session, payload: StockMoveRequest, *, operator: str) -> tuple[Item, Movement, bool]:
    """
    Increase stock (restock / put-away confirmation).

    By default deposits onto the scanned/selected item's own shelf. If
    `payload.shelf_position` names a *different* shelf, the deposit is
    redirected there instead -- topping up a matching item if one already
    exists on that shelf, or creating a new one -- while the original item
    is left completely untouched. Returns whether the deposit was redirected
    like this, so the caller can word its response accordingly.
    """
    item = _get_item_by_barcode(db, payload.barcode)

    destination = (payload.shelf_position or "").strip().upper()
    redirected = bool(destination) and destination != item.shelf_position
    target = _find_or_create_destination(
        db, item, destination) if redirected else item

    target.quantity += payload.quantity
    movement = _log_movement(
        db, target, MovementAction.DEPOSIT, payload, operator=operator)
    db.commit()
    db.refresh(target)
    db.refresh(movement)
    return target, movement, redirected


def log_edit_item(
    db: Session, item: Item, changes: dict[str, list], *, operator: str
) -> Movement:
    """
    Log an EDIT movement for an already-modified Item row, recording what
    actually changed.

    `changes` is `{field: [old_value, new_value]}` for every field that
    differs -- this is what makes the entry both meaningful to read in the
    Activity Log and possible to roll back (see rollback_movement), unlike
    a bare "item was edited" note with no record of the previous values.
    Doesn't commit -- the caller (update_item) does, in the same
    transaction as the field changes themselves.
    """
    movement = Movement(
        item_id=item.id,
        item_name=item.name,
        pn=item.pn,
        shelf_position=item.shelf_position,
        action=MovementAction.EDIT,
        quantity=item.quantity,
        balance_after=item.quantity,
        source=MovementSource.MANUAL,
        operator=operator.strip() or "Operator",
        field_changes=json.dumps(changes, default=str),
    )
    db.add(movement)
    return movement


def move_item(db: Session, payload: RelocateItemRequest, *, operator: str) -> tuple[Item, Movement, bool]:
    """
    Relocate stock to a different shelf.

    Moving the item's *entire* current quantity (the default, if
    `payload.quantity` is omitted) behaves exactly as before: the same item
    row just gets a new `shelf_position`, quantity untouched.

    Moving a smaller quantity splits the stock instead: the source keeps
    the remainder on its current shelf, and the moved quantity either tops
    up a matching item already on the destination shelf or creates a new
    one there. Returns whether this was a full relocation (vs. a split),
    so the caller can word its response accordingly.
    """
    item = _get_item_by_barcode(db, payload.barcode)
    destination = payload.shelf_position.strip().upper()

    if not destination:
        raise HTTPException(
            status_code=400, detail="Destination shelf can't be empty")
    if destination == item.shelf_position:
        raise HTTPException(
            status_code=400, detail=f"'{item.name}' is already on shelf {destination}")

    move_qty = payload.quantity if payload.quantity is not None else item.quantity
    if move_qty > item.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {item.quantity} unit(s) of '{item.name}' available to move",
        )

    origin = item.shelf_position
    source = payload.source if isinstance(
        payload.source, MovementSource) else MovementSource(payload.source)
    clean_operator = operator.strip() or "Operator"

    if move_qty == item.quantity:
        # Full relocation: same row, just a new shelf.
        item.shelf_position = destination
        movement = Movement(
            item_id=item.id,
            item_name=item.name,
            pn=item.pn,
            shelf_position=destination,
            from_shelf_position=origin,
            action=MovementAction.MOVE,
            quantity=item.quantity,
            balance_after=item.quantity,
            source=source,
            operator=clean_operator,
        )
        db.add(movement)
        db.commit()
        db.refresh(item)
        db.refresh(movement)
        return item, movement, True

    # Partial move: shrink the source, grow (or create) the destination.
    item.quantity -= move_qty
    target = _find_or_create_destination(db, item, destination)
    target.quantity += move_qty
    movement = Movement(
        item_id=target.id,
        item_name=target.name,
        pn=target.pn,
        shelf_position=destination,
        from_shelf_position=origin,
        action=MovementAction.MOVE,
        quantity=move_qty,
        balance_after=target.quantity,
        source=source,
        operator=clean_operator,
        split_from_item_id=item.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(item)
    db.refresh(target)
    db.refresh(movement)
    return item, movement, False


def _log_movement(
    db: Session, item: Item, action: MovementAction, payload: StockMoveRequest, *, operator: str
) -> Movement:
    movement = Movement(
        item_id=item.id,
        item_name=item.name,
        pn=item.pn,
        shelf_position=item.shelf_position,
        action=action,
        quantity=payload.quantity,
        balance_after=item.quantity,
        source=payload.source if isinstance(
            payload.source, MovementSource) else MovementSource(payload.source),
        operator=operator.strip() or "Operator",
    )
    db.add(movement)
    return movement


def list_recent_movements(
    db: Session,
    limit: int = 50,
    *,
    operator: str | None = None,
    item_id: int | None = None,
    item: str | None = None,
    action: MovementAction | None = None,
    source: MovementSource | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Movement]:
    stmt = select(Movement).order_by(Movement.timestamp.desc())
    if operator:
        stmt = stmt.where(Movement.operator.ilike(f"%{operator.strip()}%"))
    if item_id is not None:
        stmt = stmt.where(Movement.item_id == item_id)
    if item:
        needle = f"%{item.strip()}%"
        stmt = stmt.where(or_(Movement.item_name.ilike(
            needle), Movement.pn.ilike(needle)))
    if action is not None:
        stmt = stmt.where(Movement.action == action)
    if source is not None:
        stmt = stmt.where(Movement.source == source)
    # Filters come in as plain calendar dates picked by the operator (e.g.
    # "27/07/2026" in the UI) -- they mean *that day in Rome*, so the day
    # boundaries must be anchored to Europe/Rome, not UTC. Otherwise, during
    # CEST (UTC+2), the first/last 2 hours of a Rome day would be filtered
    # using the wrong calendar day.
    if date_from is not None:
        stmt = stmt.where(Movement.timestamp >= datetime.combine(
            date_from, time.min, tzinfo=APP_TZ))
    if date_to is not None:
        stmt = stmt.where(Movement.timestamp <= datetime.combine(
            date_to, time.max, tzinfo=APP_TZ))
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def rollback_movement(db: Session, movement_id: int, *, operator: str) -> tuple[Movement, Movement]:
    """
    Undo a past movement (admin-only, see routers/movements.py).

    Does not edit or delete the original row -- it's flagged `voided` and a
    brand-new, opposite movement is written pointing back at it via
    `reversal_of_id`, so the audit log stays a complete, append-only record
    of everything that happened, including the rollback itself.
    """
    original = db.get(Movement, movement_id)
    if original is None:
        raise HTTPException(
            status_code=404, detail=f"No movement found with id {movement_id}")
    if original.voided:
        raise HTTPException(
            status_code=400, detail="This movement has already been rolled back")
    if original.reversal_of_id is not None:
        raise HTTPException(
            status_code=400, detail="A rollback itself can't be rolled back")
    if original.item_id is None:
        raise HTTPException(
            status_code=400,
            detail="The item this movement belongs to no longer exists, so it can't be rolled back",
        )

    item = db.get(Item, original.item_id)
    if item is None:
        raise HTTPException(
            status_code=404, detail="The item this movement belongs to no longer exists")

    # Reversing a WITHDRAW puts stock back (DEPOSIT); reversing a DEPOSIT
    # takes it back out (WITHDRAW), and must not push stock negative if
    # some of it has since been withdrawn again by something else.
    # Reversing a full MOVE sends the item back to its origin shelf instead;
    # quantity is untouched either way. A *split* move (see move_item) is
    # different again: it touched two items' quantities, not one item's
    # shelf, so it needs its own reversal that moves the quantity back.
    if original.action == MovementAction.MOVE and original.split_from_item_id is not None:
        origin_item = db.get(Item, original.split_from_item_id)
        if origin_item is None:
            raise HTTPException(
                status_code=400,
                detail="The shelf this quantity was split from no longer exists, so it can't be rolled back",
            )
        if original.quantity > item.quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Can't roll back: would require removing {original.quantity} from shelf "
                    f"{item.shelf_position}, only {item.quantity} currently there"
                ),
            )
        item.quantity -= original.quantity
        origin_item.quantity += original.quantity
        reversal = Movement(
            item_id=origin_item.id,
            item_name=origin_item.name,
            pn=origin_item.pn,
            shelf_position=origin_item.shelf_position,
            from_shelf_position=item.shelf_position,
            action=MovementAction.MOVE,
            quantity=original.quantity,
            balance_after=origin_item.quantity,
            source=MovementSource.MANUAL,
            operator=operator.strip() or "Operator",
            reversal_of_id=original.id,
        )
        db.add(reversal)
        original.voided = True
        db.commit()
        db.refresh(item)
        db.refresh(origin_item)
        db.refresh(original)
        db.refresh(reversal)
        return origin_item, reversal
    elif original.action == MovementAction.EDIT:
        if not original.field_changes:
            raise HTTPException(
                status_code=400,
                detail="This edit has no recorded changes to roll back",
            )
        changes: dict[str, list] = json.loads(original.field_changes)
        reverse_changes: dict[str, list] = {}
        for field, (old_value, _new_value) in changes.items():
            current_value = getattr(item, field)
            restored = ItemSize(old_value) if field == "size" and old_value is not None else old_value
            setattr(item, field, restored)
            reverse_changes[field] = [current_value, restored]
        reversal = Movement(
            item_id=item.id,
            item_name=item.name,
            pn=item.pn,
            shelf_position=item.shelf_position,
            action=MovementAction.EDIT,
            quantity=item.quantity,
            balance_after=item.quantity,
            source=MovementSource.MANUAL,
            operator=operator.strip() or "Operator",
            reversal_of_id=original.id,
            field_changes=json.dumps(reverse_changes, default=str),
        )
        db.add(reversal)
        original.voided = True
        db.commit()
        db.refresh(item)
        db.refresh(original)
        db.refresh(reversal)
        return item, reversal
    elif original.action == MovementAction.MOVE:
        reverse_action = MovementAction.MOVE
        origin = item.shelf_position
        item.shelf_position = original.from_shelf_position or origin
        reversal = Movement(
            item_id=item.id,
            item_name=item.name,
            pn=item.pn,
            shelf_position=item.shelf_position,
            from_shelf_position=origin,
            action=reverse_action,
            quantity=item.quantity,
            balance_after=item.quantity,
            source=MovementSource.MANUAL,
            operator=operator.strip() or "Operator",
            reversal_of_id=original.id,
        )
    else:
        if original.action == MovementAction.WITHDRAW:
            reverse_action = MovementAction.DEPOSIT
            item.quantity += original.quantity
        else:
            reverse_action = MovementAction.WITHDRAW
            if original.quantity > item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Can't roll back: would require removing {original.quantity}, "
                        f"only {item.quantity} currently in stock"
                    ),
                )
            item.quantity -= original.quantity

        reversal = Movement(
            item_id=item.id,
            item_name=item.name,
            pn=item.pn,
            shelf_position=item.shelf_position,
            action=reverse_action,
            quantity=original.quantity,
            balance_after=item.quantity,
            source=MovementSource.MANUAL,
            operator=operator.strip() or "Operator",
            reversal_of_id=original.id,
        )
        if reverse_action == MovementAction.WITHDRAW:
            _clear_shelf_if_empty(item)
    db.add(reversal)
    original.voided = True

    db.commit()
    db.refresh(item)
    db.refresh(original)
    db.refresh(reversal)
    return item, reversal


def bulk_move(db: Session, payload: BulkMoveRequest, *, operator: str) -> tuple[int, int, str]:
    """
    Relocate everything on a shelf, or an entire rack, in one shot.

    'shelf' mode moves every item currently at `from_code` to `to_code`
    (both plain shelf positions like '12B'). 'rack' mode moves every level
    of the `from_code` rack to the matching level (by order) on the
    `to_code` rack -- e.g. rack "12"'s levels A,B,C,D map onto rack "9"'s
    A,B,C,D. The destination rack must have at least as many levels as the
    source, so nothing is left with nowhere to go.

    Unlike `move_item`, there's no merge-or-create step: a shelf position
    already holds however many items happen to be there (that's normal --
    see ShelfDetailPanel), so items just get their `shelf_position`
    reassigned directly. Each moved item gets its own MOVE audit-log row.
    """
    clean_operator = operator.strip() or "Operator"
    source_code = payload.from_code.strip().upper()
    dest_code = payload.to_code.strip().upper()

    if source_code == dest_code:
        raise HTTPException(
            status_code=400, detail="Source and destination are the same")

    if payload.mode == "shelf":
        pairs = [(source_code, dest_code)]
    else:
        source_rack = get_shelf_node(db, source_code)
        dest_rack = get_shelf_node(db, dest_code)
        if source_rack is None:
            raise HTTPException(
                status_code=404, detail=f"Rack '{source_code}' not found")
        if dest_rack is None:
            raise HTTPException(
                status_code=404, detail=f"Rack '{dest_code}' not found")

        src_levels = [lvl for lvl in (
            source_rack.levels or "").split(",") if lvl]
        dst_levels = [lvl for lvl in (
            dest_rack.levels or "").split(",") if lvl]
        if len(dst_levels) < len(src_levels):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Rack '{dest_code}' only has {len(dst_levels)} level(s), but "
                    f"'{source_code}' has {len(src_levels)} -- pick a rack with at least as many levels"
                ),
            )
        pairs = [
            (f"{source_rack.rack_code}{s_lvl}", f"{dest_rack.rack_code}{d_lvl}")
            for s_lvl, d_lvl in zip(src_levels, dst_levels)
        ]

    moved_items = 0
    moved_quantity = 0
    for src_pos, dst_pos in pairs:
        if src_pos == dst_pos:
            continue
        shelf_items = list(db.execute(select(Item).where(
            Item.shelf_position == src_pos)).scalars().all())
        for item in shelf_items:
            item.shelf_position = dst_pos
            movement = Movement(
                item_id=item.id,
                item_name=item.name,
                pn=item.pn,
                shelf_position=dst_pos,
                from_shelf_position=src_pos,
                action=MovementAction.MOVE,
                quantity=item.quantity,
                balance_after=item.quantity,
                source=payload.source,
                operator=clean_operator,
            )
            db.add(movement)
            moved_items += 1
            moved_quantity += item.quantity

    if moved_items == 0:
        noun = "Shelf" if payload.mode == "shelf" else "Rack"
        raise HTTPException(
            status_code=400, detail=f"{noun} '{source_code}' has no items to move")

    db.commit()

    if payload.mode == "shelf":
        message = f"Moved {moved_items} item(s) ({moved_quantity} unit(s)) from shelf {source_code} to {dest_code}."
    else:
        message = f"Moved {moved_items} item(s) ({moved_quantity} unit(s)) from rack {source_code} to rack {dest_code}."

    return moved_items, moved_quantity, message
