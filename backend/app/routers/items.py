"""Item CRUD, scanning, and withdrawal endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.models.item import Item, ItemSize
from app.schemas.item import BarcodeSuggestion, ItemCreate, ItemOut
from app.schemas.movement import StockMoveRequest, StockMoveResponse
from app.services.barcode_generator import generate_unique_barcode
from app.services.movement_service import deposit_stock, withdraw_stock

router = APIRouter(prefix="/items", tags=["items"])
settings = get_settings()


@router.get("", response_model=list[ItemOut])
def list_items(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(
        default=None, description="Case-insensitive match against name, P/N, or barcode"
    ),
    category: Optional[str] = Query(default=None, description="Exact category match"),
    size: Optional[ItemSize] = Query(default=None, description="Exact size match"),
    shelf_position: Optional[str] = Query(default=None, description="Exact shelf match"),
    low_stock: bool = Query(
        default=False, description=f"Only items with quantity <= {settings.low_stock_threshold}"
    ),
):
    """
    Return items, optionally filtered. Powers both the plain inventory list
    and the dashboard's search/filter panel.
    """
    stmt = select(Item)

    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(Item.name.ilike(like), Item.pn.ilike(like), Item.barcode.ilike(like))
        )
    if category:
        stmt = stmt.where(Item.category == category)
    if size:
        stmt = stmt.where(Item.size == size)
    if shelf_position:
        stmt = stmt.where(Item.shelf_position == shelf_position.upper())
    if low_stock:
        stmt = stmt.where(Item.quantity <= settings.low_stock_threshold)

    stmt = stmt.order_by(Item.id.desc())
    return db.execute(stmt).scalars().all()


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    """Distinct categories currently in use -- populates the dashboard filter dropdown."""
    rows = db.execute(select(Item.category).distinct()).scalars().all()
    return sorted(rows)


@router.get("/scan", response_model=ItemOut)
def scan_item(barcode: str, db: Session = Depends(get_db)):
    """Look up a single item by its exact barcode value (used by the scanner gun)."""
    item = db.execute(select(Item).where(Item.barcode == barcode)).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found for barcode '{barcode}'")
    return item


@router.get("/barcode/next", response_model=BarcodeSuggestion)
def get_next_barcode(db: Session = Depends(get_db)):
    """
    Generate a fresh, currently-unused barcode value to prefill the item
    form with. Purely a suggestion -- the form field stays editable, and
    the value is only reserved once the item is actually created.
    """
    return BarcodeSuggestion(barcode=generate_unique_barcode(db))


@router.post("", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    """Create a new inventory item. Fails with 409 if the barcode already exists."""
    existing = db.execute(select(Item).where(Item.barcode == payload.barcode)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409, detail=f"Barcode '{payload.barcode}' is already assigned to another item"
        )

    item = Item(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/withdraw", response_model=StockMoveResponse)
def withdraw_item(payload: StockMoveRequest, db: Session = Depends(get_db)):
    """
    Atomically withdraw stock for the item matching `barcode` (PRELEVA).

    Prevents the resulting quantity from going negative; returns 400 if the
    requested quantity exceeds what's currently in stock. Every call writes
    a matching audit-log row (see /movements) tagged with `source` so the
    UI can show a "Barcode Verified" / "Manual Entry" badge.
    """
    item, movement = withdraw_stock(db, payload)
    return StockMoveResponse(
        item=item,
        moved=payload.quantity,
        action=movement.action,
        message=f"Prelevate {payload.quantity} unità di '{item.name}'. {item.quantity} rimanenti.",
    )


@router.post("/deposit", response_model=StockMoveResponse)
def deposit_item(payload: StockMoveRequest, db: Session = Depends(get_db)):
    """
    Atomically deposit (restock) the item matching `barcode` (DEPOSITA).

    Mirrors `withdraw_item` but increases quantity; also writes a
    matching audit-log row.
    """
    item, movement = deposit_stock(db, payload)
    return StockMoveResponse(
        item=item,
        moved=payload.quantity,
        action=movement.action,
        message=f"Depositate {payload.quantity} unità di '{item.name}'. {item.quantity} totali.",
    )
