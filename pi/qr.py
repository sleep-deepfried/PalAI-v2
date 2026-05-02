"""Decode a 5x5 grid-cell QR marker out of a JPEG frame.

Markers are printed as plain text `R{row}C{col}` with row/col in 0..4 (e.g.
`R2C3`). The first symbol that matches the pattern wins; if no symbol matches
we still return the raw text of any decoded symbol so it can be logged.
"""
from __future__ import annotations
import logging
import re

log = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    from pyzbar.pyzbar import decode as _zbar_decode
    HAS_DECODER = True
except Exception as e:
    HAS_DECODER = False
    log.warning("QR decoder unavailable (%s) — grid position will be NULL", e)

_PATTERN = re.compile(r"^R([0-4])C([0-4])$")


def decode_grid_cell(jpeg: bytes) -> tuple[int | None, int | None, str | None]:
    if not HAS_DECODER or not jpeg:
        return None, None, None
    try:
        arr = np.frombuffer(jpeg, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, None, None
        symbols = _zbar_decode(img)
    except Exception as e:
        log.warning("QR decode failed: %s", e)
        return None, None, None

    raw_first: str | None = None
    for sym in symbols:
        try:
            text = sym.data.decode("utf-8", errors="replace").strip()
        except Exception:
            continue
        if raw_first is None:
            raw_first = text
        m = _PATTERN.match(text)
        if m:
            return int(m.group(1)), int(m.group(2)), text
    return None, None, raw_first
