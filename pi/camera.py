"""USB webcam capture via OpenCV (mock fallback when cv2 / device unavailable)."""
from __future__ import annotations
import logging
import os
import threading
import time

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

# Where each captured frame is mirrored. Used by the preview server.
LAST_FRAME_PATH = os.environ.get("LAST_FRAME_PATH", "/tmp/palai_last.jpg")


class Camera:
    """Thread-safe webcam wrapper. capture_jpeg() and grab_jpeg() share a single
    cv2.VideoCapture under a lock so the preview server and the scanner can
    coexist without fighting over /dev/video0.
    """

    def __init__(self, index: int = 0):
        self.index = index
        self._cap = None
        self._lock = threading.Lock()
        self._last_jpeg: bytes | None = None
        self._last_capture_at: float = 0.0

    def _open_locked(self):
        if not HAS_CV2:
            return None
        cap = cv2.VideoCapture(self.index)
        if not cap.isOpened():
            log.warning("could not open /dev/video%d", self.index)
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        for _ in range(3):
            cap.read()
        return cap

    def _read_locked(self) -> bytes:
        if not HAS_CV2:
            return _MOCK_JPEG
        if self._cap is None:
            self._cap = self._open_locked()
        if self._cap is None:
            return _MOCK_JPEG
        ok, frame = self._cap.read()
        if not ok or frame is None:
            log.warning("frame read failed")
            return _MOCK_JPEG
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return _MOCK_JPEG
        return buf.tobytes()

    def _save(self, jpeg: bytes) -> None:
        try:
            tmp = LAST_FRAME_PATH + ".tmp"
            with open(tmp, "wb") as f:
                f.write(jpeg)
            os.replace(tmp, LAST_FRAME_PATH)
        except Exception as e:
            log.warning("could not save last frame: %s", e)

    def capture_jpeg(self) -> bytes:
        """Capture for the scanner. Always saves to disk."""
        with self._lock:
            jpeg = self._read_locked()
            self._last_jpeg = jpeg
            self._last_capture_at = time.time()
        self._save(jpeg)
        return jpeg

    def grab_jpeg(self, max_age: float = 0.4) -> bytes:
        """Get a fresh frame for the live preview. Reuses a recent capture
        when called many times per second; otherwise pulls a new frame.
        """
        with self._lock:
            age = time.time() - self._last_capture_at
            if self._last_jpeg is not None and age < max_age:
                return self._last_jpeg
            jpeg = self._read_locked()
            self._last_jpeg = jpeg
            self._last_capture_at = time.time()
        return jpeg

    def close(self) -> None:
        with self._lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception:
                    pass
                self._cap = None
