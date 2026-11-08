"""DEMO market data: deterministic synthetic OHLCV series. NOT real market information.
If a CSV folder is set in Settings, SYMBOL.csv (Date,Open,High,Low,Close,Volume) overrides the demo series."""
import os, zlib
import numpy as np, pandas as pd
from functools import lru_cache
from . import database as db

_A = [  # sym, name, class, sector, base price (INR), annual vol, annual drift, avg volume
    ("RELIANCE", "Reliance Industries", "Stock", "Energy", 2900, .24, .10, 6e6),
    ("TCS", "Tata Consultancy Services", "Stock", "IT", 3900, .22, .12, 2e6),
    ("HDFCBANK", "HDFC Bank", "Stock", "Banking", 1650, .20, .08, 9e6),
    ("INFY", "Infosys", "Stock", "IT", 1550, .25, .11, 7e6),
    ("ICICIBANK", "ICICI Bank", "Stock", "Banking", 1100, .22, .14, 8e6),
    ("SBIN", "State Bank of India", "Stock", "Banking", 780, .28, .15, 1.4e7),
    ("ITC", "ITC Ltd", "Stock", "FMCG", 430, .19, .09, 1.2e7),
    ("LT", "Larsen & Toubro", "Stock", "Infra", 3500, .24, .16, 2.5e6),
    ("BHARTIARTL", "Bharti Airtel", "Stock", "Telecom", 1250, .23, .17, 5e6),
    ("TATAMOTORS", "Tata Motors", "Stock", "Auto", 950, .33, .12, 1.5e7),
    ("BTC", "Bitcoin (INR)", "Crypto", "Crypto", 5400000, .65, .30, 2.4e4),
    ("ETH", "Ethereum (INR)", "Crypto", "Crypto", 280000, .75, .25, 3e5),
    ("SOL", "Solana (INR)", "Crypto", "Crypto", 14000, .95, .30, 4e6),
    ("BNB", "BNB (INR)", "Crypto", "Crypto", 48000, .70, .22, 1e6),
    ("XRP", "XRP (INR)", "Crypto", "Crypto", 190, .85, .15, 9e7),
    ("ADA", "Cardano (INR)", "Crypto", "Crypto", 70, .90, .12, 5e7),
    ("NIFTY50", "NIFTY 50 Index", "Index", "Index", 24500, .13, .11, 3e8),
    ("SENSEX", "BSE SENSEX Index", "Index", "Index", 80500, .13, .11, 1.5e5),
    ("BANKNIFTY", "NIFTY Bank Index", "Index", "Index", 52000, .16, .10, 1.2e5),
]
ASSETS = [dict(sym=a[0], name=a[1], cls=a[2], sector=a[3], base=a[4], vol=a[5], drift=a[6], volu=a[7]) for a in _A]
ASSET = {a["sym"]: a for a in ASSETS}
N = 900
TF_DAYS = {"1W": 7, "1M": 30, "3M": 91, "6M": 182, "1Y": 365, "3Y": 1095}


def _csv(sym):
    d = db.cfg.get("csv_dir") or ""
    p = os.path.join(d, f"{sym}.csv")
    if d and os.path.isfile(p):
        try:
            df = pd.read_csv(p)
            df.columns = [c.strip().lower() for c in df.columns]
            df["date"] = pd.to_datetime(df["date"]); df = df.set_index("date").sort_index()
            if "volume" not in df: df["volume"] = 0
            return df[["open", "high", "low", "close", "volume"]].dropna()
        except Exception:
            return None
    return None


@lru_cache(maxsize=None)
def series(sym):
    c = _csv(sym)
    if c is not None:
        return c
    a = ASSET[sym]
    rng = np.random.default_rng(zlib.crc32(sym.encode()))
    vol, mu = a["vol"] / np.sqrt(252), a["drift"] / 252
    t = np.arange(N)
    r = rng.normal(mu, vol, N) + 0.0006 * np.sin(t / rng.uniform(35, 80) + rng.uniform(0, 6)) \
        + 0.0003 * np.sin(t / rng.uniform(120, 220))
    close = np.exp(np.cumsum(r)); close = close / close[-1] * a["base"]
    op = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, vol / 4, N))
    hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, vol / 2.5, N)))
    lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, vol / 2.5, N)))
    v = rng.lognormal(0, .35, N) * a["volu"] * (1 + np.abs(r) / vol)
    end = pd.Timestamp.today().normalize()
    idx = pd.date_range(end=end, periods=N) if a["cls"] == "Crypto" else pd.bdate_range(end=end, periods=N)
    return pd.DataFrame({"open": op, "high": hi, "low": lo, "close": close, "volume": v}, index=idx)


def clear_cache():
    series.cache_clear()


def source(sym):
    return "CSV" if _csv(sym) is not None else "DEMO"


def quote(sym):
    d = series(sym); last, prev = float(d.close.iloc[-1]), float(d.close.iloc[-2])
    return dict(last=last, prev=prev, chg=last - prev, pct=(last / prev - 1) * 100)


def window(df, tf):
    if tf in TF_DAYS:
        return df[df.index >= df.index[-1] - pd.Timedelta(days=TF_DAYS[tf])]
    return df


def search(q="", cls="All", only=None):
    q = q.lower().strip()
    out = []
    for a in ASSETS:
        if cls != "All" and a["cls"] != cls: continue
        if only is not None and a["sym"] not in only: continue
        if q and q not in a["sym"].lower() and q not in a["name"].lower(): continue
        out.append(a)
    return out
