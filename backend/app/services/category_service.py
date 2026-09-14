"""Manages the admin-curated category catalog used by the item creation form."""
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.item import Item


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


def update_category(db: Session, category_id: int, name: str) -> Category | None:
    """Rename a category and cascade the new name onto every item that
    currently carries the old one, so `Item.category` (free text) never
    drifts out of sync with the catalog it was chosen from."""
    category = db.get(Category, category_id)
    if category is None:
        return None

    old_name = category.name
    if old_name == name:
        return category

    db.execute(
        update(Item).where(Item.category == old_name).values(category=name)
    )
    category.name = name
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
