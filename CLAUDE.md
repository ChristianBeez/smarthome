# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A Raspberry Pi home automation system ("Haussteuerung") that controls lights and roller blinds (Jalousien) in a multi-floor house via Modbus TCP to a WAGO PLC. Three separate entry points exist — a web UI, an Alexa skill, and an automated daytime loop — all sharing the same `modbus.py` core.

## Running the scripts

```bash
# Web interface (browser control)
python website.py
# → runs on http://192.168.2.165:5000, route /home

# Alexa skill handler
python SmartHome.py
# → runs on port 5000 with flask-ask

# Automated sunrise/sunset shutter control (runs indefinitely, 60s loop)
python daytime.py
```

No build step, no package manager file — dependencies must be installed manually: `flask`, `flask-ask`, `pymodbus`, `astral`, `pytz`.

## Architecture

### `modbus.py` — the core library

All device control flows through here.

- **`connectMod()`** — connects to WAGO PLC at `192.168.2.100:502`
- **`readRegister(client)`** — reads 34 coils starting at Modbus address 12336
- **`createDig(regist)`** — builds a dict mapping room keys (e.g. `'Kueche'`, `'Schlafzimmer'`) to a 6-element list:
  `[currentState, lightOutputBit, blindUpBit, blindDownBit, label, registerOffset]`
  — `-1` means that function (light or blind) doesn't exist for that room
- **`handle(dig, ltyp, val, out)`** — sets bits in `out` list based on val (`'ein'`/`'aus'`/`'auf'`/`'zu'`). For lights: only toggles if not already in that state (reads current state from `dig`). For blinds: always triggers.
- **`write(client, out)`** — sends a **pulse** to coil register 12816: sets bits True, waits 101ms, then resets all to False. This matches the impulse relay behavior of the WAGO hardware.
- **`createList()`** — returns a `[False]*63` output buffer passed through handle→write

Convenience functions (`allesUnten`, `allesOben`, `fensterfront`, `sofa`, `dunkel`, `hoch`, `hell`, `weg`) operate on predefined room lists.

### `website.py` — web backend

Flask app with two routes:
- `GET /home` — renders `templates/index.html`
- `GET /Modbus?typ=<key>&val=<val>` — calls modbus directly (typ is a `createDig` key, val is `'true'`/`'auf'`/`'zu'`)
- `GET /Read` — returns current register state as JSON

### `templates/index.html` + `static/java.js`

The web UI overlays clickable icons (light bulbs, shutter arrows) on a floor plan image. Two floor views (OG = Obergeschoss, DG = Dachgeschoss) switch via a transparent button over the staircase. `static/modbus.js` handles the actual AJAX calls to `/Modbus`. `java.js` handles layout positioning and the floor-switch logic.

### `SmartHome.py` — Alexa skill

Flask + flask-ask app. Defines two intents:
- `allgemein` — maps spoken room names and actions to modbus calls (e.g. "Wohnzimmer einschalten")
- `specialOne` — scene shortcuts (sofa, hoch/schlafen, dunkel, hell, weg)

### `daytime.py` — automated loop

Runs a `while True` loop with `time.sleep(60)`. Uses the `astral` library with a hardcoded location (Haig, Germany, 50.28°N 11.28°E) to compute sunrise/sunset. Raises shutters at sunrise, lowers them at sunset. Configuration flags at the top of the file: `SchlafRollo`, `christmas`, `extremeHot`.

## Key constants

| Item | Value |
|---|---|
| WAGO PLC address | `192.168.2.100:502` |
| Raspberry Pi address | `192.168.2.165` |
| Read coils start | `12336` (34 bits) |
| Write coils start | `12816` (63 bits) |
| Pulse duration | `101ms` |

## Modbus output bit mapping

Each room key in `createDig` has `[state, lightBit, blindUpBit, blindDownBit, ...]`. Light bits run 22–48; blind up/down pairs start at 0 (Fensterfront segments) through 21 (Schlafzimmer). A bit set to `-1` means that function is not wired.
