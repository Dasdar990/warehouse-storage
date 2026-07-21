"""Printable barcode label endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_db
from app.models.item import Item
from app.models.user import User
from app.services.label_generator import generate_label_image

router = APIRouter(prefix="/items", tags=["labels"])


@router.post("/label/{item_id}")
def generate_label(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    )

    return FileResponse(
        path=output_path,
        media_type="image/png",
        filename=f"label_{item.id}.png",
    )


@router.get("/{item_id}/label", response_class=HTMLResponse)
def get_item_label(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Regenerate the label PNG and return an HTML wrapper (sized to the label
    via @page, auto-printing on load) -- this is what the "🖨️ Stampa
    Etichetta" button in the UI opens, so a single click both prints and
    closes the tab without any extra steps at the warehouse bench.

    Opened as a plain browser navigation (new tab), so it can't send an
    Authorization header -- the frontend appends `?token=<jwt>` instead,
    which `get_current_user` also accepts.
    """
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # Genera/salva l'immagine PNG usando la funzione PIL
    generate_label_image(
        item_id=item.id,
        name=item.name,
        pn=item.pn,
        shelf_position=item.shelf_position,
        barcode_value=item.barcode,
    )

    # HTML wrapper with @page CSS sized to the label dimensions and
    # auto-print on load; the image is served from the static mount
    # /labels_static (see app/main.py) so it's always the latest version.
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Label - {item.name}</title>
        <style>
            @page {{
                size: auto;
                margin: 0mm;
            }}
            body {{
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: white;
            }}
            img {{
                width: 100%;
                height: auto;
                max-width: 400px;
                image-rendering: pixelated; /* Mantiene nitidi i dati del codice a barre */
            }}
        </style>
    </head>
    <body onload="window.print(); setTimeout(() => window.close(), 500);">
        <img src="/labels_static/{item.id}.png" alt="Label">
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
