"""
L298N motor driver (gpiozero, BCM pins).

Pin map:
  IN1=17  left backward
  IN2=18  left forward
  IN3=27  right forward
  IN4=22  right backward
  ENA=12  left  PWM (speed)
  ENB=13  right PWM (speed)
"""
from __future__ import annotations
import logging

log = logging.getLogger(__name__)

try:
    from gpiozero import DigitalOutputDevice, PWMOutputDevice
    HAS_GPIO = True
except (ImportError, RuntimeError, OSError):
    HAS_GPIO = False
    log.warning("gpiozero not available — running in MOCK mode")

DEFAULT_SPEED = 0.7  # 0.0-1.0


class Motors:
    def __init__(self, speed: float = DEFAULT_SPEED):
        self.speed = max(0.0, min(1.0, speed))
        if not HAS_GPIO:
            self.IN1 = self.IN2 = self.IN3 = self.IN4 = None
            self.ENA = self.ENB = None
            return

        self.IN1 = DigitalOutputDevice(17)   # Left backward
        self.IN2 = DigitalOutputDevice(18)   # Left forward
        self.IN3 = DigitalOutputDevice(27)   # Right forward
        self.IN4 = DigitalOutputDevice(22)   # Right backward
        self.ENA = PWMOutputDevice(12, initial_value=0)
        self.ENB = PWMOutputDevice(13, initial_value=0)

    def _drive(self, in1: int, in2: int, in3: int, in4: int,
               left_pwm: float, right_pwm: float) -> None:
        if not HAS_GPIO:
            log.info("MOCK drive IN1=%d IN2=%d IN3=%d IN4=%d L=%.2f R=%.2f",
                     in1, in2, in3, in4, left_pwm, right_pwm)
            return
        (self.IN1.on if in1 else self.IN1.off)()
        (self.IN2.on if in2 else self.IN2.off)()
        (self.IN3.on if in3 else self.IN3.off)()
        (self.IN4.on if in4 else self.IN4.off)()
        self.ENA.value = left_pwm
        self.ENB.value = right_pwm

    def forward(self) -> None:
        self._drive(0, 1, 1, 0, self.speed, self.speed)

    def backward(self) -> None:
        self._drive(1, 0, 0, 1, self.speed, self.speed)

    def left(self) -> None:
        self._drive(0, 0, 1, 0, 0.0, self.speed)

    def right(self) -> None:
        self._drive(0, 1, 0, 0, self.speed, 0.0)

    def stop(self) -> None:
        self._drive(0, 0, 0, 0, 0.0, 0.0)

    def set_speed(self, s: float) -> None:
        self.speed = max(0.0, min(1.0, s))

    def cleanup(self) -> None:
        try:
            self.stop()
        except Exception:
            pass
        if not HAS_GPIO:
            return
        for dev in (self.IN1, self.IN2, self.IN3, self.IN4, self.ENA, self.ENB):
            try:
                if dev is not None:
                    dev.close()
            except Exception:
                pass
