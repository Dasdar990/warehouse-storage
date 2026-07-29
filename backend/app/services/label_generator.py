"""
Printable Code128 barcode label generation.

Optimized for 89mm x 28mm thermal label printers (203 DPI native resolution).
Canvas size: 712x224px (89mm * 8.0 bits/mm x 28mm * 8.0 bits/mm).

Layout:
- Top Left: Logo
- Top Right: I.E. NERVIANO + Shelf Position
- Middle: Product Name & P/N
- Bottom: Max-Width Code128 Barcode + Human readable value (Optimized for entry-level scanners)
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

# Risoluzione nativa a 203 DPI per 89mm x 28mm (712x224 pixel)
LABEL_WIDTH = 712
LABEL_HEIGHT = 224
BARCODE_DPI = 203

logger = logging.getLogger("uvicorn.error")


def _load_font(size: int, mono: bool = False, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load DejaVu / Liberation font, falling back to PIL default font."""
    if mono:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
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
    """Render base Code128 barcode image in 1-bit mode."""
    code128 = barcode.get_barcode_class("code128")
    writer = ImageWriter()

    writer_options = {
        "dpi": BARCODE_DPI,
        "module_height": 12.0,
        "module_width": 0.25,  # Genera moduli base puliti a 203 DPI
        "quiet_zone": 4.0,     # Garantisce la Quiet Zone minima ai lati
        "font_size": 0,
        "text_distance": 0,
        "write_text": False,
    }
    instance = code128(value, writer=writer)
    buffer = io.BytesIO()
    instance.write(buffer, options=writer_options)
    buffer.seek(0)
    return Image.open(buffer).convert("1")


def _draw_logo(canvas: Image.Image, x: int, y: int, max_w: int, max_h: int):
    """Draws logo from ASSETS_DIR/logo.png or renders a compact text fallback."""
    logo_path = settings.assets_dir / "logo.png"

    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            # Incolla sul canvas 1-bit mantenendo la trasparenza pulita
            logo_bg = Image.new("RGB", logo.size, (255, 255, 255))
            logo_bg.paste(logo, (0, 0), logo)
            logo_bw = logo_bg.convert("1")

            canvas.paste(logo_bw, (x, y))
            return
        except Exception:
            logger.exception("Error loading logo")

    # Fallback grafico compatto
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x, y, x + max_w, y + max_h], outline=0, width=1)
    font = _load_font(12, bold=True)
    draw.text((x + 8, y + 6), "LOGO", fill=0, font=font)


def generate_label_image(
    item_id: int, name: str, pn: str, shelf_position: str, barcode_value: str
) -> Path:
    """Build the 712x224 1-bit PNG label optimized for 89x28mm thermal labels."""
    settings.labels_dir.mkdir(parents=True, exist_ok=True)

    # Canvas 1-bit monocromatico puro (0=Nero, 1=Bianco)
    canvas = Image.new("1", (LABEL_WIDTH, LABEL_HEIGHT), 1)
    draw = ImageDraw.Draw(canvas)

    padding = 10
    y = padding

    # -------------------------------------------------------------
    # 1. TOP ROW: Logo (Left) + Info (Right) - Layout compatto per 28mm
    # -------------------------------------------------------------
    _draw_logo(canvas, x=padding, y=y, max_w=180, max_h=36)

    top_right_font = _load_font(16, bold=True)
    meta_font = _load_font(13, bold=False)

    tag_text = "I.E. NERVIANO"
    tag_bbox = top_right_font.getbbox(tag_text)
    tag_w = tag_bbox[2] - tag_bbox[0]
    draw.text((LABEL_WIDTH - padding - tag_w, y),
              tag_text, fill=0, font=top_right_font)

    shelf_text = f"Shelf: {shelf_position}"
    shelf_bbox = meta_font.getbbox(shelf_text)
    shelf_w = shelf_bbox[2] - shelf_bbox[0]
    draw.text((LABEL_WIDTH - padding - shelf_w, y + 20),
              shelf_text, fill=0, font=meta_font)

    y += 40

    # Divisore orizzontale sottile
    draw.line([(padding, y), (LABEL_WIDTH - padding, y)], fill=0, width=1)
    y += 5

    # -------------------------------------------------------------
    # 2. MIDDLE BAND: Nome Prodotto & P/N
    # -------------------------------------------------------------
    title_font = _load_font(16, bold=True)
    pn_font = _load_font(13, bold=True)

    truncated_name = name[:36] + "..." if len(name) > 36 else name
    draw.text((padding, y), truncated_name, fill=0, font=title_font)
    y += 20

    draw.text((padding, y), f"P/N: {pn}", fill=0, font=pn_font)
    y += 18

    # -------------------------------------------------------------
    # 3. BOTTOM PART: Barcode MASSIMO SPazio + Testo sotto
    # -------------------------------------------------------------
    barcode_img = _generate_barcode_image(barcode_value)

    text_font = _load_font(14, mono=True, bold=True)
    text_height = 16

    # Margine laterale minimo (20px per lato) per massimizzare la larghezza
    horizontal_margin = 20
    available_width = LABEL_WIDTH - (2 * horizontal_margin)
    available_height = LABEL_HEIGHT - y - padding - text_height

    # Calcolo fattore di scala
    scale_w = available_width / barcode_img.width
    scale_h = available_height / barcode_img.height
    scale = min(scale_w, scale_h)

    # Forza moltiplicatore INTERO per mantenere l'allineamento dei pixel neri
    if scale >= 1.0:
        scale = float(int(scale))

    new_w = max(1, int(barcode_img.width * scale))
    new_h = max(1, int(barcode_img.height * scale))

    # Resizing rigorosamente NEAREST per bordi netti
    barcode_img = barcode_img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Centra il barcode nella parte inferiore dell'etichetta
    barcode_x = horizontal_margin + (available_width - new_w) // 2
    canvas.paste(barcode_img, (barcode_x, y))
    y += new_h + 2

    # Valore leggibile centrato sotto il codice a barre
    bbox = text_font.getbbox(barcode_value)
    text_w = bbox[2] - bbox[0]
    text_x = horizontal_margin + (available_width - text_w) // 2
    draw.text((text_x, y), barcode_value, fill=0, font=text_font)

    output_path = settings.labels_dir / f"{item_id}.png"
    canvas.save(output_path, format="PNG")
    return output_path
