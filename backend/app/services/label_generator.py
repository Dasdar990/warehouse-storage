"""
Printable Code128 barcode label generation.

Optimized for 89mm x 28mm thermal label printers (203 DPI native resolution).
Canvas size: 712x224px (89mm * 8.0 bits/mm x 28mm * 8.0 bits/mm).
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
        "module_height": 10.0,
        "module_width": 0.25,
        "quiet_zone": 2.0,     # Riduciamo la quiet zone base per allargare di più il codice
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
    """Draws logo or renders a compact text fallback."""
    logo_path = settings.assets_dir / "logo.png"

    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            logo_bg = Image.new("RGB", logo.size, (255, 255, 255))
            logo_bg.paste(logo, (0, 0), logo)
            logo_bw = logo_bg.convert("1")

            canvas.paste(logo_bw, (x, y))
            return
        except Exception:
            logger.exception("Error loading logo")

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x, y, x + max_w, y + max_h], outline=0, width=2)
    font = _load_font(14, bold=True)
    draw.text((x + 8, y + 10), "LOGO", fill=0, font=font)


def generate_label_image(
    item_id: int, name: str, pn: str, shelf_position: str, barcode_value: str
) -> Path:
    """Build the 712x224 1-bit PNG label optimized for 89x28mm thermal labels."""
    settings.labels_dir.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("1", (LABEL_WIDTH, LABEL_HEIGHT), 1)
    draw = ImageDraw.Draw(canvas)

    padding = 8
    y = padding

    # -------------------------------------------------------------
    # 1. TOP ROW: Header molto compatto ma leggibile
    # -------------------------------------------------------------
    _draw_logo(canvas, x=padding, y=y, max_w=150, max_h=40)

    # Font ingranditi per l'header
    top_right_font = _load_font(24, bold=True)
    meta_font = _load_font(18, bold=False)

    tag_text = "I.E. NERVIANO"
    tag_bbox = top_right_font.getbbox(tag_text)
    tag_w = tag_bbox[2] - tag_bbox[0]
    draw.text((LABEL_WIDTH - padding - tag_w, y - 4),
              tag_text, fill=0, font=top_right_font)

    shelf_text = f"Shelf: {shelf_position}"
    shelf_bbox = meta_font.getbbox(shelf_text)
    shelf_w = shelf_bbox[2] - shelf_bbox[0]
    draw.text((LABEL_WIDTH - padding - shelf_w, y + 24),
              shelf_text, fill=0, font=meta_font)

    y += 48
    draw.line([(padding, y), (LABEL_WIDTH - padding, y)], fill=0, width=2)
    y += 6

    # -------------------------------------------------------------
    # 2. MIDDLE BAND: Testi "Huge" per il prodotto
    # -------------------------------------------------------------
    title_font = _load_font(28, bold=True)  # Nome prodotto enorme
    pn_font = _load_font(22, bold=True)     # Part Number enorme

    truncated_name = name[:36] + "..." if len(name) > 36 else name
    draw.text((padding, y), truncated_name, fill=0, font=title_font)
    y += 32

    draw.text((padding, y), f"P/N: {pn}", fill=0, font=pn_font)
    y += 28

    # -------------------------------------------------------------
    # 3. BOTTOM PART: Barcode stretching estremo
    # -------------------------------------------------------------
    text_font = _load_font(20, mono=True, bold=True)
    text_height = 24

    # Calcoliamo lo spazio effettivo rimasto prima di arrivare in fondo
    available_width = LABEL_WIDTH - (padding * 2)
    available_height = LABEL_HEIGHT - y - text_height - padding

    barcode_img = _generate_barcode_image(barcode_value)

    # Il calcolo magico:
    # 1. Asse X: calcoliamo quante volte entra il codice nella larghezza.
    #    Forziamo un moltiplicatore INT per evitare jitter (es. 700 / 150 = 4).
    scale_x = max(1, int(available_width / barcode_img.width))
    new_w = barcode_img.width * scale_x

    # 2. Asse Y: Tiriamo le barre in verticale prendendoci TUTTA l'altezza disponibile.
    new_h = available_height

    # Ridimensioniamo applicando scale_x e stretch_y separatamente.
    # Usiamo NEAREST per tenere i contrasti del laser nitidissimi
    barcode_img = barcode_img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Centriamo tutto
    barcode_x = padding + (available_width - new_w) // 2
    canvas.paste(barcode_img, (barcode_x, y))
    y += new_h + 2

    # Valore testuale stampato sotto il barcode (Font 20)
    bbox = text_font.getbbox(barcode_value)
    text_w = bbox[2] - bbox[0]
    text_x = padding + (available_width - text_w) // 2
    draw.text((text_x, y), barcode_value, fill=0, font=text_font)

    output_path = settings.labels_dir / f"{item_id}.png"
    canvas.save(output_path, format="PNG")
    return output_path
