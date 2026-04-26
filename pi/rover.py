"""
PalAI rover — polls Supabase rover_commands and drives motors.

- Polls public.rover_commands every POLL_INTERVAL seconds for new rows.
- Maintains rover_status.is_online via heartbeat.
- Stops automatically if no command arrives within COMMAND_TIMEOUT_SECONDS
  (covers the webapp's press-and-hold protocol if 'stop' is missed).
"""
from __future__ import annotations
import logging
import os
import signal
import threading
import time

from dotenv import load_dotenv
from supabase import create_client, Client

from motors import Motors
from camera import Camera
from sprayer import Sprayer
from gemini import classify_brownspot

load_dotenv()
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
# Silence noisy library loggers — only show our own events.
for _name in ("httpx", "httpcore", "hpack", "websockets", "urllib3"):
    logging.getLogger(_name).setLevel(logging.WARNING)

log = logging.getLogger("rover")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]
STATUS_ROW_ID = 1
HEARTBEAT_SECONDS = 5
POLL_INTERVAL = 0.15          # 150 ms (webapp inserts every 300 ms)
COMMAND_TIMEOUT_SECONDS = 0.6 # auto-stop if no fresh command within this window

VALID_COMMANDS = {"forward", "backward", "left", "right", "stop", "scan"}


class Rover:
    def __init__(self, sb: Client):
        self.sb = sb
        self.motors = Motors()
        self.camera = Camera(index=int(os.environ.get("WEBCAM_INDEX", "0")))
        self.sprayer = Sprayer(
            pin=int(os.environ.get("SPRAY_PIN", "26")),
            active_low=os.environ.get("SPRAY_ACTIVE_LOW", "1") == "1",
            duration=float(os.environ.get("SPRAY_DURATION_SECONDS", "2.0")),
        )
        self._cursor: str = ""           # last seen created_at (ISO string)
        self._last_cmd_at: float = 0.0
        self._scanning = threading.Event()
        self._stopping = threading.Event()

    # ── command dispatch ────────────────────────────────────────────────
    def handle_command(self, command: str) -> None:
        if command not in VALID_COMMANDS:
            log.warning("Unknown command: %s", command)
            return
        log.info("→ %s", command)
        self._last_cmd_at = time.monotonic()

        if command == "forward":
            self.motors.forward()
        elif command == "backward":
            self.motors.backward()
        elif command == "left":
            self.motors.left()
        elif command == "right":
            self.motors.right()
        elif command == "stop":
            self.motors.stop()
        elif command == "scan":
            self._start_scan()

    def _start_scan(self) -> None:
        if self._scanning.is_set():
            log.info("scan already in progress — ignoring duplicate")
            return
        self._scanning.set()
        threading.Thread(target=self._run_scan, name="scan", daemon=True).start()

    def _run_scan(self) -> None:
        try:
            self.scan()
        finally:
            self._scanning.clear()

    def scan(self) -> None:
        log.info("📷 capturing frame")
        jpeg = self.camera.capture_jpeg()
        log.info(
            "🧠 classifying with %s (%d KB)",
            os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
            len(jpeg) // 1024,
        )
        result = classify_brownspot(jpeg)

        sprayed = False
        label = result.get("label")
        confidence = float(result.get("confidence") or 0.0)

        if result.get("is_diseased") is True:
            log.info("🚨 brown spot detected (conf=%.2f) — spraying", confidence)
            try:
                self.sprayer.spray()
                sprayed = True
            except Exception as e:
                log.warning("spray failed: %s", e)
        elif label == "error":
            log.warning("scan error: %s", result.get("notes"))
        else:
            log.info("✅ %s (conf=%.2f)", label, confidence)

        try:
            self.sb.table("scan_results").insert({
                "is_diseased": result.get("is_diseased"),
                "label": label,
                "confidence": confidence,
                "notes": result.get("notes"),
                "sprayed": sprayed,
            }).execute()
        except Exception as e:
            log.warning("scan_results insert failed: %s", e)

    # ── polling loop ────────────────────────────────────────────────────
    def _initial_cursor(self) -> str:
        """Return the most recent created_at so we don't replay history."""
        try:
            res = (
                self.sb.table("rover_commands")
                .select("created_at")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            data = res.data or []
            if data and data[0].get("created_at"):
                return str(data[0]["created_at"])
        except Exception as e:
            log.warning("could not fetch initial cursor: %s", e)
        # Fall back to "epoch" — Postgres accepts this and we'll race-skip below.
        return "1970-01-01T00:00:00+00:00"

    def poll_loop(self) -> None:
        self._cursor = self._initial_cursor()
        log.info("Listening for rover commands…")

        while not self._stopping.is_set():
            try:
                res = (
                    self.sb.table("rover_commands")
                    .select("created_at, command")
                    .gt("created_at", self._cursor)
                    .order("created_at")
                    .limit(50)
                    .execute()
                )
                rows = res.data or []
                for row in rows:
                    ts = row.get("created_at")
                    cmd = row.get("command")
                    if cmd:
                        self.handle_command(cmd)
                    if ts and ts > self._cursor:
                        self._cursor = ts
            except Exception as e:
                log.warning("poll error: %s", e)

            self._stopping.wait(POLL_INTERVAL)

    # ── safety + heartbeat ──────────────────────────────────────────────
    def safety_loop(self) -> None:
        while not self._stopping.is_set():
            self._stopping.wait(0.2)
            if self._stopping.is_set():
                break
            now = time.monotonic()
            if self._last_cmd_at and now - self._last_cmd_at > COMMAND_TIMEOUT_SECONDS:
                self.motors.stop()
                self._last_cmd_at = 0.0

    def heartbeat_loop(self) -> None:
        self._set_online(True)
        try:
            while not self._stopping.is_set():
                try:
                    self.sb.table("rover_status").update(
                        {"is_online": True}
                    ).eq("id", STATUS_ROW_ID).execute()
                except Exception as e:
                    log.warning("heartbeat failed: %s", e)
                self._stopping.wait(HEARTBEAT_SECONDS)
        finally:
            self._set_online(False)

    def _set_online(self, value: bool) -> None:
        try:
            self.sb.table("rover_status").update({"is_online": value}).eq(
                "id", STATUS_ROW_ID
            ).execute()
            log.info("rover_status.is_online = %s", value)
        except Exception as e:
            log.warning("set_online(%s) failed: %s", value, e)

    # ── lifecycle ───────────────────────────────────────────────────────
    def request_stop(self, *_args) -> None:
        log.info("Shutdown requested")
        self._stopping.set()

    def cleanup(self) -> None:
        self.motors.cleanup()
        self.camera.close()
        self.sprayer.cleanup()


def main() -> None:
    sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    rover = Rover(sb)

    signal.signal(signal.SIGINT, rover.request_stop)
    signal.signal(signal.SIGTERM, rover.request_stop)

    threads = [
        threading.Thread(target=rover.poll_loop, name="poll", daemon=True),
        threading.Thread(target=rover.heartbeat_loop, name="heartbeat", daemon=True),
        threading.Thread(target=rover.safety_loop, name="safety", daemon=True),
    ]
    for t in threads:
        t.start()

    try:
        while not rover._stopping.is_set():
            rover._stopping.wait(0.5)
    finally:
        rover.request_stop()
        for t in threads:
            t.join(timeout=2)
        rover.cleanup()


if __name__ == "__main__":
    main()
