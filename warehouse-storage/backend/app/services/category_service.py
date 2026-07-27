"""Manages the admin-curated category catalog used by the item creation form."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


def list_categories(db: Session) -> list[Category]:
    """All categories, alphabetically -- populates the item form's dropdown."""
    return list(db.execute(select(Category).order_by(Category.name)).scalars().all())


def get_category_by_name(db: Session, name: str) -> Category | None:
    return db.execute(select(Category).where(Category.name == name)).scalar_one_or_none()


def create_category(db: Session, name: str) -> Category:
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> bool:
    """Remove a category from the catalog. Existing items keep their (free-text) category value."""
    category = db.get(Category, category_id)
    if category is None:
        return False
    db.delete(category)
    db.commit()
    return True
