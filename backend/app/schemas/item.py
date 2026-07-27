"""Pydantic request/response schemas for items."""
import re

from pydantic import BaseModel, Field, field_validator

from app.models.item import ItemSize

SHELF_POSITION_PATTERN = re.compile(r"^\d+[A-Za-z]$")


class ItemBase(BaseModel):
    name: str = Field(..., min_length=1,
                      description="Human readable item name")
    pn: str = Field(default="", description="Optional part number")
    serial: str | None = Field(
        default=None,
        description="Optional serial number identifying this specific unit",
    )
    barcode: str = Field(..., min_length=1,
                         description="Unique scannable barcode value")
    category: str = Field(..., min_length=1,
                          description="Product category, e.g. 'Fasteners'")
    program: str | None = Field(
        default=None, description="Optional program, e.g. 'Falcon Refit'"
    )
    size: ItemSize = Field(..., description="Physical size classification")
    shelf_position: str = Field(
        ..., description='Alphanumeric shelf position, e.g. "12B" or "3A"'
    )
    quantity: int = Field(
        default=0, ge=0, description="Current stock quantity")

    @field_validator("shelf_position")
    @classmethod
    def validate_shelf_position(cls, value: str) -> str:
        if not SHELF_POSITION_PATTERN.match(value):
            raise ValueError(
                'shelf_position must be alphanumeric like "12B" or "3A" '
                "(shelf number followed by a level letter)"
            )
        return value.upper()

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return value.strip()

    @field_validator("program")
    @classmethod
    def normalize_program(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("pn")
    @classmethod
    def normalize_pn(cls, value: str) -> str:
        return value.strip()

    @field_validator("serial")
    @classmethod
    def normalize_serial(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ItemCreate(ItemBase):
    pass


class ItemOut(ItemBase):
    id: int

    class Config:
        from_attributes = True


class BarcodeSuggestion(BaseModel):
    """A freshly generated, currently-unused barcode value the form can prefill."""

    barcode: str
