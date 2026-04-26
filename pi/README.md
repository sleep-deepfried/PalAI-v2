# PalAI Rover (Raspberry Pi)

Listens to Supabase `rover_commands` inserts and drives the L298N motor pair.
Reports `rover_status.is_online` so the webapp dashboard can show liveness.

## Hardware

L298N dual H-bridge wired to BCM pins:

| Signal | Pin | Purpose            |
|--------|-----|--------------------|
| IN1    | 17  | Left motor backward |
| IN2    | 18  | Left motor forward  |
| IN3    | 27  | Right motor forward |
| IN4    | 22  | Right motor backward |
| ENA    | 12  | Left PWM (speed)    |
| ENB    | 13  | Right PWM (speed)   |
| RELAY  | 26  | Spray relay IN (active-LOW) |

USB webcam plugs into any USB port and shows up as `/dev/video0`. Add the user
to the `video` group: `sudo usermod -aG video $USER` and re-login.

## Setup (Raspberry Pi OS)

```bash
# 1. System packages (gpiozero + lgpio backend, prebuilt — no compiler needed)
sudo apt update
sudo apt install -y python3-gpiozero python3-lgpio

# 2. Code
cd ~
git clone git@github.com:sleep-deepfried/PalAI-v2.git
cd PalAI-v2/pi

# 3. Virtualenv that can see the apt-installed gpiozero/lgpio
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env       # already has the Supabase URL + anon key
python rover.py
```

## Run as a service

```bash
sudo cp rover.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rover
journalctl -u rover -f
```

## Supabase prerequisites

1. Database → Replication: enable on `rover_commands`.
2. Run once in SQL editor:
   ```sql
   alter table rover_commands enable row level security;
   create policy "anon insert commands" on rover_commands
     for insert to anon with check (true);

   alter table rover_status enable row level security;
   create policy "anon read status"   on rover_status for select to anon using (true);
   create policy "anon update status" on rover_status for update to anon
     using (id = 1) with check (id = 1);

   insert into rover_status (id, is_online) values (1, false)
     on conflict (id) do nothing;

   create table if not exists scan_results (
     id           uuid primary key default gen_random_uuid(),
     created_at   timestamptz not null default now(),
     is_diseased  boolean,
     label        text,
     confidence   double precision,
     notes        text,
     sprayed      boolean not null default false
   );
   alter table scan_results enable row level security;
   create policy "anon read scan_results"   on scan_results for select to anon using (true);
   create policy "anon insert scan_results" on scan_results for insert to anon with check (true);
   ```
3. Database → Replication: enable on `scan_results` so the webapp toast fires in real time.

## Notes

- Auto-stop safety: motors halt if no command arrives within 600ms (covers tab close / WiFi drop).
- `scan()` captures a frame from the USB webcam, asks Gemini whether it sees rice brown spot, sprays the relay if positive, and posts the result to `scan_results` — the webapp toasts on insert.
- Without GPIO / cv2 available (e.g. on a Mac), `motors.py`, `sprayer.py`, and `camera.py` run in mock mode.

## Smoke tests

```bash
# Camera
python -c "import cv2; cam=cv2.VideoCapture(0); ok,_=cam.read(); print('camera ok' if ok else 'camera fail'); cam.release()"

# Spray relay (clicks on for 2s)
python -c "from gpiozero import OutputDevice; import time; r=OutputDevice(26, active_high=False); r.on(); time.sleep(2); r.off()"
```
