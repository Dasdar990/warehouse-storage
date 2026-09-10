"""SQLAlchemy ORM model for warehouse map zones.

A Zone is a rectangle drawn on the map canvas to delimit an area of the
physical warehouse (e.g. "Engine parts zone"). Two kinds:
- SHELF_GROUP (default): a purely visual grouping of racks. Items may not
  be placed directly on the zone -- they go on a shelf inside it.
- DIRECT_STORAGE: no racks inside; items are placed directly on the zone
  itself (no shelf_position).
"""

import enum

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy import Enum as SAEnum

from app.db import Base


class ZoneKind(str, enum.Enum):
    SHELF_GROUP = "shelf_group"
    DIRECT_STORAGE = "direct_storage"


class Zone(Base):
    """A named, colored rectangular area drawn on the warehouse map canvas."""

    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=False, default="#3b82f6")
    x = Column(Float, nullable=False, default=0)
    y = Column(Float, nullable=False, default=0)
    width = Column(Float, nullable=False, default=200)
    height = Column(Float, nullable=False, default=150)
    kind = Column(
        SAEnum(
            ZoneKind,
            native_enum=False,
            length=16,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=ZoneKind.SHELF_GROUP,
    )
