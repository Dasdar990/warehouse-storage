"""
Full-map export/import endpoints: download or restore zones + racks +
room outline as a single JSON file, from the map config page's
Export/Import buttons. Admin-only since import replaces the entire map.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db import get_db
from app.schemas.map_transfer import MapBundle
from app.services.map_transfer_service import export_map, import_map

router = APIRouter(prefix="/map", tags=["map-transfer"], dependencies=[Depends(require_admin)])


@router.get("/export", response_model=MapBundle)
def export_map_bundle(db: Session = Depends(get_db)):
    """Everything on the map (zones, racks, walls, doors) as one JSON bundle."""
    return export_map(db)


@router.post("/import", response_model=MapBundle)
def import_map_bundle(payload: MapBundle, db: Session = Depends(get_db)):
    """
    Replace the entire map with the contents of an exported bundle.
    Returns the freshly re-read map so the caller can confirm what was
    actually saved.
    """
    try:
        return import_map(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
