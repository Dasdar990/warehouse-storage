"""SQLAlchemy ORM models for the warehouse room outline.

`Wall` and `Door` are purely visual/orientation aids drawn on the map
canvas: they have no functional link to items, racks, or zones. A wall is
a thin rectangle (x, y, width, height, rotation) — the same drag / resize /
rotate model already used for racks, so placing and reshaping a wall on
the canvas behaves exactly the same way. A door is a point along the
perimeter (its hinge) with a swing width and rotation, drawn as the
familiar architectural door-swing symbol so the layout reads at a glance.
"""
from sqlalchemy import Column, Float, Integer

from app.db import Base


class Wall(Base):
    """A single wall segment, drawn/dragged/resized/rotated as a thin rectangle."""

    __tablename__ = "walls"

    id = Column(Integer, primary_key=True, index=True)
    x = Column(Float, nullable=False, default=0)
    y = Column(Float, nullable=False, default=0)
    width = Column(Float, nullable=False, default=300)
    height = Column(Float, nullable=False, default=10)
    rotation = Column(Float, nullable=False, default=0)


class Door(Base):
    """A door marker (hinge point + swing width/rotation) on the map canvas."""

    __tablename__ = "doors"

    id = Column(Integer, primary_key=True, index=True)
    x = Column(Float, nullable=False, default=0)
    y = Column(Float, nullable=False, default=0)
    width = Column(Float, nullable=False, default=40)
    # Rotation in degrees, matching how the door opening is physically
    # oriented in the room (same convention as Shelf.rotation).
    rotation = Column(Float, nullable=False, default=0)
