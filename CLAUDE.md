# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Raspberry Pi home automation system ("Haussteuerung") that controls lights and roller blinds (Jalousien) in a multi-floor house via Modbus TCP to a WAGO PLC. Three separate entry points exist — a web UI, an Alexa skill, and an automated daytime loop — all sharing the same `modbus.py` core. The web UI also shows live solar/battery data from the SMA energy system.

The working directory on the Raspberry Pi is `/home/pi/Haussteuerung/`. The `R:\` network drive on the Windows development machine is a Samba share pointing directly to that folder.

---

## System dependencies — what must be installed on the Pi

### System packages (apt)

```bash
sudo apt install python3 python3-pip
```

### Python packages (pip — install as the `pi` user)

```bash
pip3 install --user flask flask-ask pymodbus astral pytz requests urllib3 \
             icalendar recurring-ical-events yfinance
```

> **Important:** The system `urllib3` bundled with Raspberry Pi OS (Buster/Bullseye) has a bug that causes `LocationParseError` on HTTPS URLs. The `--user` install above overwrites it with a working version (`~/.local/lib/python3.x/site-packages/urllib3`).

> **Note:** `flask-ask` (Alexa skill) requires Python 3.8 and may need `pip3 install flask-ask==0.9.7 cryptography==3.3.2`.

### ngrok

Used to expose the Flask apps to the internet (Alexa skill requires a public HTTPS endpoint). Download the ARM binary from https://ngrok.com and place it at `/home/pi/bin/ngrok`. Configure in `ngrok.yml` in the project directory.

---

## Running the scripts

```bash
# Web interface (browser control + solar dashboard)
python3 website.py          # → http://192.168.2.165:5001/home

# Alexa skill handler
python3 SmartHome.py        # → port 5000 (Flask)

