"""SQLAlchemy ORM models for the Warehouse Storage backend."""
import enum

from sqlalchemy import Column, Enum as SAEnum, Integer, String

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
    # Optional manufacturer/unit serial number -- unlike `pn` (which identifies
    # the part type), this identifies one specific physical unit.
    serial = Column(String, index=True, nullable=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    # Optional, free-text like `category` -- populated from the admin-managed
    # Program catalog, but never invalidated if that catalog entry is deleted.
    program = Column(String, index=True, nullable=True)
    size = Column(SAEnum(ItemSize, native_enum=False,
                  length=16), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    # Alphanumeric shelf position, e.g. "12B" or "3A" (shelf number + level letter)
    shelf_position = Column(String, index=True, nullable=False)
