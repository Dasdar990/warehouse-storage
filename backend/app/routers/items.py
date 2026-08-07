"""Item CRUD, scanning, and withdrawal endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, require_admin
from app.db import get_db
from app.models.item import Item, ItemSize
from app.models.user import User
from app.schemas.item import BarcodeSuggestion, ItemCreate, ItemOut, ItemUpdate
from app.schemas.movement import (
    BulkMoveRequest,
    BulkMoveResponse,
    RelocateItemRequest,
    RelocateItemResponse,
    StockMoveRequest,
    StockMoveResponse,
)
from app.services.barcode_generator import generate_unique_barcode
from app.services.movement_service import bulk_move, deposit_stock, log_edit_item, move_item, withdraw_stock

router = APIRouter(
    prefix="/items", tags=["items"], dependencies=[Depends(get_current_user)])
settings = get_settings()


@router.get("", response_model=list[ItemOut])
def list_items(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(
        default=None, description="Case-insensitive match against name, P/N, or barcode"
    ),
    category: Optional[str] = Query(
        default=None, description="Exact category match"),
    program: Optional[str] = Query(
        default=None, description="Exact program match"),
    size: Optional[ItemSize] = Query(
        default=None, description="Exact size match"),
    shelf_position: Optional[str] = Query(
        default=None, description="Exact shelf match"),
    pn: Optional[str] = Query(
        default=None, description="Exact P/N match -- finds every shelf location for one part"
    ),
    tag: Optional[str] = Query(
        default=None, description="Exact tag match (one of the item's tags, not a substring)"
    ),
    min_qty: Optional[int] = Query(
        default=None, ge=0, description="Only items with quantity >= this value"),
    max_qty: Optional[int] = Query(
        default=None, ge=0, description="Only items with quantity <= this value"),
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
                Item.tags.ilike(like),
                Item.notes.ilike(like),
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
    if tag:
        # Tags are stored comma-separated with no spaces (see _normalize_tags),
        # so match this exact tag as one element of that list, not just any
        # substring -- a filter for "spa" shouldn't also pull in "spare-part".
        t = tag.strip()
        stmt = stmt.where(
            or_(
                Item.tags.ilike(t),
                Item.tags.ilike(f"{t},%"),
                Item.tags.ilike(f"%,{t},%"),
                Item.tags.ilike(f"%,{t}"),
            )
        )
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


@router.get("/tags", response_model=list[str])
def list_item_tags(db: Session = Depends(get_db)):
    """Distinct tags currently in use across all items -- populates the dashboard's tag filter dropdown."""
    rows = db.execute(select(Item.tags).where(Item.tags.isnot(None))).scalars().all()
    seen: set[str] = set()
    for row in rows:
        for tag in row.split(","):
            if tag:
                seen.add(tag)
    return sorted(seen, key=str.lower)


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
    item = db.execute(select(Item).where(
        Item.barcode == barcode)).scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"No item found for barcode '{barcode}'")
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
    name: Optional[str] = Query(
        default=None, description="Candidate item name"),
    pn: Optional[str] = Query(
        default=None, description="Candidate part number"),
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

    stmt = select(Item).where(or_(*conditions)
                              ).order_by(Item.id.desc()).limit(5)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    """Create a new inventory item. Fails with 409 if the barcode already exists."""
    existing = db.execute(select(Item).where(
        Item.barcode == payload.barcode)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=409, detail=f"Barcode '{payload.barcode}' is already assigned to another item"
        )

    data = payload.model_dump()
    tags = data.pop("tags", [])
    item = Item(**data, tags=",".join(tags) if tags else None)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Edit an item's descriptive fields (name, P/N, serial, category,
    program, size, tags, notes). Quantity, shelf, and barcode aren't
    editable here -- see /items/deposit, /withdraw, /move for stock
    changes, all of which keep a matching Activity Log entry. Whatever
    *does* change here is diffed and logged as an EDIT movement too, so
    it shows up in the Activity Log and can be rolled back like any other
    change (see rollback_movement).
    """
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    updates = payload.model_dump(exclude_unset=True)
    changes: dict[str, list[str | None]] = {}

    def apply(field: str, new_value):
        old_value = getattr(item, field)
        if old_value != new_value:
            changes[field] = [old_value, new_value]
        setattr(item, field, new_value)

    if "name" in updates:
        name = (updates["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Name can't be blank")
        apply("name", name)

    if "category" in updates:
        category = (updates["category"] or "").strip()
        if not category:
            raise HTTPException(status_code=400, detail="Category can't be blank")
        apply("category", category)

    if "pn" in updates:
        apply("pn", (updates["pn"] or "").strip())

    if "serial" in updates:
        apply("serial", (updates["serial"] or "").strip() or None)

    if "program" in updates:
        apply("program", (updates["program"] or "").strip() or None)

    if "size" in updates:
        apply("size", updates["size"])

    if "tags" in updates:
        tags = updates["tags"] or []
        apply("tags", ",".join(tags) if tags else None)

    if "notes" in updates:
        apply("notes", (updates["notes"] or "").strip() or None)

    if changes:
        log_edit_item(db, item, changes, operator=current_user.full_name)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Admin-only: permanently delete an item, including any stock it still
    shows. This is not a movement -- there's nothing to roll back, unlike
    withdraw/deposit/move. Past Activity Log entries for this item are kept
    (their `item_id` is set to null by the DB, but item name/P/N are
    already stored as plain text on each entry, so the history stays
    readable).
    """
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()


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
    item, movement = withdraw_stock(
        db, payload, operator=current_user.full_name)
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

    Mirrors `withdraw_item` but increases quantity. If `shelf_position` is
    given and differs from the item's own shelf, the stock lands there
    instead (on a matching item if one already exists, otherwise a new one
    is created) -- the original item is untouched in that case. Also writes
    a matching audit-log row with `operator` derived from the logged-in user.
    """
    item, movement, redirected = deposit_stock(
        db, payload, operator=current_user.full_name)
    if redirected:
        message = (
            f"Deposited {payload.quantity} unit(s) of '{item.name}' onto shelf "
            f"{item.shelf_position}. {item.quantity} there now."
        )
    else:
        message = f"Deposited {payload.quantity} unit(s) of '{item.name}'. {item.quantity} total."
    return StockMoveResponse(
        item=item,
        moved=payload.quantity,
        action=movement.action,
        message=message,
    )


@router.post("/move", response_model=RelocateItemResponse)
def move_item_endpoint(
    payload: RelocateItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Relocate stock for the item matching `barcode` to a different shelf.

    Omitting `quantity` (or passing the item's full current quantity) moves
    it entirely -- quantity is left untouched, only the shelf changes. A
    smaller `quantity` splits the stock instead: the source keeps the
    remainder and the moved amount tops up (or creates) an item on the
    destination shelf. Writes a MOVE audit-log row (see /movements)
    recording both the origin and destination shelf, with `operator`
    derived from the logged-in user.
    """
    item, movement, full = move_item(
        db, payload, operator=current_user.full_name)
    if full:
        message = f"Moved '{item.name}' from shelf {movement.from_shelf_position} to {movement.shelf_position}."
    else:
        message = (
            f"Moved {movement.quantity} unit(s) of '{item.name}' to shelf {movement.shelf_position}. "
            f"{item.quantity} unit(s) remain on shelf {item.shelf_position}."
        )
    return RelocateItemResponse(
        item=item,
        from_shelf_position=movement.from_shelf_position or "",
        to_shelf_position=movement.shelf_position,
        message=message,
    )


@router.post("/special-move", response_model=BulkMoveResponse)
def special_move(
    payload: BulkMoveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Admin-only: relocate everything on one shelf, or an entire rack, in one
    shot -- e.g. when a physical shelving unit gets moved, or a shelf's
    contents get consolidated elsewhere. Every item found there is
    relocated with its own MOVE audit-log entry; quantities are untouched.
    """
    moved_items, moved_quantity, message = bulk_move(
        db, payload, operator=current_user.full_name)
    return BulkMoveResponse(moved_items=moved_items, moved_quantity=moved_quantity, message=message)
