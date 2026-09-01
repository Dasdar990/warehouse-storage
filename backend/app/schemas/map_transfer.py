"""
Pydantic schema for exporting/importing the *entire* warehouse map (zones,
racks, walls, doors) as a single JSON file, instead of saving/loading each
piece separately through /zones, /shelves/config and /room-layout.
"""
from pydantic import BaseModel, Field

from app.schemas.room import DoorOut, WallOut
from app.schemas.shelf import ShelfNodeOut
from app.schemas.zone import ZoneOut

# Bumped whenever the bundle's shape changes in a way that would make an
# older file unsafe to import as-is, so `import_map` can reject it with a
# clear error instead of silently misreading fields.
MAP_EXPORT_VERSION = 1


class MapBundle(BaseModel):
    """
    A full snapshot of the map config page: zones, racks, and the room
    outline (walls + doors).

    The `id` fields on `zones` and `nodes` are only meaningful *within this
    file*: a rack's `zone_id` points at a zone's `id` elsewhere in the same
    bundle. On import, zones and racks are recreated from scratch with new
    database ids, and `zone_id` references are remapped accordingly --
    they are never reused as real database ids.
    """

    version: int = MAP_EXPORT_VERSION
    zones: list[ZoneOut] = Field(default_factory=list)
    nodes: list[ShelfNodeOut] = Field(default_factory=list)
    walls: list[WallOut] = Field(default_factory=list)
    doors: list[DoorOut] = Field(default_factory=list)
