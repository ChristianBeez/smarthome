from flask import Flask, render_template, request, jsonify, redirect, url_for
from modbus import *
import json
import os
import threading
import urllib.request
import ssl
from icalendar import Calendar as _ICalendar
import recurring_ical_events as _rie
from datetime import datetime, date, timedelta
import pytz
from sma import SMAManager

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"SchlafRollo": False, "christmas": False, "extremeHot": False, "halbZuDelay": 10}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=4)

app = Flask(__name__)

_cfg = load_config()
_sma = SMAManager(
    tripower_ip=_cfg.get('smaTripower'),
    island_ip=_cfg.get('smaSunnyIsland'),
    shm_serial=_cfg.get('smaSerial'),
    portal_user=_cfg.get('sunnyportalUser'),
    portal_password=_cfg.get('sunnyportalPass'),
)
_sma.start()

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/home')
def index():
    return render_template('index.html')

@app.route('/Modbus')
def Modbus():
    typ = request.args.get('typ')
    val = request.args.get('val')
    client = connectMod()
    regist = readRegister(client)
    dig = createDig(regist)
    out = createList()
    ltyp = [typ]
    handle(dig, ltyp, val, out)
    write(client,out)
    disconnectMod(client)
    return 'done'    

@app.route('/Read')
def getStatus():
    client = connectMod()
    data = readRegister(client)
    disconnectMod(client)
    return jsonify(result=data)

def _wu_fetch(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, context=ctx, timeout=8) as resp:
        return json.loads(resp.read())

