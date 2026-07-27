"""
Stock movement logic: mutates an item's quantity and writes a matching
`Movement` audit-log row in the same transaction, so the two can never
drift apart.
"""
from datetime import date, datetime, time

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.timezone import APP_TZ
from app.models.item import Item
from app.models.movement import Movement, MovementAction, MovementSource
from app.schemas.movement import RelocateItemRequest, StockMoveRequest


def _get_item_by_barcode(db: Session, barcode: str) -> Item:
    item = db.execute(select(Item).where(Item.barcode == barcode)).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found for barcode '{barcode}'")
    return item


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
    movement = _log_movement(db, item, MovementAction.WITHDRAW, payload, operator=operator)
    db.commit()
    db.refresh(item)
    db.refresh(movement)
    return item, movement


def deposit_stock(db: Session, payload: StockMoveRequest, *, operator: str) -> tuple[Item, Movement]:
    """Increase stock (restock / put-away confirmation)."""
    item = _get_item_by_barcode(db, payload.barcode)

    item.quantity += payload.quantity
    movement = _log_movement(db, item, MovementAction.DEPOSIT, payload, operator=operator)
    db.commit()
    db.refresh(item)
    db.refresh(movement)
    return item, movement


def move_item(db: Session, payload: RelocateItemRequest, *, operator: str) -> tuple[Item, Movement]:
    """Relocate an item to a different shelf; quantity is untouched."""
    item = _get_item_by_barcode(db, payload.barcode)
    destination = payload.shelf_position.strip().upper()

    if not destination:
        raise HTTPException(status_code=400, detail="Destination shelf can't be empty")
    if destination == item.shelf_position:
        raise HTTPException(status_code=400, detail=f"'{item.name}' is already on shelf {destination}")

    origin = item.shelf_position
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
        source=payload.source if isinstance(payload.source, MovementSource) else MovementSource(payload.source),
        operator=operator.strip() or "Operator",
    )
    db.add(movement)
    db.commit()
    db.refresh(item)
    db.refresh(movement)
    return item, movement


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
        source=payload.source if isinstance(payload.source, MovementSource) else MovementSource(payload.source),
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
        stmt = stmt.where(or_(Movement.item_name.ilike(needle), Movement.pn.ilike(needle)))
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
        stmt = stmt.where(Movement.timestamp >= datetime.combine(date_from, time.min, tzinfo=APP_TZ))
    if date_to is not None:
        stmt = stmt.where(Movement.timestamp <= datetime.combine(date_to, time.max, tzinfo=APP_TZ))
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
        raise HTTPException(status_code=404, detail=f"No movement found with id {movement_id}")
    if original.voided:
        raise HTTPException(status_code=400, detail="This movement has already been rolled back")
    if original.reversal_of_id is not None:
        raise HTTPException(status_code=400, detail="A rollback itself can't be rolled back")
    if original.item_id is None:
        raise HTTPException(
            status_code=400,
            detail="The item this movement belongs to no longer exists, so it can't be rolled back",
        )

    item = db.get(Item, original.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="The item this movement belongs to no longer exists")

    # Reversing a WITHDRAW puts stock back (DEPOSIT); reversing a DEPOSIT
    # takes it back out (WITHDRAW), and must not push stock negative if
    # some of it has since been withdrawn again by something else.
    # Reversing a MOVE sends the item back to its origin shelf instead;
    # quantity is untouched either way.
    if original.action == MovementAction.MOVE:
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
    db.add(reversal)
    original.voided = True

    db.commit()
    db.refresh(item)
    db.refresh(original)
    db.refresh(reversal)
    return item, reversal
