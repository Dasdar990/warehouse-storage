"""Pydantic schemas for warehouse map zones."""
import re

from pydantic import BaseModel, Field, field_validator

_HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


class ZoneBase(BaseModel):
    """A named, colored area drawn on the map canvas to delimit a zone."""

    name: str = Field(..., min_length=1, max_length=60, description='e.g. "Zona ricambi motore"')
    color: str = Field(default="#3b82f6", description="Hex color, e.g. #3b82f6")
    x: float = Field(..., description="Top-left X on the canvas, in pixels")
    y: float = Field(..., description="Top-left Y on the canvas, in pixels")
    width: float = Field(default=200, gt=0)
    height: float = Field(default=150, gt=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        return value

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        value = (value or "#3b82f6").strip()
        if not _HEX_COLOR_PATTERN.match(value):
            raise ValueError('color must be a hex value like "#3b82f6"')
        return value.lower()


class ZoneOut(ZoneBase):
    id: int

    class Config:
        from_attributes = True


class ZoneMapSave(BaseModel):
    """Full-layout payload sent by the config page's zone canvas."""

    zones: list[ZoneBase] = Field(default_factory=list)
