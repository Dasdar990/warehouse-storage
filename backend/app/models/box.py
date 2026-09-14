"""SQLAlchemy ORM model for storage boxes.

A Box is a physical container (e.g. a small bin) that lives on one shelf
level -- same granularity as an Item's `shelf_position` (rack code + level
letter, e.g. "12B"). It exists for generic items that don't have room for
their own printed label (loose parts like cables): the box gets one label
of its own, and items placed inside it point at it via `Item.box_id`
instead of carrying a useful label of their own. See Item.box_id and
routers/boxes.py for the assign/remove flow.
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base


class Box(Base):
    """A labeled container holding one or more generic items on a shelf level."""

    __tablename__ = "boxes"

    id = Column(Integer, primary_key=True, index=True)
    # Printed/scannable identifier, e.g. "BOX-0007". Auto-generated, unique.
    code = Column(String, unique=True, index=True, nullable=False)
    # Optional human-friendly name, e.g. "Cavi HDMI".
    name = Column(String, nullable=True)
    # Same format/meaning as Item.shelf_position (e.g. "12B"). Always
    # required -- boxes live on shelves, not loose in a zone (a zone-level
    # box would have nothing to visually anchor it to on the map).
    shelf_position = Column(String, index=True, nullable=False)

    items = relationship("Item", back_populates="box")
