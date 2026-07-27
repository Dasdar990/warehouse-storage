"""SQLAlchemy ORM model for user-designed warehouse map layouts.

A `Shelf` row represents one physical rack drawn on the map
canvas by the drag-and-drop editor: its position/size (x/y/width/height),
which `Zone` it sits in (optional), and which levels it has.

Levels are stored as a comma-separated string of level letters (e.g.
"A,B,C,D"). Each level combined with the rack's `rack_code` reproduces the
free-text `Item.shelf_position` value used by the inventory (e.g. rack
"12" + level "B" -> item shelf_position "12B"), so items show up nested
under the right rack/level without a separate join table.
"""
from sqlalchemy import Column, Float, ForeignKey, Integer, String

from app.db import Base


class Shelf(Base):
    """A single rack positioned on the warehouse map canvas."""

    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, index=True)
    # Numeric rack identifier. Combined with a level letter it matches
    # Item.shelf_position values (e.g. rack_code "12" + level "B" -> "12B").
    # Not a strict FK on items since items can reference a rack/level before
    # it exists on the map, or vice versa.
    rack_code = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=True)
    x = Column(Float, nullable=False, default=0)
    y = Column(Float, nullable=False, default=0)
    width = Column(Float, nullable=False, default=90)
    height = Column(Float, nullable=False, default=140)
    # Comma-separated level letters for this rack's shelves, e.g. "A,B,C,D".
    levels = Column(String, nullable=False, default="A")
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    # Rotation in degrees, matching how the rack is physically oriented in
    # the room (set via the Konva transformer on the map editor canvas).
    rotation = Column(Float, nullable=False, default=0)
