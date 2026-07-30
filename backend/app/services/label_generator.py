"""
Printable Code128 barcode label generation.

Optimized for 101mm x 54mm thermal label printers (203 DPI native resolution).
Canvas size: 808x432px (101mm * 8.0 bits/mm x 54mm * 8.0 bits/mm).

Layout:
- Top Left: Logo (Original implementation)
- Top Right: I.E. NERVIANO + Shelf Position
- Middle: Product Name & P/N
- Bottom: Code128 Barcode + Human readable value (Optimized for entry-level scanners)
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

# Risoluzione nativa a 203 DPI per 101mm x 54mm (808x432 pixel)
LABEL_WIDTH = 808
LABEL_HEIGHT = 432

# --- Barcode generation tuning -------------------------------------------
# IMPORTANT: python-barcode's ImageWriter defaults to 300 DPI internally.
# If we don't pass `dpi` explicitly and match it to our printer's real
# resolution (203 DPI), `module_width` (in mm) gets converted to a
# non-integer pixel count per module. The writer then rounds bar-by-bar to
# avoid cumulative drift, so neighboring bars end up 2px/3px inconsistently
# -- the barcode still *decodes*, but the module ratios are slightly noisy,
# which is exactly what makes entry-level laser/CCD scanners take multiple
# passes instead of reading it instantly.
#
# Fix: generate at the printer's actual DPI, and pick a module width that
# is an exact integer number of pixels at that DPI.
BARCODE_DPI = 203
MODULE_PX = 3  # 3px/module @ 203 DPI is a good robustness/space compromise
MODULE_WIDTH_MM = MODULE_PX * 25.4 / BARCODE_DPI  # == 0.375mm, exact at 203 DPI

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
    """Render Code128 barcode at the printer's real DPI, with an exact
    integer pixel-per-module width so bar ratios stay clean end to end."""
    code128 = barcode.get_barcode_class("code128")
    writer = ImageWriter()

    writer_options = {
        "dpi": BARCODE_DPI,
        "module_height": 12.0,
        "module_width": MODULE_WIDTH_MM,
        "quiet_zone": 6.35,  # 0.25" -- the widely-used minimum entry-level
                             # scanners expect to reliably lock onto start/stop
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
    """Draws logo from ASSETS_DIR/logo.png or renders a compact text fallback (Original logic)."""
    logo_path = settings.assets_dir / "logo.png"

    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            # Per incollarlo sul canvas 1-bit, convertiamo temporaneamente in RGB/L
            logo_bg = Image.new("RGB", logo.size, (255, 255, 255))
            logo_bg.paste(logo, (0, 0), logo)
            logo_bw = logo_bg.convert("1")

            canvas.paste(logo_bw, (x, y))
            return
        except Exception:
            logger.exception("Error loading logo")

    # Graphic fallback if logo.png is not present
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x, y, x + max_w, y + max_h], outline=0, width=2)
    font = _load_font(18, bold=True)
    draw.text((x + 15, y + 12), "LOGO", fill=0, font=font)


def generate_label_image(
    item_id: int, name: str, pn: str, shelf_position: str, barcode_value: str
) -> Path:
    """Build the 808x432 1-bit PNG label for 101x54mm thermal paper."""
    settings.labels_dir.mkdir(parents=True, exist_ok=True)

    # Canvas in modalità '1' (1-bit monocromatico puro: 0=Nero, 1=Bianco)
    canvas = Image.new("1", (LABEL_WIDTH, LABEL_HEIGHT), 1)
    draw = ImageDraw.Draw(canvas)

    padding = 24
    y = padding

    # -------------------------------------------------------------
    # 1. TOP ROW: Logo (Left) + I.E. NERVIANO & Shelf (Right)
    # -------------------------------------------------------------
    _draw_logo(canvas, x=padding, y=y, max_w=260, max_h=80)

    top_right_font = _load_font(28, bold=True)
    meta_font = _load_font(22, bold=False)

    tag_text = "I.E. NERVIANO"
    tag_bbox = top_right_font.getbbox(tag_text)
    tag_w = tag_bbox[2] - tag_bbox[0]
    draw.text((LABEL_WIDTH - padding - tag_w, y + 4),
              tag_text, fill=0, font=top_right_font)

    shelf_text = f"Shelf: {shelf_position}"
    shelf_bbox = meta_font.getbbox(shelf_text)
    shelf_w = shelf_bbox[2] - shelf_bbox[0]
    draw.text((LABEL_WIDTH - padding - shelf_w, y + 40),
              shelf_text, fill=0, font=meta_font)

    y += 90

    # Linea divisoria orizzontale
    draw.line([(padding, y), (LABEL_WIDTH - padding, y)], fill=0, width=2)
    y += 12

    # -------------------------------------------------------------
    # 2. MIDDLE BAND: Nome Prodotto & P/N
    # -------------------------------------------------------------
    title_font = _load_font(30, bold=True)
    pn_font = _load_font(22, bold=True)

    truncated_name = name[:40] + "..." if len(name) > 40 else name
    draw.text((padding, y), truncated_name, fill=0, font=title_font)
    y += 38

    draw.text((padding, y), f"P/N: {pn}", fill=0, font=pn_font)
    y += 32

    barcode_img = _generate_barcode_image(barcode_value)

    text_font = _load_font(22, mono=True, bold=True)
    text_height = 26

    horizontal_margin = 40
    available_width = LABEL_WIDTH - (2 * horizontal_margin)
    available_height = LABEL_HEIGHT - y - padding - text_height

    # Calcolo della scala
    scale_w = available_width / barcode_img.width
    scale_h = available_height / barcode_img.height
    scale = min(scale_w, scale_h)

    # Il trucco per la Netum: forzare un moltiplicatore INTERO se stiamo ingrandendo
    # (es. 2.7 -> 2.0). Questo evita che i pixel vengano spalmati (jitter).
    if scale >= 1.0:
        scale = float(int(scale))
    else:
        # Downscaling a 1-bit con NEAREST campiona singoli pixel: può far
        # sparire o fondere barre sottili e sballare i rapporti tra moduli
        # senza che si veda a occhio -- causa tipica di scansioni lente o
        # intermittenti solo su alcuni barcode/nomi più lunghi del solito.
        # Con BARCODE_DPI/MODULE_WIDTH_MM allineati questo caso dovrebbe
        # essere ormai raro; se capita, meglio saperlo dai log.
        logger.warning(
            "Barcode '%s' più largo dello spazio disponibile (scale=%.2f); "
            "qualità di stampa a rischio, considera un barcode_value più corto.",
            barcode_value, scale,
        )

    new_w = max(1, int(barcode_img.width * scale))
    new_h = max(1, int(barcode_img.height * scale))

    # NEAREST mantiene i bordi dei pixel netti come lame
    barcode_img = barcode_img.resize((new_w, new_h), Image.Resampling.NEAREST)

    # Centra il barcode nell'area disponibile
    barcode_x = horizontal_margin + (available_width - new_w) // 2
    canvas.paste(barcode_img, (barcode_x, y))
    y += new_h + 4

    # Testo del codice a barre centrato sotto le barre
    bbox = text_font.getbbox(barcode_value)
    text_w = bbox[2] - bbox[0]
    text_x = horizontal_margin + (available_width - text_w) // 2
    draw.text((text_x, y), barcode_value, fill=0, font=text_font)

    output_path = settings.labels_dir / f"{item_id}.png"
    canvas.save(output_path, format="PNG")
    return output_path
