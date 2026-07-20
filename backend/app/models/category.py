"""SQLAlchemy ORM model for the admin-managed item category catalog."""
from sqlalchemy import Column, Integer, String

from app.db import Base


class Category(Base):
    """A named category available for selection when creating an item.

    This is a small managed catalog (created/deleted from the admin
    Categories page) that populates the dropdown on the item creation
    form. `Item.category` itself stays a free-text column so existing
    items are never invalidated by deleting a category later.
    """

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
