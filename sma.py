import socket
import struct
import threading
import time
from collections import deque
from datetime import datetime

try:
    # pymodbus >= 3.0
    from pymodbus.client import ModbusTcpClient as _MBClient
    _MODBUS_OK = True
except ImportError:
    try:
        # pymodbus 2.x fallback
        from pymodbus.client.sync import ModbusTcpClient as _MBClient
        _MODBUS_OK = True
    except ImportError:
        _MODBUS_OK = False

try:
    import requests as _requests
    _REQUESTS_OK = True
except ImportError:
    _REQUESTS_OK = False

_MCAST_GRP  = '239.12.255.254'
_MCAST_PORT = 9522
_STALE_GRID   = 15   # seconds before grid data is considered stale
_STALE_INV    = 360  # seconds before inverter/battery data is stale
_PORTAL_POLL  = 300  # seconds between Sunny Portal polls (5 min)

# SMA Modbus unit IDs and register addresses
# NOTE: Verify these against your device's Modbus fieldlist PDF.
# Addresses are 0-based as used in pymodbus read_input_registers().
_TRIPOWER_UNIT     = 3
_TRIPOWER_REG_PAC  = 30775  # AC power output (W), S32, 2 registers
_TRIPOWER_REG_DYWH = 30529  # Daily yield (Wh), U32, 2 registers

_ISLAND_UNIT       = 3
_ISLAND_REG_SOC    = 30845  # Battery SOC (%), U32, 2 registers; raw value = SOC * 100
_ISLAND_REG_PAC    = 30775  # Battery AC power (W), S32, 2 registers


