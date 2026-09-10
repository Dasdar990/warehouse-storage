"""Printable barcode label endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.item import Item
from app.models.user import User
from app.services.label_generator import generate_label_image

router = APIRouter(prefix="/items", tags=["labels"])


def _regenerate_label(item: Item) -> None:
    """(Re)build the PNG for `item` on disk so /labels_static always has a
    fresh file to serve -- callers that only display the PNG (view_label,
    the batch view) never called generate_label_image themselves, so a
    brand-new item had no file to show at all."""
    generate_label_image(
        item_id=item.id,
        name=item.name,
        pn=item.pn,
        shelf_position=item.shelf_position,
        barcode_value=item.barcode,
        serial=item.serial,
    )


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
    // afterprint fires whether the user actually printed or hit Cancel,
    // so either way this tab closes itself instead of sitting there.
    window.onafterprint = () => window.close();
  </script>
</body>
</html>"""


@router.get("/{item_id}/label")
def view_label(item_id: int, token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found with id {item_id}")

    # Regenerate on every view so the PNG exists for brand-new items and
    # always reflects the item's current shelf/name/etc.
    _regenerate_label(item)

    png_url = f"/labels_static/{item_id}.png"
    return HTMLResponse(content=_label_page_html(png_url))


@router.get("/label/batch")
def view_label_batch(
    ids: str = Query(..., description="Comma-separated item ids"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """One tab, one print dialog for several labels (multi-serial creation)."""
    try:
        item_ids = [int(i) for i in ids.split(",") if i]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ids parameter")

    if not item_ids:
        raise HTTPException(status_code=400, detail="No ids provided")

    items = db.query(Item).filter(Item.id.in_(item_ids)).all()
    items_by_id = {item.id: item for item in items}
    missing = [i for i in item_ids if i not in items_by_id]
    if missing:
        raise HTTPException(status_code=404, detail=f"No item(s) found with id(s) {missing}")

    # Preserve the order the caller asked for, regenerate every PNG.
    ordered_items = [items_by_id[i] for i in item_ids]
    for item in ordered_items:
        _regenerate_label(item)

    images_html = "\n".join(
        f'  <img src="/labels_static/{item.id}.png">' for item in ordered_items
    )

    html = f"""<!DOCTYPE html>
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
{images_html}
<script>
  window.onload = () => window.print();
  // afterprint fires whether the user actually printed or hit Cancel.
  window.onafterprint = () => window.close();
</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.post("/label/{item_id}")
def generate_label(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate (or regenerate) a printable Code128 label PNG for the given item and return the raw file."""
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"No item found with id {item_id}")

    output_path = generate_label_image(
        item_id=item.id,
        name=item.name,
        pn=item.pn,
        shelf_position=item.shelf_position,
        barcode_value=item.barcode,
        serial=item.serial,
    )

    return FileResponse(
        path=output_path,
        media_type="image/png",
        filename=f"label_{item.id}.png",
    )