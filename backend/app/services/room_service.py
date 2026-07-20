"""Manages the user-drawn room outline (walls + door) shown on the map canvas.

Purely visual/orientation context, same "replace the whole set in one
shot" pattern used for zones: there's no reason to diff individual walls
since the config page always saves its full, current canvas state.
"""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.room import Door, Wall
from app.schemas.room import DoorBase, RoomLayoutOut, WallBase


def get_room_layout(db: Session) -> RoomLayoutOut:
    """The room outline (walls + door) saved from the map config page."""
    walls = list(db.execute(select(Wall).order_by(Wall.id)).scalars().all())
    doors = list(db.execute(select(Door).order_by(Door.id)).scalars().all())
    return RoomLayoutOut(walls=walls, doors=doors)


def replace_room_layout(db: Session, walls: list[WallBase], doors: list[DoorBase]) -> RoomLayoutOut:
    """Persist the full room outline in one shot, replacing whatever was saved before."""
    db.execute(delete(Wall))
    db.execute(delete(Door))
    db.flush()

    created_walls: list[Wall] = []
    for wall in walls:
        row = Wall(x=wall.x, y=wall.y, width=wall.width, height=wall.height, rotation=wall.rotation)
        db.add(row)
        created_walls.append(row)

    created_doors: list[Door] = []
    for door in doors:
        row = Door(x=door.x, y=door.y, width=door.width, rotation=door.rotation)
        db.add(row)
        created_doors.append(row)

    db.commit()
    for row in created_walls:
        db.refresh(row)
    for row in created_doors:
        db.refresh(row)

    return RoomLayoutOut(walls=created_walls, doors=created_doors)
