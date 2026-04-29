"""Quick hardware sanity check — bypasses Supabase entirely.

Usage:  python test_motors.py

Drives forward, backward, left, right for 1.5s each, then stops.
If nothing moves here, the issue is hardware (power, wiring, L298N
ENA/ENB jumpers, motor connections), not the dashboard or polling.

Common gotchas:
- L298N ships with ENA/ENB jumpers ON — these short ENA to 5V and
  override the PWM input. REMOVE both jumpers for PWM speed control.
- Motor supply (V_motor) must be powered separately (e.g., a battery
  pack) — the Pi cannot push enough current through its 5V rail.
- Motor power ground must be tied to the Pi's GND.
"""
import logging
import time

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

from motors import Motors

m = Motors(speed=0.9)
print("forward 1.5s")
m.forward()
time.sleep(1.5)
print("stop 0.5s")
m.stop()
time.sleep(0.5)

print("backward 1.5s")
m.backward()
time.sleep(1.5)
m.stop()
time.sleep(0.5)

print("left (tank) 1.5s")
m.left()
time.sleep(1.5)
m.stop()
time.sleep(0.5)

print("right (tank) 1.5s")
m.right()
time.sleep(1.5)
m.stop()

print("done")
m.cleanup()
