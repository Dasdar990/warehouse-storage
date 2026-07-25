"""Pydantic request/response schemas for the program catalog."""
from pydantic import BaseModel, Field, field_validator


class ProgramBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=60, description='e.g. "Falcon Refit"')

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be empty")
        return value


class ProgramCreate(ProgramBase):
    pass


class ProgramOut(ProgramBase):
    id: int

    class Config:
        from_attributes = True