class SMAManager:
    def __init__(self, tripower_ip=None, island_ip=None, shm_serial=None,
                 portal_user=None, portal_password=None):
        self._tripower_ip    = tripower_ip
        self._island_ip      = island_ip
        self._shm_serial     = int(shm_serial) if shm_serial else None
        self._portal_user    = portal_user
        self._portal_password = portal_password

        self._lock = threading.Lock()
        self._grid  = {}
        self._inv   = {}
        self._bat   = {}

        self._history    = deque(maxlen=1440)
        self._min_buf    = []
        self._min_bucket = None

        self._baseline      = {}
        self._baseline_date = None

        self._grid_ts = 0.0
        self._inv_ts  = 0.0
        self._bat_ts  = 0.0

        # Sunny Portal HTTP session (wiederverwendet zwischen Polls)
        self._portal_sess = None

    def start(self):
        threading.Thread(target=self._run_speedwire, daemon=True, name='sma-speedwire').start()
        if self._tripower_ip or self._island_ip:
            threading.Thread(target=self._run_modbus, daemon=True, name='sma-modbus').start()
        if self._portal_user and self._portal_password:
            threading.Thread(target=self._run_portal, daemon=True, name='sma-portal').start()

    # ── Public API ──────────────────────────────────────────────────────────

    def get_current(self):
        now = time.monotonic()
        with self._lock:
            grid_ok = bool(self._grid) and (now - self._grid_ts) < _STALE_GRID
            inv_ok  = bool(self._inv)  and (now - self._inv_ts)  < _STALE_INV
            bat_ok  = bool(self._bat)  and (now - self._bat_ts)  < _STALE_INV

            if not (grid_ok or inv_ok):
                return {'ok': False}

            return {
                'ok':               True,
                'pconsume_w':       self._grid.get('pconsume_w'),
                'psupply_w':        self._grid.get('psupply_w'),
                'pv_w':             self._inv.get('pv_w'),
                'battery_w':        self._bat.get('battery_w') if bat_ok else None,
                'battery_soc':      self._bat.get('battery_soc') if bat_ok else None,
                'today_supply_kwh': self._grid.get('today_supply_kwh'),
                'today_consume_kwh':self._grid.get('today_consume_kwh'),
                'today_pv_kwh':     self._inv.get('today_pv_kwh') if inv_ok else None,
                'last_update':      datetime.now().strftime('%H:%M:%S'),
            }

    def get_history(self):
        with self._lock:
            return list(self._history)

    # ── Speedwire listener (SHM 2.0 grid data) ─────────────────────────────

    def _run_speedwire(self):
        while True:
            try:
                self._speedwire_loop()
            except Exception as exc:
                print(f'[SMA Speedwire] {exc!r} — restart in 10 s')
                time.sleep(10)

    def _speedwire_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', _MCAST_PORT))
        mreq = struct.pack('4sL', socket.inet_aton(_MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1.0)
        try:
            while True:
                try:
                    data, _ = sock.recvfrom(4096)
                except socket.timeout:
                    continue
                parsed = _parse_speedwire(data)
                if not parsed:
                    continue
                if self._shm_serial and parsed.get('serial') != self._shm_serial:
                    continue
                self._update_grid(parsed)
        finally:
            sock.close()

    def _update_grid(self, p):
        today = datetime.now().strftime('%Y-%m-%d')
        with self._lock:
            if self._baseline_date != today:
                self._baseline_date = today
                self._baseline = {
                    'esupply':  p.get('esupply_wh', 0),
                    'econsume': p.get('econsume_wh', 0),
                }

            supply_wh  = p.get('esupply_wh', 0)
            consume_wh = p.get('econsume_wh', 0)

            self._grid = {
                'psupply_w':         round(p.get('psupply_w',  0), 1),
                'pconsume_w':        round(p.get('pconsume_w', 0), 1),
                'today_supply_kwh':  round((supply_wh  - self._baseline.get('esupply',  supply_wh))  / 1000, 3),
                'today_consume_kwh': round((consume_wh - self._baseline.get('econsume', consume_wh)) / 1000, 3),
            }
            self._grid_ts = time.monotonic()
            self._accumulate_minute()

    # ── Modbus poller (Tripower PV + Sunny Island battery) ──────────────────

    def _run_modbus(self):
        while True:
            try:
                self._modbus_poll()
            except Exception as exc:
                print(f'[SMA Modbus] {exc!r}')
            time.sleep(10)

    def _modbus_poll(self):
        if not _MODBUS_OK:
            return

        if self._tripower_ip:
            try:
                c = _MBClient(self._tripower_ip, port=502)
                if c.connect():
                    pv_w        = _read_s32(c, _TRIPOWER_REG_PAC,  _TRIPOWER_UNIT)
                    today_pv_wh = _read_u32(c, _TRIPOWER_REG_DYWH, _TRIPOWER_UNIT)
                    c.close()
                    pv_w = max(0, pv_w) if pv_w is not None else None
                    with self._lock:
                        self._inv = {
                            'pv_w':        pv_w,
                            'today_pv_kwh': round(today_pv_wh / 1000, 3) if today_pv_wh is not None else None,
                        }
                        self._inv_ts = time.monotonic()
            except Exception as exc:
                print(f'[SMA Tripower] {exc!r}')

        if self._island_ip:
            try:
                c = _MBClient(self._island_ip, port=502)
                if c.connect():
                    soc_raw  = _read_u32(c, _ISLAND_REG_SOC, _ISLAND_UNIT)
                    bat_w    = _read_s32(c, _ISLAND_REG_PAC, _ISLAND_UNIT)
                    c.close()
                    soc = round(soc_raw / 100.0, 1) if soc_raw is not None else None
                    with self._lock:
                        self._bat = {'battery_soc': soc, 'battery_w': bat_w}
                        self._bat_ts = time.monotonic()
            except Exception as exc:
                print(f'[SMA Sunny Island] {exc!r}', file=__import__('sys').stderr)

    # ── Sunny Portal poller (PV + Batterie via /homemanager API) ───────────────

    def _run_portal(self):
        while True:
            try:
                self._portal_poll()
            except Exception as exc:
                print(f'[SMA Portal] {exc!r}', file=__import__('sys').stderr)
            time.sleep(_PORTAL_POLL)

    def _portal_login(self):
        """Keycloak-Login für sunnyportal.com. Gibt authentifizierte Session zurück."""
        import re
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        if not _REQUESTS_OK:
            print('[SMA Portal] FEHLER: pip3 install requests', file=__import__('sys').stderr)
            return None

        BASE = 'https://www.sunnyportal.com'
        sess = _requests.Session()
        sess.headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        try:
            # 1. Login-Seite → Hidden-Fields
            r = sess.get(f'{BASE}/Templates/Login.aspx', timeout=30)
            hidden = {}
            for m in re.finditer(r'<input[^>]+type=["\']?hidden["\']?[^>]*>', r.text, re.I):
                tag = m.group(0)
                nm = re.search(r'name=["\']([^"\']+)["\']', tag)
                vl = re.search(r'value=["\']([^"\']*)["\']', tag)
                if nm:
                    hidden[nm.group(1)] = vl.group(1) if vl else ''

            # 2. SmaId-PostBack → 302-Redirect zu Keycloak
            r2 = sess.post(
                f'{BASE}/Templates/Login.aspx',
                data={**hidden,
                      '__EVENTTARGET':   'ctl00$ContentPlaceHolder1$LoginControl1$SmaId',
                      '__EVENTARGUMENT': ''},
                timeout=30, allow_redirects=False,
            )
            kc_silent = r2.headers.get('Location', '')
            if 'login.sma.energy' not in kc_silent:
                print('[SMA Portal] Kein Keycloak-Redirect', file=__import__('sys').stderr)
                return None

            # 3. prompt=none entfernen → echtes Login-Formular anzeigen
            parsed = urlparse(kc_silent)
            params = {k: v[0] for k, v in parse_qs(parsed.query, keep_blank_values=True).items()}
            params.pop('prompt', None)
            r3 = sess.get(urlunparse(parsed._replace(query=urlencode(params))), timeout=30)
            if 'login.sma.energy' not in r3.url:
                print('[SMA Portal] Keycloak-Seite nicht geladen', file=__import__('sys').stderr)
                return None

            # 4. Keycloak-Formular ausfüllen und absenden
            fm = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', r3.text, re.I)
            if not fm:
                print('[SMA Portal] Kein Keycloak-Formular', file=__import__('sys').stderr)
                return None
            action = fm.group(1).replace('&amp;', '&')
            if action.startswith('/'):
                p = urlparse(r3.url)
                action = f'{p.scheme}://{p.netloc}{action}'

            kc_h = {}
            for m in re.finditer(r'<input[^>]+type=["\']?hidden["\']?[^>]*>', r3.text, re.I):
                tag = m.group(0)
                nm = re.search(r'name=["\']([^"\']+)["\']', tag)
                vl = re.search(r'value=["\']([^"\']*)["\']', tag)
                if nm:
                    kc_h[nm.group(1)] = vl.group(1) if vl else ''

            r4 = sess.post(action,
                           data={**kc_h, 'username': self._portal_user,
                                 'password': self._portal_password},
                           timeout=30, allow_redirects=True)

            body_l = r4.text.lower()
            ok = ('logout' in body_l or 'abmelden' in body_l or
                  'homan' in r4.url.lower() or '/plants/' in r4.url.lower() or
                  ('sunnyportal.com' in r4.url and 'login' not in r4.url.lower()))
            if not ok:
                print('[SMA Portal] Login fehlgeschlagen', file=__import__('sys').stderr)
                return None

            print('[SMA Portal] Login OK ✓', file=__import__('sys').stderr)
            return sess

        except Exception as exc:
            print(f'[SMA Portal] Login-Fehler: {exc!r}', file=__import__('sys').stderr)
            return None

    def _portal_poll(self):
        """Holt Live-Daten vom /homemanager Endpunkt des Sunny Portals."""
        import sys
        if not _REQUESTS_OK:
            return
        BASE = 'https://www.sunnyportal.com'

        # Session aufbauen falls nötig
        if self._portal_sess is None:
            self._portal_sess = self._portal_login()
            if self._portal_sess is None:
                return

        sess = self._portal_sess
        try:
            r = sess.get(
                f'{BASE}/homemanager',
                headers={
                    'Accept':           'application/json, text/javascript, */*; q=0.01',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer':          f'{BASE}/FixedPages/HoManLive.aspx',
                },
                timeout=30,
            )
        except Exception as exc:
            print(f'[SMA Portal] /homemanager Fehler: {exc!r}', file=sys.stderr)
            self._portal_sess = None
            return

        # Session abgelaufen?
        if r.status_code != 200 or 'application/json' not in r.headers.get('Content-Type', ''):
            print('[SMA Portal] Session abgelaufen – Login beim nächsten Poll', file=sys.stderr)
            self._portal_sess = None
            return

        try:
            data = r.json()
        except Exception:
            print('[SMA Portal] Kein JSON von /homemanager', file=sys.stderr)
            self._portal_sess = None
            return

        # PV-Leistung (W) – kann nachts None sein
        pv_raw = data.get('PV')
        pv_w   = round(max(0.0, float(pv_raw)), 1) if pv_raw is not None else None

        # Batterie: BatteryOut = Entladen (positiv), BatteryIn = Laden (negativ)
        bat_out = data.get('BatteryOut')
        bat_in  = data.get('BatteryIn')
        soc     = data.get('BatteryChargeStatus')
        bat_w   = None
        if bat_out is not None and bat_in is not None:
            bat_w = round(float(bat_out) - float(bat_in), 1)
        soc_pct = round(float(soc), 1) if soc is not None else None

        now = time.monotonic()
        with self._lock:
            self._inv    = {'pv_w': pv_w, 'today_pv_kwh': None}
            self._inv_ts = now
            # Batterie aus Portal nur verwenden wenn kein frischer Modbus-Wert vorhanden
            if not (bool(self._bat) and (now - self._bat_ts) < 30):
                self._bat    = {'battery_soc': soc_pct, 'battery_w': bat_w}
                self._bat_ts = now

        print(f'[SMA Portal] PV={pv_w} W  Bat={bat_w} W  SOC={soc_pct}%', file=sys.stderr)

    # ── History accumulation (per-minute averages) ──────────────────────────

    def _accumulate_minute(self):
        """Called while lock is held. Flushes history when minute changes."""
        bucket = datetime.now().strftime('%H:%M')

        if self._min_bucket != bucket:
            if self._min_bucket is not None and self._min_buf:
                self._history.append(self._flush_minute_buf())
            self._min_bucket = bucket
            self._min_buf    = []

        self._min_buf.append({
            'psupply_w':  self._grid.get('psupply_w'),
            'pconsume_w': self._grid.get('pconsume_w'),
            'pv_w':       self._inv.get('pv_w'),
            'battery_w':  self._bat.get('battery_w'),
        })

    def _flush_minute_buf(self):
        def avg(key):
            vals = [r[key] for r in self._min_buf if r.get(key) is not None]
            return round(sum(vals) / len(vals), 0) if vals else None

        return {
            'time':       self._min_bucket,
            'psupply_w':  avg('psupply_w'),
            'pconsume_w': avg('pconsume_w'),
            'pv_w':       avg('pv_w'),
            'battery_w':  avg('battery_w'),
        }


# ── Modbus helpers ──────────────────────────────────────────────────────────

_S32_NAN = 0x80000000
_U32_NAN = 0xFFFFFFFF

def _mb_read(client, address, count, unit):
    """Reads input registers, compatible with pymodbus 2.x (unit=) and 3.x (slave=)."""
    try:
        return client.read_input_registers(address, count, slave=unit)
    except TypeError:
        return client.read_input_registers(address, count, unit=unit)

def _read_s32(client, address, unit):
    rr = _mb_read(client, address, 2, unit)
    if rr.isError():
        return None
    raw = (rr.registers[0] << 16) | rr.registers[1]
    if raw == _S32_NAN:
        return None
    return raw - 0x100000000 if raw & 0x80000000 else raw

def _read_u32(client, address, unit):
    rr = _mb_read(client, address, 2, unit)
    if rr.isError():
        return None
    raw = (rr.registers[0] << 16) | rr.registers[1]
    return None if raw == _U32_NAN else raw


# ── SMA Speedwire Energy Meter packet parser ────────────────────────────────
#
# Packet layout (SMA Speedwire / SMA Energy Meter protocol):
#   Offset  0–3 :  "SMA\x00" magic
#   Offset  4–7 :  tag header (length + type 0x6069)
#   Offset  8–11:  SusyID / version bytes
#   Offset 12–15:  ???
#   Offset 16–19:  ???
#   Offset 20–23:  serial number (big-endian U32)
#   Offset 24–27:  timestamp (big-endian U32, 100 ms ticks)
#   Offset 28+  :  OBIS records (4-byte header + 4 or 8 byte value)
#
# OBIS record header bytes: [channel, index, type, tariff]
#   type 4 → 4-byte U32 value (actual power, 0.1 W per unit)
#   type 8 → 8-byte U64 value (energy counter, 0.1 Wh per unit)
#   type 0, all zeros → end marker
#
# Key OBIS codes used here:
#   (0, 1, 4, 0) = 0:1.4.0  → grid consumption power  (pconsume, 0.1 W)
#   (0, 2, 4, 0) = 0:2.4.0  → grid feed-in power      (psupply,  0.1 W)
#   (0, 1, 8, 0) = 0:1.8.0  → grid consumption energy counter (0.1 Wh)
#   (0, 2, 8, 0) = 0:2.8.0  → grid feed-in energy counter     (0.1 Wh)

def _parse_speedwire(data):
    if len(data) < 32 or data[:4] != b'SMA\x00':
        return None
    try:
        serial = struct.unpack_from('>I', data, 20)[0]
        result = {'serial': serial}
        pos = 28

        while pos + 4 <= len(data):
            ch, idx, typ, tar = data[pos], data[pos+1], data[pos+2], data[pos+3]
            pos += 4

            if ch == 0 and idx == 0 and typ == 0:
                break  # end marker

            if typ == 4:
                if pos + 4 > len(data):
                    break
                val = struct.unpack_from('>I', data, pos)[0]
                pos += 4
                if (ch, idx) == (0, 1):
                    result['pconsume_w'] = val / 10.0
                elif (ch, idx) == (0, 2):
                    result['psupply_w'] = val / 10.0

            elif typ == 8:
                if pos + 8 > len(data):
                    break
                val = struct.unpack_from('>Q', data, pos)[0]
                pos += 8
                if (ch, idx) == (0, 1):
                    result['econsume_wh'] = val / 10.0
                elif (ch, idx) == (0, 2):
                    result['esupply_wh'] = val / 10.0
            else:
                # Unbekannter Typ – Länge schätzen (4 Byte) und überspringen
                # statt break, damit nachfolgende Records nicht verloren gehen
                pos += 4

        return result if len(result) > 1 else None
    except Exception:
        return None
