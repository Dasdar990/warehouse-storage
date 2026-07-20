"""Pydantic schemas for the warehouse room outline (walls + door)."""
from pydantic import BaseModel, Field, field_validator


class WallBase(BaseModel):
    """A wall segment: a thin rectangle, dragged/resized/rotated like a rack."""

    x: float
    y: float
    width: float = Field(..., gt=0, description="Wall length, in pixels")
    height: float = Field(default=10, gt=0, description="Wall thickness, in pixels")
    rotation: float = Field(default=0, description="Rotation in degrees")

    @field_validator("rotation")
    @classmethod
    def normalize_wall_rotation(cls, value: float) -> float:
        return round(value % 360, 2)


class WallOut(WallBase):
    id: int

    class Config:
        from_attributes = True


class DoorBase(BaseModel):
    """A door marker: hinge point + swing width/rotation."""

    x: float = Field(..., description="Hinge point X, in pixels")
    y: float = Field(..., description="Hinge point Y, in pixels")
    width: float = Field(default=40, gt=0, description="Door opening width, in pixels")
    rotation: float = Field(default=0, description="Rotation in degrees, matching the door's physical orientation")

    @field_validator("rotation")
    @classmethod
    def normalize_rotation(cls, value: float) -> float:
        return round(value % 360, 2)


class DoorOut(DoorBase):
    id: int

    class Config:
        from_attributes = True


class RoomLayoutOut(BaseModel):
    """Full room outline as drawn on the map config page."""

    walls: list[WallOut] = Field(default_factory=list)
    doors: list[DoorOut] = Field(default_factory=list)


class RoomLayoutSave(BaseModel):
    """Full-layout payload sent by the config page's room outline canvas."""

    walls: list[WallBase] = Field(default_factory=list)
    doors: list[DoorBase] = Field(default_factory=list)
