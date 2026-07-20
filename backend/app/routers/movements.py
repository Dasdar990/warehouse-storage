"""Live stock-movement audit log endpoint (powers the ActivityLog feed)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.movement import MovementOut
from app.services.movement_service import list_recent_movements

router = APIRouter(prefix="/movements", tags=["movements"])


@router.get("", response_model=list[MovementOut])
def get_recent_movements(
    limit: int = Query(default=50, ge=1, le=200, description="Max rows to return, most recent first"),
    db: Session = Depends(get_db),
):
    """Most recent deposit/withdraw events, newest first."""
    return list_recent_movements(db, limit=limit)
