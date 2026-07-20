"""
Printable Code128 barcode label generation.

Produces a 712x224px PNG -- a 28x89mm thermal label at the standard
~203 DPI (8 dots/mm) industrial label-printer resolution -- containing the
item name, part number, shelf position, and a scannable Code128 barcode
rendered from the item's barcode value.
"""
import io
import os
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_settings

settings = get_settings()

# 28mm x 89mm at 8 dots/mm (203 DPI thermal printer standard).
LABEL_WIDTH = 712
LABEL_HEIGHT = 224


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load a reasonable default font, falling back to PIL's bitmap font."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _generate_barcode_image(value: str) -> Image.Image:
    """Render the Code128 barcode itself (no human-readable text) to a PIL Image."""
    code128 = barcode.get_barcode_class("code128")
    writer = ImageWriter()
    # Tune the writer so the barcode renders compactly and without its own
    # built-in text label -- we draw our own text layout instead.
    writer_options = {
        "module_height": 10.0,
        "module_width": 0.28,
        "quiet_zone": 2.0,
        "font_size": 0,
        "text_distance": 0,
        "write_text": False,
    }
    instance = code128(value, writer=writer)
    buffer = io.BytesIO()
    instance.write(buffer, options=writer_options)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def generate_label_image(
    item_id: int, name: str, pn: str, shelf_position: str, barcode_value: str
) -> Path:
    """
    Build the full 712x224px (28x89mm) label -- a text header block on top
    (name / P/N / shelf, with shelf position emphasized so it's readable at
    a glance when placing/picking stock) and the scannable Code128 barcode
    filling the bottom band -- and persist it to LABELS_DIR/{item_id}.png.
    Returns the path to the saved file.
    """
    canvas = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    padding = 18
    name_font = _load_font(30)
    shelf_font = _load_font(40)
    pn_font = _load_font(22)

    # --- Header row: item name (left) + shelf position (right, large) ---
    y = padding
    draw.text((padding, y), name[:40], fill="black", font=name_font)

    shelf_text = shelf_position
    shelf_bbox = draw.textbbox((0, 0), shelf_text, font=shelf_font)
    shelf_w = shelf_bbox[2] - shelf_bbox[0]
    draw.text((LABEL_WIDTH - padding - shelf_w, y - 4), shelf_text, fill="black", font=shelf_font)

    y += 40
    draw.text((padding, y), f"P/N: {pn}", fill="black", font=pn_font)
    y += 34

    draw.line([(padding, y), (LABEL_WIDTH - padding, y)], fill="black", width=2)
    y += 14

    # --- Bottom band: barcode, scaled to fill the remaining width/height ---
    barcode_img = _generate_barcode_image(barcode_value)
    available_height = LABEL_HEIGHT - y - padding
    scale = min(
        (LABEL_WIDTH - 2 * padding) / barcode_img.width,
        available_height / barcode_img.height,
    )
    new_size = (
        max(1, int(barcode_img.width * scale)),
        max(1, int(barcode_img.height * scale)),
    )
    barcode_img = barcode_img.resize(new_size)
    barcode_x = (LABEL_WIDTH - new_size[0]) // 2
    canvas.paste(barcode_img, (barcode_x, y))

    output_path = settings.labels_dir / f"{item_id}.png"
    canvas.save(output_path, format="PNG")
    return output_path
