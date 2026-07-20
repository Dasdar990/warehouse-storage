"""Category catalog endpoints, managed from the admin Categories page and
consumed as a dropdown by the item creation form."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.category import CategoryCreate, CategoryOut
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """All categories in the catalog, alphabetically."""
    return category_service.list_categories(db)


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    """Add a new category to the catalog. Fails with 409 if the name already exists."""
    existing = category_service.get_category_by_name(db, payload.name)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f'Category "{payload.name}" already exists')
    return category_service.create_category(db, payload.name)


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Remove a category from the catalog. Items that already used it keep
    their category text -- only the dropdown option disappears.
    """
    deleted = category_service.delete_category(db, category_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No category found with id {category_id}")
