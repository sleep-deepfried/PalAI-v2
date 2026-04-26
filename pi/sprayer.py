"""Spray relay control via gpiozero. Polarity-aware so .on() always sprays."""
from __future__ import annotations
import logging
import time

log = logging.getLogger(__name__)

try:
    from gpiozero import OutputDevice
    HAS_GPIO = True
except (ImportError, RuntimeError, OSError):
    HAS_GPIO = False
    log.warning("gpiozero not available — Sprayer running in MOCK mode")


class Sprayer:
    def __init__(self, pin: int = 26, active_low: bool = True, duration: float = 2.0):
        self.pin = pin
        self.active_low = active_low
        self.duration = duration
        self._dev = None
        if not HAS_GPIO:
            return
        # active_high=False inverts logic so .on() sprays even on active-LOW relays.
        self._dev = OutputDevice(
            pin, active_high=not active_low, initial_value=False
        )

    def spray(self) -> None:
        log.info(
            "💧 spray ON (pin=%d active_low=%s duration=%.1fs)",
            self.pin, self.active_low, self.duration,
        )
        if self._dev is None:
            time.sleep(self.duration)
        else:
            self._dev.on()
            try:
                time.sleep(self.duration)
            finally:
                self._dev.off()
        log.info("💧 spray OFF")

    def cleanup(self) -> None:
        if self._dev is None:
            return
        try:
            self._dev.off()
            self._dev.close()
        except Exception:
            pass
        self._dev = None
