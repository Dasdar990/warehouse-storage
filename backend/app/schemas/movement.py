"""Pydantic schemas for stock movements (deposit/withdraw) and the audit log."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.movement import MovementAction, MovementSource
from app.schemas.item import ItemOut


class StockMoveRequest(BaseModel):
    """Shared shape for both /items/withdraw and /items/deposit."""

    barcode: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, description="Quantity to move, must be positive")
    source: MovementSource = Field(
        default=MovementSource.MANUAL,
        description="'barcode' if triggered by a scanner read, 'manual' if typed/clicked in the UI",
    )
    operator: str = Field(default="Operatore", min_length=1, description="Name/badge of the operator performing the action")


class StockMoveResponse(BaseModel):
    item: ItemOut
    moved: int
    action: MovementAction
    message: str


class MovementOut(BaseModel):
    id: int
    timestamp: datetime
    item_id: int | None
    item_name: str
    pn: str
    shelf_position: str
    action: MovementAction
    quantity: int
    balance_after: int
    source: MovementSource
    operator: str

    class Config:
        from_attributes = True