# Automated sunrise/sunset shutter control (runs indefinitely, 60 s loop)
python3 daytime.py
```

### Autostart via systemd

Run `sudo ./setup_autostart.sh` once to install and enable four systemd services:

| Service | Script | Port |
|---|---|---|
| `website.service` | `website.py` | 5001 |
| `smarthome.service` | `SmartHome.py` | 5000 |
| `daytime.service` | `daytime.py` | — |
| `ngrok.service` | ngrok tunnel | — |

Useful commands:
```bash
sudo systemctl status daytime website smarthome ngrok
sudo journalctl -u website -f        # live log Website
sudo journalctl -u smarthome -f      # live log Alexa
sudo journalctl -u daytime -f        # live log Daytime
sudo systemctl restart website       # restart a service
```

---

## Configuration (`config.json`)

All runtime configuration lives in `config.json` in the project directory. The file is read at startup and on every `/api/config` POST (no restart needed for most settings).

| Key | Type | Description |
|---|---|---|
| `SchlafRollo` | bool | Include bedroom shutter in sunrise/sunset automation |
| `christmas` | bool | Disable automation during holidays |
| `extremeHot` | bool | Close shutters at midday even in summer |
| `halbZuDelay` | int | Seconds the "fensterfront-halb-zu" scene waits between down and up |
| `smaTripower` | string\|null | IP of SMA Tripower PV inverter (Modbus TCP) |
| `smaSunnyIsland` | string\|null | IP of SMA Sunny Island battery inverter (Modbus TCP) |
| `smaSerial` | string\|null | Serial number of SMA Energy Meter (Speedwire filter; null = accept all) |
| `sunnyportalUser` | string | Sunny Portal login e-mail |
| `sunnyportalPass` | string | Sunny Portal password |
| `kalender_ics` | list | List of `{name, color, url}` iCal feed objects |

---

## Architecture

### `modbus.py` — the core library (WAGO PLC control)

All device control flows through here.

- **`connectMod()`** — connects to WAGO PLC at `192.168.2.100:502`
- **`readRegister(client)`** — reads 34 coils starting at Modbus address 12336
- **`createDig(regist)`** — builds a dict mapping room keys (e.g. `'Kueche'`, `'Schlafzimmer'`) to a 6-element list:
  `[currentState, lightOutputBit, blindUpBit, blindDownBit, label, registerOffset]`
  — `-1` means that function (light or blind) doesn't exist for that room
- **`handle(dig, ltyp, val, out)`** — sets bits in `out` list based on val (`'ein'`/`'aus'`/`'auf'`/`'zu'`). For lights: only toggles if not already in that state (reads current state from `dig`). For blinds: always triggers.
- **`write(client, out)`** — sends a **pulse** to coil register 12816: sets bits True, waits 101 ms, then resets all to False. This matches the impulse relay behavior of the WAGO hardware.
- **`createList()`** — returns a `[False]*63` output buffer passed through handle→write

Convenience functions (`allesUnten`, `allesOben`, `fensterfront`, `sofa`, `dunkel`, `hoch`, `hell`, `weg`) operate on predefined room lists.

### `website.py` — web backend

Flask app (port 5001) with these routes:

| Route | Method | Description |
|---|---|---|
| `/home` | GET | Renders `templates/index.html` |
| `/Modbus?typ=<key>&val=<val>` | GET | Direct Modbus command |
| `/Read` | GET | Current register state as JSON |
| `/api/config` | GET/POST | Read/write `config.json` |
| `/api/solar` | GET | Live solar/battery data from `SMAManager` |
| `/api/solar/history` | GET | Per-minute history (last 24 h rolling) |
| `/api/weather` | GET | Current conditions from Weather Underground station ISTOCK603 |
| `/api/weather/hourly` | GET | Hourly wind data for today |
| `/api/kalender` | GET | Upcoming events from configured iCal feeds (30-day window) |
| `/api/kalender/debug` | GET | Diagnostic info for calendar feeds |
| `/api/boerse/overview` | GET | DAX / S&P 500 / NASDAQ / Gold / Bitcoin via yfinance |
| `/api/boerse/chart` | GET | VWCE.DE price chart data via yfinance |
| `/api/szene/<name>` | GET | Execute a named shutter scene |

### `templates/index.html` + `static/java.js`

The web UI overlays clickable icons (light bulbs, shutter arrows) on a floor plan image. Two floor views (OG = Obergeschoss, DG = Dachgeschoss) switch via a transparent button over the staircase. `static/modbus.js` handles the actual AJAX calls to `/Modbus`. `java.js` handles layout positioning and the floor-switch logic.

### `SmartHome.py` — Alexa skill

Flask + flask-ask app. Defines two intents:
- `allgemein` — maps spoken room names and actions to modbus calls (e.g. "Wohnzimmer einschalten")
- `specialOne` — scene shortcuts (sofa, hoch/schlafen, dunkel, hell, weg)

### `daytime.py` — automated loop

Runs a `while True` loop with `time.sleep(60)`. Uses the `astral` library with a hardcoded location (Haig, Germany, 50.28°N 11.28°E) to compute sunrise/sunset. Raises shutters at sunrise, lowers them at sunset. Configuration flags are read from `config.json` on every loop iteration.

### `sma.py` — SMA solar energy integration

`SMAManager` class spawned as background threads by `website.py`. Three data sources are used in parallel:

#### 1. SMA Speedwire / Energy Meter (grid data, always running)

- Joins UDP multicast group `239.12.255.254:9522`
- Receives SMA Speedwire packets every ~1 s from the SMA Energy Meter (SHM 2.0)
- Parses OBIS records to extract grid consumption (`pconsume_w`) and feed-in (`psupply_w`) power, plus cumulative energy counters
- Daily kWh totals are derived from the counters relative to midnight baseline
- If `smaSerial` is set in config, only packets from that device serial are processed

#### 2. SMA Modbus TCP (PV inverter + battery inverter)

- Polls `smaTripower` IP every 10 s for PV power (`pv_w`) and daily yield (`today_pv_kwh`)
- Polls `smaSunnyIsland` IP every 10 s for battery SOC and charge/discharge power
- Compatible with **pymodbus 2.x** (`unit=` parameter) and **pymodbus 3.x** (`slave=` parameter): the `_mb_read()` helper tries `slave=` first and falls back to `unit=` on `TypeError`
- If `c.connect()` returns `False` (e.g. Modbus TCP not enabled on device), polling is silently skipped

> **Current limitation:** The Sunny Island at `192.168.2.116` does not have Modbus TCP enabled. A service technician must activate it via the installer menu. Until then, battery data comes from the Sunny Portal (see below).

#### 3. SMA Sunny Portal (PV + battery fallback, every 5 min)

Used when Modbus is unavailable. Logs in via the Sunny Portal website and polls a live-data JSON endpoint.

**Login flow (Keycloak-based):**

SMA migrated the Sunny Portal login from a classic ASP.NET form to a Keycloak OIDC identity provider (`login.sma.energy`). The login sequence in `_portal_login()`:

1. `GET /Templates/Login.aspx` → collect ASP.NET hidden fields (`__VIEWSTATE` etc.)
2. `POST` with `__EVENTTARGET = ctl00$ContentPlaceHolder1$LoginControl1$SmaId` → triggers a server-side redirect (302) to Keycloak with `prompt=none` (silent auth attempt)
3. Capture the `Location` header **without following** the redirect (`allow_redirects=False`)
4. Strip `prompt=none` from the Keycloak URL (silent auth would fail without an existing Keycloak session)
5. `GET` the Keycloak login page → find the `<form action="...">` URL
6. `POST` username + password to the Keycloak form action → Keycloak redirects back to `sunnyportal.com` with an auth code, completing the session

**Live data endpoint:**

After login, `_portal_poll()` calls:
```
GET https://www.sunnyportal.com/homemanager
Accept: application/json, text/javascript, */*; q=0.01
X-Requested-With: XMLHttpRequest
Referer: https://www.sunnyportal.com/FixedPages/HoManLive.aspx
```

The response is a JSON object with fields including:
- `PV` — current PV output in W (null at night when inverter is sleeping)
- `BatteryOut` — battery discharge power in W
- `BatteryIn` — battery charge power in W
- `BatteryChargeStatus` — state of charge in %

Battery data from the portal is only used if no fresh Modbus data exists (< 30 s old). `today_pv_kwh` is not available from this endpoint and remains null unless Tripower Modbus is active.

---

## Key constants

| Item | Value |
|---|---|
| WAGO PLC address | `192.168.2.100:502` |
| Raspberry Pi address | `192.168.2.165` |
| Read coils start | `12336` (34 bits) |
| Write coils start | `12816` (63 bits) |
| Pulse duration | `101 ms` |
| Speedwire multicast | `239.12.255.254:9522` |
| Portal poll interval | `300 s` (5 min) |
| Grid data stale after | `15 s` |
| Inverter/battery stale after | `360 s` |

## Modbus output bit mapping

Each room key in `createDig` has `[state, lightBit, blindUpBit, blindDownBit, ...]`. Light bits run 22–48; blind up/down pairs start at 0 (Fensterfront segments) through 21 (Schlafzimmer). A bit set to `-1` means that function is not wired.
