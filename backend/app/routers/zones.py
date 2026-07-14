"""Warehouse-map zone endpoints: the delimited areas drawn on the config page canvas."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.zone import ZoneMapSave, ZoneOut
from app.services.zone_service import list_zones, replace_zones

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
def get_zones(db: Session = Depends(get_db)):
    """Raw list of zones as drawn on the map config page."""
    return list_zones(db)


@router.put("", response_model=list[ZoneOut])
def save_zones(payload: ZoneMapSave, db: Session = Depends(get_db)):
    """
    Replace the entire set of zones in one shot (what the config page's
    "Save layout" button sends). Racks belonging to a removed zone simply
    lose that association.
    """
    return replace_zones(db, payload.zones)
