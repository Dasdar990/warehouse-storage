"""Pydantic request/response schemas for boxes."""

from pydantic import BaseModel, Field, field_validator

from app.schemas.item import SHELF_POSITION_PATTERN


class BoxBase(BaseModel):
    name: str | None = Field(
        default=None, description="Optional human label, e.g. 'Cavi HDMI'"
    )
    shelf_position: str = Field(
        ..., description='Shelf level the box sits on, e.g. "12B"'
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("shelf_position")
    @classmethod
    def normalize_shelf_position(cls, value: str) -> str:
        value = (value or "").strip()
        if not SHELF_POSITION_PATTERN.match(value):
            raise ValueError(
                'shelf_position must be alphanumeric like "12B" or "3A" '
                "(shelf number followed by a level letter)"
            )
        return value.upper()


class BoxCreate(BoxBase):
    pass


class BoxUpdate(BaseModel):
    """Rename a box or move it (with everything inside it) to a different shelf level."""

    name: str | None = None
    shelf_position: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("shelf_position")
    @classmethod
    def normalize_shelf_position(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not SHELF_POSITION_PATTERN.match(value):
            raise ValueError(
                'shelf_position must be alphanumeric like "12B" or "3A" '
                "(shelf number followed by a level letter)"
            )
        return value.upper()


class BoxOut(BoxBase):
    id: int
    code: str
    item_count: int = Field(
        default=0, description="Number of distinct item rows stored in this box"
    )
    total_quantity: int = Field(
        default=0, description="Sum of quantity across every item in this box"
    )

    class Config:
        from_attributes = True
