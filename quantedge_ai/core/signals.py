"""DEMO AI signals derived from indicator scores on synthetic data. Not trading advice."""
import numpy as np, pandas as pd
from . import indicators as ind, demo_data as dd


def frame(sym):
    df = dd.series(sym); sc = ind.score_series(df)
    sig = pd.Series(np.where(sc >= 1.5, "BUY", np.where(sc <= -1.5, "SELL", "HOLD")), index=df.index)
    conf = np.where(sig == "HOLD", 50 + (1.5 - sc.abs()).clip(lower=0) * 12, 52 + sc.abs() * 11).clip(50, 96)
    return pd.DataFrame({"close": df.close, "score": sc, "signal": sig, "conf": conf})


def snapshot(sym):
    df = dd.series(sym); c = df.close; f = frame(sym).iloc[-1]
    e20, e50 = ind.ema(c, 20).iloc[-1], ind.ema(c, 50).iloc[-1]; m, s, h = ind.macd(c)
    trend = "Uptrend" if c.iloc[-1] > e20 > e50 else "Downtrend" if c.iloc[-1] < e20 < e50 else "Sideways"
    return dict(sym=sym, signal=f.signal, conf=float(f.conf), score=float(f.score), rsi=float(ind.rsi(c).iloc[-1]),
                macd=float(m.iloc[-1]), macd_sig=float(s.iloc[-1]), hist=float(h.iloc[-1]), ema20=float(e20), ema50=float(e50),
                mom=float(c.pct_change(10).iloc[-1] * 100), trend=trend, price=float(c.iloc[-1]))


def changes(sym, n=12):
    f = frame(sym); chg = f[f.signal != f.signal.shift()].iloc[1:]
    return chg.iloc[::-1].head(n)


def all_snapshots(include_index=False):
    return [snapshot(a["sym"]) for a in dd.ASSETS if include_index or a["cls"] != "Index"]


def recent(n=8):
    rows = []
    for a in dd.ASSETS:
        if a["cls"] == "Index": continue
        c = changes(a["sym"], 1)
        if len(c): rows.append((c.index[0], a["sym"], c.signal.iloc[0], float(c.conf.iloc[0])))
    return sorted(rows, key=lambda r: r[0], reverse=True)[:n]
