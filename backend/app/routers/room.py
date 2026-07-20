"""Warehouse-map room outline endpoints: the walls + door drawn on the config page canvas."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.room import RoomLayoutOut, RoomLayoutSave
from app.services.room_service import get_room_layout, replace_room_layout

router = APIRouter(prefix="/room-layout", tags=["room-layout"])


@router.get("", response_model=RoomLayoutOut)
def read_room_layout(db: Session = Depends(get_db)):
    """Raw walls + door as drawn on the map config page."""
    return get_room_layout(db)


@router.put("", response_model=RoomLayoutOut)
def save_room_layout(payload: RoomLayoutSave, db: Session = Depends(get_db)):
    """
    Replace the entire room outline in one shot (what the config page's
    "Save layout" button sends).
    """
    return replace_room_layout(db, payload.walls, payload.doors)
