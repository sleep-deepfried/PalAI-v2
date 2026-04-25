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
   ```

## Notes

- Auto-stop safety: motors halt if no command arrives within 600ms (covers tab close / WiFi drop).
- `scan()` in `rover.py` is a placeholder — wire your servo / sensor / camera there.
- Without GPIO available (e.g. on a Mac), `motors.py` runs in mock mode and just logs.
