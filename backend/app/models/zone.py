"""SQLAlchemy ORM model for warehouse map zones.

A Zone is a purely organizational/visual rectangle drawn on the map canvas
to delimit an area of the physical warehouse (e.g. "Zona ricambi motore").
Zones have no functional link to items -- they exist so the map can group
racks visually. A rack (Shelf) may optionally reference a zone.
"""
from sqlalchemy import Column, Float, Integer, String

from app.db import Base


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
