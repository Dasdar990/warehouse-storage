"""
Stock movement logic: mutates an item's quantity and writes a matching
`Movement` audit-log row in the same transaction, so the two can never
drift apart.
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.movement import Movement, MovementAction, MovementSource
from app.schemas.movement import StockMoveRequest


def _get_item_by_barcode(db: Session, barcode: str) -> Item:
    item = db.execute(select(Item).where(Item.barcode == barcode)).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found for barcode '{barcode}'")
    return item


def withdraw_stock(db: Session, payload: StockMoveRequest) -> tuple[Item, Movement]:
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
    movement = _log_movement(db, item, MovementAction.WITHDRAW, payload)
    db.commit()
    db.refresh(item)
    db.refresh(movement)
    return item, movement


def deposit_stock(db: Session, payload: StockMoveRequest) -> tuple[Item, Movement]:
    """Increase stock (restock / put-away confirmation)."""
    item = _get_item_by_barcode(db, payload.barcode)

    item.quantity += payload.quantity
    movement = _log_movement(db, item, MovementAction.DEPOSIT, payload)
    db.commit()
    db.refresh(item)
    db.refresh(movement)
    return item, movement


def _log_movement(
    db: Session, item: Item, action: MovementAction, payload: StockMoveRequest
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
        operator=payload.operator.strip() or "Operatore",
    )
    db.add(movement)
    return movement


def list_recent_movements(db: Session, limit: int = 50) -> list[Movement]:
    stmt = select(Movement).order_by(Movement.timestamp.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())
