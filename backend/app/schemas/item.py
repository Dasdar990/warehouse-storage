"""Pydantic request/response schemas for items."""
import re

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.item import ItemSize

SHELF_POSITION_PATTERN = re.compile(r"^\d+[A-Za-z]$")


def _normalize_tags(value) -> list[str]:
    """
    Accepts either a raw comma-separated string (how tags are stored on the
    ORM model, so this doubles as the read-path converter) or a list (how
    they arrive from the client on create/update). Either way: trimmed,
    de-duplicated case-insensitively (first-seen casing wins), empties and
    stray commas dropped.
    """
    if value is None:
        return []
    parts = value.split(",") if isinstance(value, str) else value
    seen: set[str] = set()
    result: list[str] = []
    for raw in parts:
        tag = str(raw).strip().replace(",", "")
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(tag)
    return result


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

    # 1. Cambiato il tipo in str | None e default in None
    shelf_position: str | None = Field(
        default=None,
        description='Alphanumeric shelf position, e.g. "12B" or "3A" -- null if the item has been fully withdrawn'
    )

    quantity: int = Field(
        default=0, ge=0, description="Current stock quantity")
    tags: list[str] = Field(
        default_factory=list,
        description="Free-form tags to help find this item later, e.g. ['spare', 'critical']",
    )
    notes: str | None = Field(
        default=None, description="Free-form notes to help find/identify this item later"
    )

    # 2. Aggiungi il normalizzatore per shelf_position in ItemBase
    @field_validator("shelf_position")
    @classmethod
    def normalize_shelf_position(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

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

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value) -> list[str]:
        return _normalize_tags(value)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ItemCreate(ItemBase):
    # A brand-new item only needs a shelf if it's starting out with actual
    # stock -- see require_shelf_if_stocked below. A zero-quantity item
    # (e.g. a catalog placeholder ordered but not yet received) can be
    # created without one and get shelved later via a deposit.

    @field_validator("shelf_position")
    @classmethod
    def validate_shelf_position(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return ""
        if not SHELF_POSITION_PATTERN.match(value):
            raise ValueError(
                'shelf_position must be alphanumeric like "12B" or "3A" '
                "(shelf number followed by a level letter)"
            )
        return value.upper()

    @model_validator(mode="after")
    def require_shelf_if_stocked(self):
        if self.quantity > 0 and not self.shelf_position:
            raise ValueError(
                "A shelf is required when the initial quantity is greater than zero -- "
                "only items starting at zero stock can be created without one"
            )
        return self


class ItemOut(ItemBase):
    id: int

    class Config:
        from_attributes = True


class ItemUpdate(BaseModel):
    """
    Shape for PATCH /items/{id}: edit descriptive fields only. Quantity and
    shelf_position are deliberately excluded -- those only ever change
    through a tracked movement (deposit/withdraw/move), so a quantity
    change always has a matching Activity Log row. Barcode is excluded
    too: it's the physical label already printed/scanned, not something
    that should silently change under it.

    Every field is optional so the client only has to send what actually
    changed; the router tells "omitted" from "explicitly cleared" via
    `exclude_unset`.
    """

    name: str | None = None
    pn: str | None = None
    serial: str | None = None
    category: str | None = None
    program: str | None = None
    size: ItemSize | None = None
    tags: list[str] | None = None
    notes: str | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if value is None:
            return None
        return _normalize_tags(value)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class BarcodeSuggestion(BaseModel):
    """A freshly generated, currently-unused barcode value the form can prefill."""

    barcode: str
