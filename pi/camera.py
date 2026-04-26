"""USB webcam capture via OpenCV (mock fallback when cv2 / device unavailable)."""
from __future__ import annotations
import logging

log = logging.getLogger(__name__)

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    log.warning("cv2 not available — Camera will return mock frames")


# 1×1 black JPEG (precomputed) so mock mode still produces valid bytes.
_MOCK_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605"
    "0807070709090808090b0e0c0b0a0a0b160f10101117151919181c1c1c1c1c"
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    "ffffc00011080001000103012200021101031101ffc4001f00000105010101"
    "01010100000000000000000102030405060708090a0bffc4001f0100030101"
    "01010101010101010000000000000102030405060708090a0bffda000c0301"
    "00021103110000000007ffd9"
)


class Camera:
    def __init__(self, index: int = 0):
        self.index = index
        self._cap = None

    def _open(self):
        if not HAS_CV2:
            return None
        cap = cv2.VideoCapture(self.index)
        if not cap.isOpened():
            log.warning("could not open /dev/video%d", self.index)
            return None
        # Modest resolution — Gemini doesn't need 4K, and smaller JPEGs upload faster.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # Warm up: throw away the first few frames so AE/AWB settle.
        for _ in range(3):
            cap.read()
        return cap

    def capture_jpeg(self) -> bytes:
        if not HAS_CV2:
            return _MOCK_JPEG
        if self._cap is None:
            self._cap = self._open()
        if self._cap is None:
            return _MOCK_JPEG
        ok, frame = self._cap.read()
        if not ok or frame is None:
            log.warning("frame read failed — returning mock")
            return _MOCK_JPEG
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            log.warning("jpeg encode failed — returning mock")
            return _MOCK_JPEG
        return buf.tobytes()

    def close(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
