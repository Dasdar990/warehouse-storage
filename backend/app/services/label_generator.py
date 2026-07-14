"""
Printable Code128 barcode label generation.

Produces a 400x200px PNG suitable for common industrial/thermal label
printers, containing the item name, part number, shelf position, and a
scannable Code128 barcode rendered from the item's barcode value.
"""
import io
import os
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_settings

settings = get_settings()

LABEL_WIDTH = 400
LABEL_HEIGHT = 200


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
    Build the full 400x200 label (text + barcode) and persist it to
    LABELS_DIR/{item_id}.png. Returns the path to the saved file.
    """
    canvas = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    title_font = _load_font(20)
    label_font = _load_font(14)

    padding = 10
    y = padding

    draw.text((padding, y), name[:32], fill="black", font=title_font)
    y += 26

    draw.text((padding, y), f"P/N: {pn}", fill="black", font=label_font)
    y += 20

    draw.text((padding, y), f"Shelf: {shelf_position}", fill="black", font=label_font)
    y += 24

    # Render and paste the barcode image, scaled to fit the remaining space.
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
    canvas.paste(barcode_img, (padding, y))

    output_path = settings.labels_dir / f"{item_id}.png"
    canvas.save(output_path, format="PNG")
    return output_path
