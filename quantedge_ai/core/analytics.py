import numpy as np, pandas as pd
from . import database as db, demo_data as dd, backtest as bt, signals as sg


def pos_table():
    cols = ["symbol", "cls", "qty", "entry", "last", "value", "cost", "pnl", "pnl_pct", "day", "weight"]
    rows = []
    for p in db.positions():
        if p["symbol"] not in dd.ASSET: continue
        q = dd.quote(p["symbol"]); v = p["qty"] * q["last"]; c = p["qty"] * p["entry"]
        rows.append(dict(symbol=p["symbol"], cls=dd.ASSET[p["symbol"]]["cls"], qty=p["qty"], entry=p["entry"], last=q["last"],
                         value=v, cost=c, pnl=v - c, pnl_pct=(v / c - 1) * 100 if c else 0, day=p["qty"] * q["chg"], weight=0.0))
    df = pd.DataFrame(rows, columns=cols)
    if len(df): df["weight"] = df.value / df.value.sum() * 100
    return df


def asset_values():
    parts = {p["symbol"]: dd.series(p["symbol"]).close * p["qty"] for p in db.positions() if p["symbol"] in dd.ASSET}
    if not parts: return pd.DataFrame()
    return pd.concat(parts, axis=1).ffill().dropna()


def history():
    v = asset_values()
    return v.sum(axis=1) if len(v) else pd.Series(dtype=float)


def period_table():
    h = history(); out = []
    if len(h) < 10: return out
    for lab, d in (("1D", 1), ("1W", 7), ("1M", 30), ("3M", 91), ("6M", 182), ("1Y", 365)):
        base = h[h.index <= h.index[-1] - pd.Timedelta(days=d)]
        b = base.iloc[-1] if len(base) else h.iloc[0]
        out.append((lab, (h.iloc[-1] / b - 1) * 100, h.iloc[-1] - b))
    return out


def default_win_rate():
    s = db.strategies()
    if not s: return None, ""
    st, w, n = s[0], 0, 0
    for p in db.positions():
        if p["symbol"] not in dd.ASSET: continue
        try:
            r = bt.run(dd.series(p["symbol"]), st["type"], st["params"], st["sl"], st["tp"], 1e6)["trades"]
            w += int((r.pnl > 0).sum()); n += len(r)
        except Exception:
            pass
    return (w / n * 100 if n else None), st["name"]


def risk():
    h = history()
    if len(h) < 60: return None
    r = h.pct_change().dropna(); val = float(h.iloc[-1])
    vol = float(r.std() * np.sqrt(252)); dd_ = h / h.cummax() - 1
    sharpe = float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0.0
    q = np.percentile(r, 5); var = -q * val; cvar = -r[r <= q].mean() * val
    t = pos_table(); w = t.weight.values / 100; hhi = float((w ** 2).sum())
    score = float(np.clip(vol * 100 * 1.4 + abs(dd_.min()) * 100 * 0.9 + (hhi - 0.1) * 60, 0, 100))
    av = asset_values().pct_change().dropna(); contrib = []
    if len(av) > 30 and len(t):
        cov = av.cov().values * 252
        wv = t.set_index("symbol").loc[av.columns, "weight"].values / 100
        pv = float(wv @ cov @ wv)
        mc = (cov @ wv) * wv / pv if pv > 0 else wv
        for i, s in enumerate(av.columns):
            contrib.append((s, wv[i] * 100, float(np.sqrt(cov[i, i]) * 100), float(mc[i] * 100)))
    alerts = []
    for _, x in t.iterrows():
        if x.weight > 20: alerts.append(("HIGH", f"{x.symbol} is {x.weight:.1f}% of the portfolio (limit 20%)."))
    crypto = t[t.cls == "Crypto"].weight.sum()
    if crypto > 20: alerts.append(("MEDIUM", f"Crypto exposure is {crypto:.1f}% (guideline 20%)."))
    if vol > 0.22: alerts.append(("MEDIUM", f"Annualised volatility {vol * 100:.1f}% exceeds the 22% guideline."))
    if dd_.iloc[-1] < -0.08: alerts.append(("HIGH", f"Portfolio is {dd_.iloc[-1] * 100:.1f}% below its peak."))
    if var / val > 0.025: alerts.append(("MEDIUM", f"1-day 95% VaR is {var / val * 100:.2f}% of portfolio value."))
    for _, x in t.iterrows():
        s = sg.snapshot(x.symbol)
        if s["rsi"] > 70: alerts.append(("LOW", f"{x.symbol} RSI {s['rsi']:.0f}: overbought."))
        if s["signal"] == "SELL": alerts.append(("LOW", f"{x.symbol} carries a DEMO SELL signal ({s['conf']:.0f}% conf.)."))
    if not alerts: alerts.append(("LOW", "No active risk alerts."))
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}; alerts.sort(key=lambda a: order[a[0]])
    return dict(value=val, vol=vol, maxdd=float(dd_.min()), dd=dd_, sharpe=sharpe, var=var, cvar=float(cvar), rets=r, hhi=hhi,
                score=score, label="Low" if score < 35 else "Moderate" if score < 65 else "High", alerts=alerts, contrib=contrib, table=t)
