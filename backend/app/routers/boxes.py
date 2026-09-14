"""
Box endpoints: CRUD for storage boxes, assigning/removing items to/from
them, and printable labels for the box itself (see services/box_service.py
for why boxes exist -- generic items with no room for their own label).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.box import Box
from app.models.item import Item
from app.models.user import User
from app.schemas.box import BoxCreate, BoxOut, BoxUpdate
from app.schemas.item import ItemOut
from app.services import box_service
from app.services.label_generator import generate_label_image

router = APIRouter(prefix="/boxes", tags=["boxes"], dependencies=[Depends(get_current_user)])


def _to_out(box: Box, item_count: int, total_quantity: int) -> BoxOut:
    return BoxOut(
        id=box.id,
        code=box.code,
        name=box.name,
        shelf_position=box.shelf_position,
        item_count=item_count,
        total_quantity=total_quantity,
    )


def _get_box_or_404(db: Session, box_id: int) -> Box:
    box = box_service.get_box(db, box_id)
    if box is None:
        raise HTTPException(status_code=404, detail=f"No box found with id {box_id}")
    return box


@router.get("", response_model=list[BoxOut])
def list_boxes(
    db: Session = Depends(get_db),
    shelf_position: str | None = Query(
        default=None, description="Only boxes sitting on this exact shelf level"
    ),
):
    """Every box, newest first, with live item/quantity aggregates."""
    rows = box_service.list_boxes(db)
    if shelf_position:
        rows = [r for r in rows if r[0].shelf_position == shelf_position.upper()]
    return [_to_out(*row) for row in rows]


@router.get("/{box_id}", response_model=BoxOut)
def get_box(box_id: int, db: Session = Depends(get_db)):
    box = _get_box_or_404(db, box_id)
    count, qty = box_service.get_box_aggregate(db, box.id)
    return _to_out(box, count, qty)


@router.get("/{box_id}/items", response_model=list[ItemOut])
def list_box_items(box_id: int, db: Session = Depends(get_db)):
    """Every item currently stored inside this box."""
    _get_box_or_404(db, box_id)
    return list(
        db.execute(select(Item).where(Item.box_id == box_id).order_by(Item.id)).scalars().all()
    )


@router.post("", response_model=BoxOut, status_code=201)
def create_box(payload: BoxCreate, db: Session = Depends(get_db)):
    """Create a new, empty box on a shelf level. Its code (e.g. "BOX-0007") is auto-generated."""
    box = box_service.create_box(db, payload)
    return _to_out(box, 0, 0)


@router.patch("/{box_id}", response_model=BoxOut)
def update_box(
    box_id: int,
    payload: BoxUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rename a box and/or move it (with everything inside) to a different shelf level."""
    box = _get_box_or_404(db, box_id)
    box = box_service.update_box(db, box, payload, operator=current_user.full_name)
    count, qty = box_service.get_box_aggregate(db, box.id)
    return _to_out(box, count, qty)


@router.delete("/{box_id}", status_code=204)
def delete_box(box_id: int, db: Session = Depends(get_db)):
    """Delete an empty box. Fails with 400 if it still has items inside."""
    box = _get_box_or_404(db, box_id)
    try:
        box_service.delete_box(db, box)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{box_id}/items/{item_id}", response_model=ItemOut)
def add_item_to_box(
    box_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Put an existing item inside this box. The item's shelf_position is
    overwritten with the box's own (and any zone placement is dropped --
    boxes only live on shelves), logged as an EDIT movement so it shows up
    in the Activity Log.
    """
    box = _get_box_or_404(db, box_id)
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found with id {item_id}")
    return box_service.assign_item(db, box, item, operator=current_user.full_name)


@router.delete("/items/{item_id}", response_model=ItemOut)
def remove_item_from_box(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Take an item out of whichever box it's in. It stays on that box's shelf, just loose."""
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found with id {item_id}")
    try:
        return box_service.remove_item(db, item, operator=current_user.full_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _label_page_html(png_url: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{ size: 101mm 54mm; margin: 0; }}
  html, body {{ margin: 0; padding: 0; }}
  img {{
    display: block;
    width: 101mm;
    height: 54mm;
    image-rendering: pixelated;
    page-break-after: always;
  }}
</style>
</head>
<body>
  <img src="{png_url}" onload="window.print()">
  <script>
    window.onafterprint = () => window.close();
  </script>
</body>
</html>"""


def _regenerate_box_label(box: Box) -> None:
    """Boxes reuse the item label layout: code goes where the barcode goes,
    the box's own name (or a generic fallback) where the item name goes,
    no P/N/serial, and the shelf line -- box ids are negative so they can
    never collide with a real item id on disk (labels_static/{id}.png)."""
    generate_label_image(
        item_id=-box.id,
        name=box.name or f"Box {box.code}",
        pn="",
        shelf_position=box.shelf_position,
        barcode_value=box.code,
        serial=None,
    )


@router.get("/{box_id}/label")
def view_box_label(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    box = _get_box_or_404(db, box_id)
    _regenerate_box_label(box)
    png_url = f"/labels_static/-{box.id}.png"
    return HTMLResponse(content=_label_page_html(png_url))


@router.post("/label/{box_id}")
def generate_box_label(
    box_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate (or regenerate) a printable Code128 label PNG for the box and return the raw file."""
    box = _get_box_or_404(db, box_id)
    output_path = generate_label_image(
        item_id=-box.id,
        name=box.name or f"Box {box.code}",
        pn="",
        shelf_position=box.shelf_position,
        barcode_value=box.code,
        serial=None,
    )
    return FileResponse(
        path=output_path,
        media_type="image/png",
        filename=f"label_box_{box.code}.png",
    )
