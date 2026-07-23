"""Live stock-movement audit log endpoint (powers the ActivityLog feed)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db import get_db
from app.models.user import User
from app.schemas.movement import MovementOut, RollbackResponse
from app.services.movement_service import list_recent_movements, rollback_movement

router = APIRouter(prefix="/movements", tags=["movements"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[MovementOut])
def get_recent_movements(
    limit: int = Query(default=50, ge=1, le=200, description="Max rows to return, most recent first"),
    operator: Optional[str] = Query(default=None, description="Case-insensitive partial match on operator name"),
    item_id: Optional[int] = Query(default=None, description="Only movements for this item (its full history)"),
    db: Session = Depends(get_db),
):
    """Most recent deposit/withdraw events, newest first. Optionally filtered by operator and/or item."""
    return list_recent_movements(db, limit=limit, operator=operator, item_id=item_id)


@router.post("/{movement_id}/rollback", response_model=RollbackResponse)
def rollback(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Admin-only: undo a past movement by writing an opposite compensating
    entry (see `rollback_movement`). No time limit -- any non-voided,
    non-reversal movement can be rolled back as long as the resulting
    stock wouldn't go negative.
    """
    item, reversal = rollback_movement(db, movement_id, operator=current_user.full_name)
    return RollbackResponse(
        item=item,
        reversal=reversal,
        message=f"Rolled back movement #{movement_id}: {reversal.action.value} {reversal.quantity} unit(s) of '{item.name}'.",
    )
