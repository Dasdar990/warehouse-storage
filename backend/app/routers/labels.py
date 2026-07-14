"""Printable barcode label endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.item import Item
from app.services.label_generator import generate_label_image

router = APIRouter(prefix="/items", tags=["labels"])


@router.post("/label/{item_id}")
def generate_label(item_id: int, db: Session = Depends(get_db)):
    """Generate (or regenerate) a printable Code128 label PNG for the given item."""
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found with id {item_id}")

    output_path = generate_label_image(
        item_id=item.id,
        name=item.name,
        pn=item.pn,
        shelf_position=item.shelf_position,
        barcode_value=item.barcode,
    )

    return FileResponse(
        path=output_path,
        media_type="image/png",
        filename=f"label_{item.id}.png",
    )
