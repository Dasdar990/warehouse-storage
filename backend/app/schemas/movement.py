"""Pydantic schemas for stock movements (deposit/withdraw) and the audit log."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.movement import MovementAction, MovementSource
from app.schemas.item import ItemOut


class StockMoveRequest(BaseModel):
    """Shared shape for both /items/withdraw and /items/deposit."""

    barcode: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0, description="Quantity to move, must be positive")
    shelf_position: str | None = Field(
        default=None,
        description=(
            "Deposit only: destination shelf, if different from the item's current one. "
            "Lands on an existing item there if one already exists for the same part "
            "number, otherwise a brand-new item row is created at that shelf. "
            "Ignored for withdrawals."
        ),
    )
    source: MovementSource = Field(
        default=MovementSource.MANUAL,
        description="'barcode' if triggered by a scanner read, 'manual' if typed/clicked in the UI",
    )
    # No `operator` field here on purpose: it's derived server-side from the
    # authenticated user (see routers/items.py), so a client can't spoof it.


class StockMoveResponse(BaseModel):
    item: ItemOut
    moved: int
    action: MovementAction
    message: str


class RelocateItemRequest(BaseModel):
    """Shape for POST /items/move: relocate an item to a different shelf."""

    barcode: str = Field(..., min_length=1)
    shelf_position: str = Field(..., min_length=1, description="Destination shelf, e.g. '12B'")
    quantity: int | None = Field(
        default=None,
        gt=0,
        description=(
            "How many units to move. Omit (or pass the item's full current quantity) "
            "to relocate it entirely -- the same behaviour as before. A smaller number "
            "splits the stock: the source keeps the remainder and the destination "
            "either tops up a matching item there or gets a new one created for it."
        ),
    )
    source: MovementSource = Field(
        default=MovementSource.MANUAL,
        description="'barcode' if triggered by a scanner read, 'manual' if typed/clicked in the UI",
    )


class RelocateItemResponse(BaseModel):
    item: ItemOut
    from_shelf_position: str
    to_shelf_position: str
    message: str


class MovementOut(BaseModel):
    id: int
    timestamp: datetime
    item_id: int | None
    item_name: str
    pn: str
    shelf_position: str
    from_shelf_position: str | None
    action: MovementAction
    quantity: int
    balance_after: int
    source: MovementSource
    operator: str
    voided: bool
    reversal_of_id: int | None

    class Config:
        from_attributes = True


class RollbackResponse(BaseModel):
    item: ItemOut
    reversal: MovementOut
    message: str
