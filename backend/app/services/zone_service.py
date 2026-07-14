"""Manages the user-drawn warehouse map zones (delimited areas on the canvas)."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.zone import Zone
from app.schemas.zone import ZoneBase


def list_zones(db: Session) -> list[Zone]:
    """All zones saved from the map config page, in creation order."""
    return list(db.execute(select(Zone).order_by(Zone.id)).scalars().all())


def replace_zones(db: Session, zones: list[ZoneBase]) -> list[Zone]:
    """
    Persist the full set of zones in one shot, replacing whatever was saved
    before. Racks that referenced a deleted zone fall back to no zone
    (handled by the ON DELETE SET NULL foreign key).
    """
    db.execute(delete(Zone))
    db.flush()

    created: list[Zone] = []
    for zone in zones:
        row = Zone(
            name=zone.name,
            color=zone.color,
            x=zone.x,
            y=zone.y,
            width=zone.width,
            height=zone.height,
        )
        db.add(row)
        created.append(row)

    db.commit()
    for row in created:
        db.refresh(row)
    return created
