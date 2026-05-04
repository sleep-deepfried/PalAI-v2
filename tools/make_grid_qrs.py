"""Generate the 25 grid-cell QR markers (R0C0..R4C4).

Outputs:
  grid_qrs/R{r}C{c}.png      — one QR per cell, with a label underneath
  grid_qrs/sheet.pdf         — all 25 on a single A4 sheet, ready to print

Run:
  pip install "qrcode[pil]"
  python tools/make_grid_qrs.py
"""
from __future__ import annotations
import os

import qrcode
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = "grid_qrs"
GRID_SIZE = 5
QR_BOX = 12       # pixels per QR module
QR_BORDER = 4     # quiet zone in modules
LABEL_H = 40      # px reserved under each QR for the text label


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",   # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_one(text: str) -> Image.Image:
    qr = qrcode.QRCode(box_size=QR_BOX, border=QR_BORDER)
    qr.add_data(text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    w, h = qr_img.size
    canvas = Image.new("RGB", (w, h + LABEL_H), "white")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font = _font(28)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, h + 4), text, fill="black", font=font)
    return canvas


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    tiles: list[Image.Image] = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            text = f"R{r}C{c}"
            img = make_one(text)
            img.save(os.path.join(OUT_DIR, f"{text}.png"))
            tiles.append(img)
    print(f"wrote {len(tiles)} PNGs to {OUT_DIR}/")

    # A4 sheet at 150 DPI is 1240x1754. 5 cols × 5 rows fits comfortably.
    sheet_w, sheet_h = 1240, 1754
    margin = 30
    cell_w = (sheet_w - margin * 2) // GRID_SIZE
    cell_h = (sheet_h - margin * 2) // GRID_SIZE
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    for i, tile in enumerate(tiles):
        r, c = divmod(i, GRID_SIZE)
        scale = min(cell_w / tile.width, cell_h / tile.height) * 0.9
        tw, th = int(tile.width * scale), int(tile.height * scale)
        resized = tile.resize((tw, th), Image.LANCZOS)
        x = margin + c * cell_w + (cell_w - tw) // 2
        y = margin + r * cell_h + (cell_h - th) // 2
        sheet.paste(resized, (x, y))

    sheet_path = os.path.join(OUT_DIR, "sheet.pdf")
    sheet.save(sheet_path, "PDF", resolution=150.0)
    print(f"wrote printable sheet to {sheet_path}")


if __name__ == "__main__":
    main()
