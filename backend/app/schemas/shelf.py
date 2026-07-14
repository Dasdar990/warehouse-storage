"""Pydantic schemas for the warehouse map / rack / mensola (shelf-level) endpoints."""
from pydantic import BaseModel, Field, field_validator

from app.schemas.item import ItemOut
from app.schemas.zone import ZoneOut

_MIN_LEVELS = 1
_MAX_LEVELS = 12


class ShelfNodeBase(BaseModel):
    """A rack ("scaffale") box as placed on the map canvas by the drag-and-drop editor."""

    rack_code: str = Field(..., min_length=1, description='Numeric rack identifier, e.g. "12"')
    label: str | None = Field(default=None, description="Optional display label, defaults to rack_code")
    x: float = Field(..., description="Top-left X on the canvas, in pixels")
    y: float = Field(..., description="Top-left Y on the canvas, in pixels")
    width: float = Field(default=90, gt=0)
    height: float = Field(default=140, gt=0)
    levels: list[str] = Field(
        default_factory=lambda: ["A"],
        description='Level letters for this rack\'s shelves, e.g. ["A", "B", "C"]',
    )
    zone_id: int | None = Field(default=None, description="Optional zone this rack belongs to")

    @field_validator("rack_code")
    @classmethod
    def normalize_rack_code(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("rack_code cannot be empty")
        if not value.isdigit():
            raise ValueError('rack_code must be numeric, e.g. "12" (levels are added separately)')
        return value

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("levels")
    @classmethod
    def normalize_levels(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for raw in value:
            level = raw.strip().upper()
            if not level:
                continue
            if not level.isalpha():
                raise ValueError(f'level "{raw}" must be a letter, e.g. "A"')
            if level not in cleaned:
                cleaned.append(level)
        if len(cleaned) < _MIN_LEVELS:
            raise ValueError("a rack needs at least one level (mensola)")
        if len(cleaned) > _MAX_LEVELS:
            raise ValueError(f"a rack can have at most {_MAX_LEVELS} levels")
        return cleaned


class ShelfNodeOut(ShelfNodeBase):
    id: int

    class Config:
        from_attributes = True


class WarehouseMapSave(BaseModel):
    """Full-layout payload sent by the config page's "Save layout" button."""

    nodes: list[ShelfNodeBase] = Field(default_factory=list)


class ShelfMapNode(ShelfNodeBase):
    """A configured rack merged with live stock aggregates across all its levels."""

    item_count: int = 0
    total_quantity: int = 0
    categories: list[str] = Field(default_factory=list)
    has_low_stock: bool = False


class ShelfSummary(BaseModel):
    """Aggregated info about a single shelf position, used by the fallback grid map."""

    shelf_position: str
    shelf_number: int
    level: str
    item_count: int
    total_quantity: int
    categories: list[str]
    has_low_stock: bool


class WarehouseLayout(BaseModel):
    """Full grid definition + per-shelf aggregates, consumed by the Vue map.

    `has_custom_layout` / `nodes` / `zones` carry the user-drawn, freeform map
    (zones + racks from the config page) when one has been saved. The
    frontend renders the freeform canvas when `has_custom_layout` is true,
    and falls back to the auto-generated number x level grid otherwise.
    """

    shelf_numbers: list[int]
    levels: list[str]
    low_stock_threshold: int
    shelves: list[ShelfSummary]
    has_custom_layout: bool = False
    nodes: list[ShelfMapNode] = Field(default_factory=list)
    zones: list[ZoneOut] = Field(default_factory=list)


class ShelfItemsResponse(BaseModel):
    shelf_position: str
    items: list[ItemOut]


class MensolaSummary(BaseModel):
    """One level ("mensola") within a rack, with its live stock aggregates."""

    shelf_position: str
    level: str
    item_count: int
    total_quantity: int
    categories: list[str]
    has_low_stock: bool


class RackLevelsResponse(BaseModel):
    """A rack's mensole (drill-down shown after clicking a rack on the map)."""

    rack_code: str
    label: str | None
    levels: list[MensolaSummary]
