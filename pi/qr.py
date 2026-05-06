"""Decode a 5x5 grid-cell QR marker out of a JPEG frame.

Markers are printed as plain text `R{row}C{col}` with row/col in 0..4 (e.g.
`R2C3`). We try a sequence of decoders and preprocessing variants because
phone-screen and low-contrast captures often fail one approach but succeed at
another. The first symbol matching the pattern wins; otherwise we return the
raw text of any decoded symbol for logging.
"""
from __future__ import annotations
import logging
import re

log = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except Exception as e:
    HAS_CV2 = False
    log.warning("cv2/numpy unavailable (%s) — grid position will be NULL", e)

try:
    from pyzbar.pyzbar import decode as _zbar_decode
    HAS_ZBAR = True
except Exception as e:
    HAS_ZBAR = False
    log.warning("pyzbar unavailable (%s) — falling back to cv2.QRCodeDetector", e)

_PATTERN = re.compile(r"^R([0-4])C([0-4])$")


def _variants(gray):
    """Yield (name, image) preprocessing variants ordered cheap → aggressive."""
    yield "gray", gray
    h, w = gray.shape[:2]
    if max(h, w) < 1600:
        yield "gray_2x", cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    yield "equalized", cv2.equalizeHist(gray)
    yield "adaptive", cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5
    )


def _try_zbar(img) -> list[str]:
    if not HAS_ZBAR:
        return []
    try:
        return [
            s.data.decode("utf-8", errors="replace").strip() for s in _zbar_decode(img)
        ]
    except Exception:
        return []


_CV2_DETECTOR = None


def _try_cv2(img) -> list[str]:
    """OpenCV's QRCodeDetector. More robust to perspective/glare than pyzbar."""
    global _CV2_DETECTOR
    if _CV2_DETECTOR is None:
        _CV2_DETECTOR = cv2.QRCodeDetector()
    try:
        ok, decoded, _, _ = _CV2_DETECTOR.detectAndDecodeMulti(img)
        if ok and decoded:
            return [t.strip() for t in decoded if t]
        text, _, _ = _CV2_DETECTOR.detectAndDecode(img)
        return [text.strip()] if text else []
    except Exception:
        return []


def decode_grid_cell(jpeg: bytes) -> tuple[int | None, int | None, str | None]:
    if not HAS_CV2 or not jpeg:
        return None, None, None
    try:
        arr = np.frombuffer(jpeg, dtype=np.uint8)
        gray = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            return None, None, None
    except Exception as e:
        log.warning("QR decode setup failed: %s", e)
        return None, None, None

    raw_first: str | None = None
    for name, variant in _variants(gray):
        for decoder, texts in (
            ("zbar", _try_zbar(variant)),
            ("cv2", _try_cv2(variant)),
        ):
            for text in texts:
                if not text:
                    continue
                if raw_first is None:
                    raw_first = text
                m = _PATTERN.match(text)
                if m:
                    log.debug("QR matched via %s/%s: %s", name, decoder, text)
                    return int(m.group(1)), int(m.group(2)), text
    return None, None, raw_first