def _ics_fetch(url):
    """ICS per urllib.request holen — umgeht Bug in altem urllib3 mit %40 in URL-Pfaden."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, context=ctx, timeout=5) as resp:
        return resp.read()

@app.route('/api/weather')
def get_weather():
    WU_KEY     = 'e52a7412771b4933aa7412771bf933b6'
    WU_STATION = 'ISTOCK603'
    url = (
        f'https://api.weather.com/v2/pws/observations/current'
        f'?stationId={WU_STATION}&format=json&units=m&apiKey={WU_KEY}'
    )
    try:
        raw = _wu_fetch(url)
        return app.response_class(json.dumps(raw), mimetype='application/json')
    except Exception as e:
        return jsonify(error=str(e)), 502

@app.route('/api/weather/hourly')
def get_weather_hourly():
    """Stündliche WU-Stationsdaten für heute — Wind-Chart."""
    from datetime import date as _date
    WU_KEY     = 'e52a7412771b4933aa7412771bf933b6'
    WU_STATION = 'ISTOCK603'
    url = (
        f'https://api.weather.com/v2/pws/observations/hourly/7day'
        f'?stationId={WU_STATION}&format=json&units=m&numericPrecision=decimal&apiKey={WU_KEY}'
    )
    try:
        raw   = _wu_fetch(url)
        today = str(_date.today())
        result = []
        for obs in raw.get('observations', []):
            if obs.get('obsTimeLocal', '').startswith(today):
                m = obs.get('metric', {})
                result.append({
                    'time':        obs['obsTimeLocal'][11:16],
                    'windAvg':     round(m.get('windspeedAvg', 0) or 0, 1),
                    'windBoe':     round(m.get('windgustHigh', 0) or 0, 1),
                    'windDir':     obs.get('winddirAvg', 0),
                })
        return jsonify(hourly=result)
    except Exception as e:
        return jsonify(error=str(e)), 502

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

BOOL_KEYS = {'SchlafRollo', 'christmas', 'extremeHot'}
NUM_KEYS  = {'halbZuDelay'}

@app.route('/api/config', methods=['POST'])
def set_config():
    cfg = load_config()
    data = request.get_json()
    key = data.get('key') if data else None
    if key in BOOL_KEYS:
        cfg[key] = bool(data['value'])
        save_config(cfg)
        return jsonify(success=True, config=cfg)
    if key in NUM_KEYS:
        cfg[key] = max(1, int(data['value']))
        save_config(cfg)
        return jsonify(success=True, config=cfg)
    return jsonify(success=False), 400

@app.route('/api/solar')
def api_solar():
    data = _sma.get_current()
    if not data.get('ok'):
        return jsonify(ok=False, error='Keine SMA-Daten empfangen'), 503
    return jsonify(data)

@app.route('/api/solar/history')
def api_solar_history():
    return jsonify(history=_sma.get_history())

@app.route('/api/kalender/debug')
def api_kalender_debug():
    cfg = load_config()
    calendars = cfg.get('kalender_ics', [])
    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz)
    today = now.date()
    horizon = today + timedelta(days=30)
    start_dt = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=tz)
    end_dt   = datetime(horizon.year, horizon.month, horizon.day, 23, 59, 59, tzinfo=tz)
    result = []
    for cal in calendars:
        info = {'name': cal['name'], 'url_ok': False, 'event_count': 0, 'error': None, 'sample': []}
        try:
            content = _ics_fetch(cal['url'])
            info['http_status'] = 200
            info['url_ok'] = True
            gcal = _ICalendar.from_ical(content)
            raw_events = list(_rie.of(gcal).between(start_dt, end_dt))
            info['event_count'] = len(raw_events)
            for ev in raw_events[:3]:
                dtstart = ev.get('DTSTART').dt
                info['sample'].append({
                    'title': str(ev.get('SUMMARY', '')),
                    'dtstart': str(dtstart),
                    'type': type(dtstart).__name__,
                })
        except Exception as e:
            import traceback
            info['error'] = traceback.format_exc()
        result.append(info)
    return jsonify({'range': [str(start_dt), str(end_dt)], 'calendars': result})


@app.route('/api/kalender')
def api_kalender():
    cfg = load_config()
    calendars = cfg.get('kalender_ics', [])
    tz = pytz.timezone('Europe/Berlin')
    now = datetime.now(tz)
    today = now.date()
    horizon = today + timedelta(days=30)
    start_dt = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=tz)
    end_dt   = datetime(horizon.year, horizon.month, horizon.day, 23, 59, 59, tzinfo=tz)
    events = []
    for cal in calendars:
        try:
            content = _ics_fetch(cal['url'])
            gcal = _ICalendar.from_ical(content)
            for component in _rie.of(gcal).between(start_dt, end_dt):
                dtstart = component.get('DTSTART').dt
                dtend_prop = component.get('DTEND')
                dtend = dtend_prop.dt if dtend_prop else dtstart
                all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)
                if all_day:
                    start_date = dtstart
                    end_date = dtend if isinstance(dtend, date) else dtend.date()
                    start_time = end_time = ''
                else:
                    if dtstart.tzinfo is None:
                        dtstart = tz.localize(dtstart)
                    if dtend.tzinfo is None:
                        dtend = tz.localize(dtend)
                    start_date = dtstart.astimezone(tz).date()
                    end_date   = dtend.astimezone(tz).date()
                    start_time = dtstart.astimezone(tz).strftime('%H:%M')
                    end_time   = dtend.astimezone(tz).strftime('%H:%M')
                events.append({
                    'title':     str(component.get('SUMMARY', '(kein Titel)')),
                    'start':     start_date.isoformat(),
                    'end':       end_date.isoformat(),
                    'allDay':    all_day,
                    'startTime': start_time,
                    'endTime':   end_time,
                    'calendar':  cal['name'],
                    'color':     cal['color'],
                })
        except Exception as e:
            print(f"Kalender-Fehler {cal.get('name', '?')}: {e}")
    events.sort(key=lambda e: (e['start'], e['startTime']))
    return jsonify(events)


_VALID_SCENES = {
    'fensterfront-hoch', 'fensterfront-halb-zu', 'fensterfront-zu',
    'og-alles-aus', 'og-jalousie-hoch', 'og-jalousie-runter',
    'dg-alles-aus', 'dg-jalousie-hoch', 'dg-jalousie-runter',
    'alles-aus', 'alles-jalousie-hoch', 'alles-jalousie-runter',
}

@app.route('/api/szene/<name>')
def api_szene(name):
    if name not in _VALID_SCENES:
        return jsonify(ok=False, error='Unbekannte Szene'), 400

    cfg   = load_config()
    delay = cfg.get('halbZuDelay', 10)

    def run_scene():
        client = connectMod()
        if not client:
            return
        regist = readRegister(client)
        dig    = createDig(regist)
        out    = createList()

        if name == 'fensterfront-halb-zu':
            out = fensterfront(dig, 'zu', out)
            write(client, out)
            disconnectMod(client)
            time.sleep(delay)
            client2 = connectMod()
            if not client2:
                return
            regist2 = readRegister(client2)
            dig2    = createDig(regist2)
            out2    = createList()
            out2 = fensterfront(dig2, 'auf', out2)
            write(client2, out2)
            disconnectMod(client2)
            return

        if name == 'fensterfront-hoch':
            out = fensterfront(dig, 'auf', out)
        elif name == 'fensterfront-zu':
            out = fensterfront(dig, 'zu', out)
        elif name == 'og-alles-aus':
            out = allesUnten(dig, 'aus', out)
        elif name == 'og-jalousie-hoch':
            out = allesUnten(dig, 'auf', out)
        elif name == 'og-jalousie-runter':
            out = allesUnten(dig, 'zu', out)
        elif name == 'dg-alles-aus':
            out = allesOben(dig, 'aus', out)
        elif name == 'dg-jalousie-hoch':
            out = allesOben(dig, 'auf', out)
        elif name == 'dg-jalousie-runter':
            out = allesOben(dig, 'zu', out)
        elif name == 'alles-aus':
            out = alles(dig, 'aus', out)
        elif name == 'alles-jalousie-hoch':
            out = alles(dig, 'auf', out)
        elif name == 'alles-jalousie-runter':
            out = alles(dig, 'zu', out)

        write(client, out)
        disconnectMod(client)

    threading.Thread(target=run_scene, daemon=True).start()
    resp = {'ok': True}
    if name == 'fensterfront-halb-zu':
        resp['delay'] = delay
    return jsonify(resp)


_BOERSE_TICKERS = [
    ('DAX',     '^GDAXI',  ''),
    ('S&P 500', '^GSPC',   ''),
    ('NASDAQ',  '^IXIC',   ''),
    ('Gold',    'GC=F',    'USD'),
    ('Bitcoin', 'BTC-USD', 'USD'),
]

_VWCE_SYMBOL = 'VWCE.DE'

_CHART_PERIODS = {
    '1m':  ('1mo',  '1d'),
    '3m':  ('3mo',  '1d'),
    '1j':  ('1y',   '1wk'),
    '5j':  ('5y',   '1mo'),
}


@app.route('/api/boerse/overview')
def api_boerse_overview():
    try:
        import yfinance as yf
        result = []
        for name, sym, cur_override in _BOERSE_TICKERS:
            t = yf.Ticker(sym)
            fi = t.fast_info
            price = fi.last_price
            prev  = fi.previous_close
            if price is None or prev is None:
                hist = t.history(period='2d')
                if len(hist) >= 1:
                    price = float(hist['Close'].iloc[-1])
                    prev  = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else price
                else:
                    price = prev = 0.0
            chg = float(price) - float(prev)
            pct = (chg / float(prev) * 100) if prev else 0.0
            result.append({
                'name':      name,
                'symbol':    sym,
                'price':     round(float(price), 2),
                'change':    round(chg, 2),
                'changePct': round(pct, 2),
                'currency':  cur_override or (fi.currency or ''),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify(error=str(e)), 502


@app.route('/api/boerse/chart')
def api_boerse_chart():
    try:
        import yfinance as yf
        period = request.args.get('period', '1j')
        yf_period, interval = _CHART_PERIODS.get(period, ('1y', '1wk'))
        t    = yf.Ticker(_VWCE_SYMBOL)
        hist = t.history(period=yf_period, interval=interval)
        labels = [str(d.date()) for d in hist.index]
        prices = [round(float(p), 2) for p in hist['Close']]
        return jsonify(labels=labels, prices=prices, symbol=_VWCE_SYMBOL)
    except Exception as e:
        return jsonify(error=str(e)), 502


if __name__ == "__main__":
    ##app.run(debug=True)
    app.run(host="0.0.0.0", port=5001, debug=False)
    