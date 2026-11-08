"""SQLite persistence: settings, portfolio positions, strategies, research notes."""
import sqlite3, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "quantedge.db")
DEFAULTS = {
    "theme": "Navy Terminal", "accent": "Emerald", "scale": "100%",
    "default_tf": "6M", "chart_type": "Line", "grid": True, "show_volume": True,
    "candle_style": "Green / Red", "csv_dir": "", "startup": "Overview",
    "confirm_delete": True, "capital": 1000000, "fee_bps": 5,
    "watchlist": ["RELIANCE", "TCS", "INFY", "BTC", "ETH", "SOL"],
}
cfg = dict(DEFAULTS)
_con = None

SEED_STRATEGIES = [
    ("EMA 20/50 Trend", "EMA Crossover", {"fast": 20, "slow": 50, "trend_filter": False, "rsi_filter": False}, 8, 0),
    ("RSI Reversion 30/55", "RSI Mean Reversion", {"period": 14, "buy_below": 30, "sell_above": 55, "trend_filter": False, "rsi_filter": False}, 6, 12),
    ("MACD Momentum", "MACD Momentum", {"fast": 12, "slow": 26, "signal": 9, "trend_filter": True, "rsi_filter": False}, 8, 0),
    ("Donchian Breakout 20/10", "Donchian Breakout", {"lookback": 20, "exit_lookback": 10, "trend_filter": False, "rsi_filter": False}, 7, 0),
    ("AI Composite Score", "AI Composite Score", {"buy_score": 1.5, "exit_score": 0.0, "trend_filter": False, "rsi_filter": True}, 8, 0),
]
SEED_POSITIONS = [("RELIANCE", 120, 60), ("TCS", 60, 150), ("HDFCBANK", 150, 100), ("INFY", 140, 200),
                  ("ITC", 400, 45), ("BTC", 0.03, 120), ("ETH", 0.4, 90)]


def init():
    global _con
    if _con is not None:
        return _con
    _con = sqlite3.connect(DB_PATH)
    _con.row_factory = sqlite3.Row
    _con.executescript("""
    CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
    CREATE TABLE IF NOT EXISTS positions(symbol TEXT PRIMARY KEY, qty REAL, entry REAL);
    CREATE TABLE IF NOT EXISTS strategies(name TEXT PRIMARY KEY, type TEXT, params TEXT, sl REAL, tp REAL, notes TEXT);
    CREATE TABLE IF NOT EXISTS notes(symbol TEXT PRIMARY KEY, text TEXT);""")
    for r in _con.execute("SELECT k,v FROM settings"):
        cfg[r["k"]] = json.loads(r["v"])
    if "_seeded" not in cfg:
        seed_demo()
    return _con


def seed_demo(reset=False):
    """(Re)create demo portfolio + strategies. Entry prices are derived from DEMO series."""
    from . import demo_data as dd
    c = init()
    if reset:
        c.execute("DELETE FROM positions"); c.execute("DELETE FROM strategies")
    for sym, qty, back in SEED_POSITIONS:
        df = dd.series(sym)
        c.execute("INSERT OR REPLACE INTO positions VALUES(?,?,?)", (sym, qty, float(df.close.iloc[-back])))
    for n, t, p, sl, tp in SEED_STRATEGIES:
        c.execute("INSERT OR REPLACE INTO strategies VALUES(?,?,?,?,?,?)", (n, t, json.dumps(p), sl, tp, "Built-in starter (editable)"))
    c.commit()
    cfg_set("_seeded", True)


def cfg_set(k, v):
    cfg[k] = v
    init().execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (k, json.dumps(v)))
    _con.commit()


def reset_settings():
    for k, v in DEFAULTS.items():
        cfg_set(k, v)


def positions():
    return [dict(r) for r in init().execute("SELECT * FROM positions ORDER BY symbol")]


def upsert_position(sym, qty, entry, merge=False):
    c = init()
    old = c.execute("SELECT qty,entry FROM positions WHERE symbol=?", (sym,)).fetchone()
    if merge and old:
        tq = old["qty"] + qty
        entry = (old["qty"] * old["entry"] + qty * entry) / tq
        qty = tq
    c.execute("INSERT OR REPLACE INTO positions VALUES(?,?,?)", (sym, qty, entry))
    c.commit()


def remove_position(sym):
    init().execute("DELETE FROM positions WHERE symbol=?", (sym,)); _con.commit()


def strategies():
    out = []
    for r in init().execute("SELECT * FROM strategies ORDER BY rowid"):
        d = dict(r); d["params"] = json.loads(d["params"]); out.append(d)
    return out


def strategy(name):
    return next((s for s in strategies() if s["name"] == name), None)


def save_strategy(name, typ, params, sl, tp, notes=""):
    init().execute("INSERT OR REPLACE INTO strategies VALUES(?,?,?,?,?,?)", (name, typ, json.dumps(params), sl, tp, notes))
    _con.commit()


def delete_strategy(name):
    init().execute("DELETE FROM strategies WHERE name=?", (name,)); _con.commit()


def get_note(sym):
    r = init().execute("SELECT text FROM notes WHERE symbol=?", (sym,)).fetchone()
    return r["text"] if r else ""


def set_note(sym, text):
    init().execute("INSERT OR REPLACE INTO notes VALUES(?,?)", (sym, text)); _con.commit()
