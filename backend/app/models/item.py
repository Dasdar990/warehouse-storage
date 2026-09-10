"""SQLAlchemy ORM models for the Warehouse Storage backend."""
import enum

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Enum as SAEnum

from app.db import Base


class ItemSize(str, enum.Enum):
    """Physical size classification used for shelving/handling decisions."""

    SMALL = "small"
    BIG = "big"
    XL = "xl"


class Item(Base):
    """A single inventory item identified by a unique scannable barcode."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    pn = Column(String, index=True, nullable=False, default="")
    serial = Column(String, index=True, nullable=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    program = Column(String, index=True, nullable=True)
    size = Column(SAEnum(ItemSize, native_enum=False,
                  length=16), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    shelf_position = Column(String, index=True, nullable=False)
    zone_id = Column(Integer, ForeignKey(
        "zones.id", ondelete="SET NULL"), nullable=True)
    tags = Column(String, nullable=True)
    notes = Column(String, nullable=True)