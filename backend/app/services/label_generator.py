"""
Printable Code128 barcode label generation.

Optimized for 28mm x 89mm thermal label printers (203 DPI native resolution).
Canvas size: 712x224px.

Layout:
- Top Left: Logo
- Top Right: I.E. NERVIANO + Shelf Position
- Middle: Product Name & P/N
- Bottom: Code128 Barcode + Human readable value
"""
import io
import logging
import os
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_settings

settings = get_settings()

# Native resolution at 203 DPI for 89mm x 28mm
LABEL_WIDTH = 712
LABEL_HEIGHT = 224

logger = logging.getLogger("uvicorn.error")


def _load_font(size: int, mono: bool = False, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load DejaVu / Liberation font, falling back to PIL default font."""
    if mono:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _generate_barcode_image(value: str) -> Image.Image:
    """Render Code128 barcode with exact module size."""
    code128 = barcode.get_barcode_class("code128")
    writer = ImageWriter()
    writer_options = {
        "module_height": 10.0,
        "module_width": 0.3,
        "quiet_zone": 1.0,
        "font_size": 0,
        "text_distance": 0,
        "write_text": False,
    }
    instance = code128(value, writer=writer)
    buffer = io.BytesIO()
    instance.write(buffer, options=writer_options)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def _draw_logo(canvas: Image.Image, x: int, y: int, max_w: int, max_h: int):
    """Draws logo from ASSETS_DIR/logo.png or renders a compact text fallback."""
    logo_path = settings.assets_dir / "logo.png"

    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            canvas.paste(logo, (x, y), logo if logo.mode == "RGBA" else None)
            return
        except Exception as e:
            logger.error(f"Error loading logo: {e}")

    # Graphic fallback if logo.png is not present
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x, y, x + max_w, y + max_h], outline="black", width=2)
    font = _load_font(14, bold=True)
    draw.text((x + 10, y + 8), "LOGO", fill="black", font=font)


def generate_label_image(
    item_id: int, name: str, pn: str, shelf_position: str, barcode_value: str
) -> Path:
    """Build the 712x224 PNG label with prominent logo and persist to LABELS_DIR/{item_id}.png."""
    settings.labels_dir.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGB", (LABEL_WIDTH, LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    padding = 14
    y = padding

    # -------------------------------------------------------------
    # 1. TOP ROW: Prominent logo (left) + info (right)
    # -------------------------------------------------------------
    # Enlarged to max 240px width and 60px height
    _draw_logo(canvas, x=padding, y=y, max_w=240, max_h=60)

    top_right_font = _load_font(18, bold=True)
    meta_font = _load_font(15, bold=False)

    # "I.E. NERVIANO" text aligned with the logo area
    tag_text = "I.E. NERVIANO"
    tag_bbox = top_right_font.getbbox(tag_text)
    tag_w = tag_bbox[2] - tag_bbox[0]
    draw.text((LABEL_WIDTH - padding - tag_w, y + 4),
              tag_text, fill="black", font=top_right_font)

    # Shelf position right below I.E. NERVIANO
    shelf_text = f"Shelf: {shelf_position}"
    shelf_bbox = meta_font.getbbox(shelf_text)
    shelf_w = shelf_bbox[2] - shelf_bbox[0]
    draw.text((LABEL_WIDTH - padding - shelf_w, y + 28),
              shelf_text, fill="black", font=meta_font)

    # Lower the divider slightly to compensate for the logo height
    y += 64

    # Thin divider line
    draw.line([(padding, y), (LABEL_WIDTH - padding, y)],
              fill="#000000", width=1)
    y += 6

    # -------------------------------------------------------------
    # 2. MIDDLE BAND: Product name and P/N
    # -------------------------------------------------------------
    title_font = _load_font(20, bold=True)
    pn_font = _load_font(15, bold=False)

    truncated_name = name[:36] + "..." if len(name) > 36 else name
    draw.text((padding, y), truncated_name, fill="black", font=title_font)
    y += 24

    draw.text((padding, y), f"P/N: {pn}", fill="black", font=pn_font)
    y += 20

    # -------------------------------------------------------------
    # 3. BOTTOM PART: Barcode + human-readable barcode text
    # -------------------------------------------------------------
    barcode_img = _generate_barcode_image(barcode_value)

    text_font = _load_font(15, mono=True, bold=True)
    text_height = 18
    available_width = LABEL_WIDTH - (2 * padding)
    available_height = LABEL_HEIGHT - y - padding - text_height

    # NEAREST resizing for crisp edges and better optical scanner readability
    scale_w = available_width / barcode_img.width
    scale_h = available_height / barcode_img.height
    scale = min(scale_w, scale_h)

    new_w = max(1, int(barcode_img.width * scale))
    new_h = max(1, int(barcode_img.height * scale))
    barcode_img = barcode_img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Center the barcode horizontally
    barcode_x = padding + (available_width - new_w) // 2
    canvas.paste(barcode_img, (barcode_x, y))
    y += new_h + 2

    # Barcode text centered below the bars
    bbox = text_font.getbbox(barcode_value)
    text_w = bbox[2] - bbox[0]
    text_x = padding + (available_width - text_w) // 2
    draw.text((text_x, y), barcode_value, fill="black", font=text_font)

    output_path = settings.labels_dir / f"{item_id}.png"
    canvas.save(output_path, format="PNG")
    return output_path
