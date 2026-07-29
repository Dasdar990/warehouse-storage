"""Item CRUD, scanning, and withdrawal endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db import get_db
from app.models.item import Item, ItemSize
from app.models.user import User
from app.schemas.item import BarcodeSuggestion, ItemCreate, ItemOut
from app.schemas.movement import RelocateItemRequest, RelocateItemResponse, StockMoveRequest, StockMoveResponse
from app.services.barcode_generator import generate_unique_barcode
from app.services.movement_service import deposit_stock, move_item, withdraw_stock

router = APIRouter(prefix="/items", tags=["items"], dependencies=[Depends(get_current_user)])
settings = get_settings()


@router.get("", response_model=list[ItemOut])
def list_items(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(
        default=None, description="Case-insensitive match against name, P/N, or barcode"
    ),
    category: Optional[str] = Query(default=None, description="Exact category match"),
    program: Optional[str] = Query(default=None, description="Exact program match"),
    size: Optional[ItemSize] = Query(default=None, description="Exact size match"),
    shelf_position: Optional[str] = Query(default=None, description="Exact shelf match"),
    pn: Optional[str] = Query(
        default=None, description="Exact P/N match -- finds every shelf location for one part"
    ),
    min_qty: Optional[int] = Query(default=None, ge=0, description="Only items with quantity >= this value"),
    max_qty: Optional[int] = Query(default=None, ge=0, description="Only items with quantity <= this value"),
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
            or_(
                Item.name.ilike(like),
                Item.pn.ilike(like),
                Item.barcode.ilike(like),
                Item.serial.ilike(like),
            )
        )
    if category:
        stmt = stmt.where(Item.category == category)
    if program:
        stmt = stmt.where(Item.program == program)
    if size:
        stmt = stmt.where(Item.size == size)
    if shelf_position:
        stmt = stmt.where(Item.shelf_position == shelf_position.upper())
    if pn:
        stmt = stmt.where(Item.pn.ilike(pn.strip()))
    if min_qty is not None:
        stmt = stmt.where(Item.quantity >= min_qty)
    if max_qty is not None:
        stmt = stmt.where(Item.quantity <= max_qty)
    if low_stock:
        stmt = stmt.where(Item.quantity <= settings.low_stock_threshold)

    stmt = stmt.order_by(Item.id.desc())
    return db.execute(stmt).scalars().all()


@router.get("/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    """Distinct categories currently in use -- populates the dashboard filter dropdown."""
    rows = db.execute(select(Item.category).distinct()).scalars().all()
    return sorted(rows)


@router.get("/programs", response_model=list[str])
def list_item_programs(db: Session = Depends(get_db)):
    """Distinct (non-empty) programs currently in use -- populates the dashboard filter dropdown."""
    rows = db.execute(select(Item.program).distinct()).scalars().all()
    return sorted(r for r in rows if r)


@router.get("/shelves", response_model=list[str])
def list_item_shelves(db: Session = Depends(get_db)):
    """
    Distinct (non-empty) shelf positions currently holding at least one
    item -- populates the dashboard's shelf filter dropdown. A fully
    withdrawn item's shelf is cleared (see `_clear_shelf_if_empty`), so
    this naturally only ever lists shelves that actually have stock on them.
    """
    rows = db.execute(select(Item.shelf_position).distinct()).scalars().all()
    return sorted(r for r in rows if r)


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


@router.get("/check-duplicate", response_model=list[ItemOut])
def check_duplicate_item(
    name: Optional[str] = Query(default=None, description="Candidate item name"),
    pn: Optional[str] = Query(default=None, description="Candidate part number"),
    db: Session = Depends(get_db),
):
    """
    Look up existing items that a about-to-be-created item might duplicate.

    Matches case-insensitively on name and/or PN so the "New Item" form can
    warn the user and offer to top up the existing item instead of creating
    a near-duplicate row.
    """
    name = (name or "").strip()
    pn = (pn or "").strip()
    if not name and not pn:
        return []

    conditions = []
    if name:
        conditions.append(Item.name.ilike(name))
    if pn:
        conditions.append(Item.pn.ilike(pn))

    stmt = select(Item).where(or_(*conditions)).order_by(Item.id.desc()).limit(5)
    return db.execute(stmt).scalars().all()


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
def withdraw_item(
    payload: StockMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atomically withdraw stock for the item matching `barcode` (WITHDRAW).

    Prevents the resulting quantity from going negative; returns 400 if the
    requested quantity exceeds what's currently in stock. Every call writes
    a matching audit-log row (see /movements) tagged with `source` so the
    UI can show a "Barcode Verified" / "Manual Entry" badge, and `operator`
    set to the logged-in user -- never client-supplied, so it can't be spoofed.
    """
    item, movement = withdraw_stock(db, payload, operator=current_user.full_name)
    return StockMoveResponse(
        item=item,
        moved=payload.quantity,
        action=movement.action,
        message=f"Withdrew {payload.quantity} unit(s) of '{item.name}'. {item.quantity} remaining.",
    )


@router.post("/deposit", response_model=StockMoveResponse)
def deposit_item(
    payload: StockMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atomically deposit (restock) the item matching `barcode` (DEPOSIT).

    Mirrors `withdraw_item` but increases quantity; also writes a
    matching audit-log row with `operator` derived from the logged-in user.
    """
    item, movement = deposit_stock(db, payload, operator=current_user.full_name)
    return StockMoveResponse(
        item=item,
        moved=payload.quantity,
        action=movement.action,
        message=f"Deposited {payload.quantity} unit(s) of '{item.name}'. {item.quantity} total.",
    )


@router.post("/move", response_model=RelocateItemResponse)
def move_item_endpoint(
    payload: RelocateItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Relocate the item matching `barcode` to a different shelf. Quantity is
    left untouched -- this only changes where the item lives. Writes a MOVE
    audit-log row (see /movements) recording both the origin and destination
    shelf, with `operator` derived from the logged-in user.
    """
    item, movement = move_item(db, payload, operator=current_user.full_name)
    return RelocateItemResponse(
        item=item,
        from_shelf_position=movement.from_shelf_position or "",
        to_shelf_position=movement.shelf_position,
        message=f"Moved '{item.name}' from shelf {movement.from_shelf_position} to {movement.shelf_position}.",
    )
