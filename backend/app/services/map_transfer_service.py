"""
Export/import the full warehouse map (zones, racks, walls, doors) as one
JSON bundle -- a backup/restore or copy-to-another-instance path, separate
from the piecewise /zones, /shelves/config, /room-layout CRUD used by the
config page's own "Save layout" buttons.
"""
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.room import Door, Wall
from app.models.shelf import Shelf
from app.models.zone import Zone
from app.schemas.map_transfer import MAP_EXPORT_VERSION, MapBundle
from app.schemas.room import DoorOut, WallOut
from app.schemas.zone import ZoneOut
from app.services.room_service import get_room_layout
from app.services.shelf_service import list_shelf_nodes_out
from app.services.zone_service import list_zones


def export_map(db: Session) -> MapBundle:
    """Everything currently on the map, in one downloadable bundle."""
    room = get_room_layout(db)
    return MapBundle(
        version=MAP_EXPORT_VERSION,
        zones=[ZoneOut.model_validate(z) for z in list_zones(db)],
        nodes=list_shelf_nodes_out(db),
        walls=[WallOut.model_validate(w) for w in room.walls],
        doors=[DoorOut.model_validate(d) for d in room.doors],
    )


def import_map(db: Session, bundle: MapBundle) -> MapBundle:
    """
    Replace the entire map (zones, racks, walls, doors) in one transaction.

    A rack's `zone_id` in the incoming file refers to a zone's `id`
    *elsewhere in that same file* -- since zones are recreated from scratch
    with new autoincrement ids, those references are remapped to the newly
    created rows rather than reused as real database ids.
    """
    if bundle.version != MAP_EXPORT_VERSION:
        raise ValueError(
            f"Unsupported map file version {bundle.version} (this app reads version {MAP_EXPORT_VERSION})"
        )

    codes = [node.rack_code for node in bundle.nodes]
    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate rack codes are not allowed on the map")

    file_zone_ids = {zone.id for zone in bundle.zones}
    for node in bundle.nodes:
        if node.zone_id is not None and node.zone_id not in file_zone_ids:
            raise ValueError(f'Rack "{node.rack_code}" references a zone not present in this file')

    db.execute(delete(Shelf))
    db.execute(delete(Zone))
    db.execute(delete(Wall))
    db.execute(delete(Door))
    db.flush()

    zone_id_map: dict[int, int] = {}
    for zone in bundle.zones:
        row = Zone(name=zone.name, color=zone.color, x=zone.x, y=zone.y, width=zone.width, height=zone.height)
        db.add(row)
        db.flush()  # need the new autoincrement id right away, to map later racks onto it
        zone_id_map[zone.id] = row.id

    for node in bundle.nodes:
        db.add(
            Shelf(
                rack_code=node.rack_code,
                label=node.label,
                x=node.x,
                y=node.y,
                width=node.width,
                height=node.height,
                levels=",".join(node.levels),
                zone_id=zone_id_map.get(node.zone_id) if node.zone_id is not None else None,
                rotation=node.rotation,
            )
        )

    for wall in bundle.walls:
        db.add(Wall(x=wall.x, y=wall.y, width=wall.width, height=wall.height, rotation=wall.rotation))

    for door in bundle.doors:
        db.add(Door(x=door.x, y=door.y, width=door.width, rotation=door.rotation))

    db.commit()

    return export_map(db)
