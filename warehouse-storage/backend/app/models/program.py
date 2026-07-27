"""SQLAlchemy ORM model for the admin-managed program catalog."""
from sqlalchemy import Column, Integer, String

from app.db import Base


class Program(Base):
    """A named program available for (optional) selection when creating an item.

    Mirrors `Category`: a small managed catalog (created/deleted from the
    admin Programs page) that populates the dropdown on the item creation
    form. `Item.program` itself stays a free-text, nullable column so
    existing items are never invalidated by deleting a program later.
    """

    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
