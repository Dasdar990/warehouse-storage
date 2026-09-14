"""Pydantic request/response schemas for the category catalog."""
from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=60, description='e.g. "Fasteners"')

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        return value


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    """Rename an existing category. Renaming also updates the free-text
    `category` value on every item currently using the old name, so the
    catalog and the item list stay in sync (see category_service.update_category)."""

    pass


class CategoryOut(CategoryBase):
    id: int

    class Config:
        from_attributes = True
