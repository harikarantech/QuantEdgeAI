import numpy as np, pandas as pd
from . import indicators as ind

TYPES = {
    "EMA Crossover": {"fast": 20, "slow": 50},
    "RSI Mean Reversion": {"period": 14, "buy_below": 30, "sell_above": 55},
    "MACD Momentum": {"fast": 12, "slow": 26, "signal": 9},
    "Donchian Breakout": {"lookback": 20, "exit_lookback": 10},
    "AI Composite Score": {"buy_score": 1.5, "exit_score": 0.0},
}
RULES = {
    "EMA Crossover": "ENTER when EMA({fast}) is above EMA({slow}); EXIT when it drops below.",
    "RSI Mean Reversion": "ENTER when RSI({period}) < {buy_below}; EXIT when RSI > {sell_above}.",
    "MACD Momentum": "ENTER when MACD({fast},{slow},{signal}) histogram > 0; EXIT when it turns negative.",
    "Donchian Breakout": "ENTER on a close above the {lookback}-day high; EXIT below the {exit_lookback}-day low.",
    "AI Composite Score": "ENTER when the composite DEMO score >= {buy_score}; EXIT when it falls to <= {exit_score}.",
}


def describe(t, p, sl=0, tp=0):
    s = RULES[t].format(**p)
    if p.get("trend_filter"): s += " Filter: only enter above EMA(100)."
    if p.get("rsi_filter"): s += " Filter: skip entries when RSI > 75."
    if sl: s += f" Stop-loss {sl:g}%."
    if tp: s += f" Take-profit {tp:g}%."
    return s


def signals(df, t, p):
    c = df.close
    if t == "EMA Crossover":
        cond = ind.ema(c, int(p["fast"])) > ind.ema(c, int(p["slow"])); en, ex = cond, ~cond
    elif t == "RSI Mean Reversion":
        r = ind.rsi(c, int(p["period"])); en, ex = r < p["buy_below"], r > p["sell_above"]
    elif t == "MACD Momentum":
        _, _, h = ind.macd(c, int(p["fast"]), int(p["slow"]), int(p["signal"])); en, ex = h > 0, h <= 0
    elif t == "Donchian Breakout":
        en = c > c.rolling(int(p["lookback"])).max().shift(1); ex = c < c.rolling(int(p["exit_lookback"])).min().shift(1)
    else:
        sc = ind.score_series(df); en, ex = sc >= p["buy_score"], sc <= p["exit_score"]
    en, ex = en.fillna(False), ex.fillna(False)
    if p.get("trend_filter"): en = en & (c > ind.ema(c, 100))
    if p.get("rsi_filter"): en = en & (ind.rsi(c) < 75)
    return en.values, ex.values


def run(df, t, p, sl=0, tp=0, capital=1_000_000, start=None, end=None, fee=0.0005):
    en, ex = signals(df, t, p)
    d = df.assign(en=en, ex=ex)
    if start is not None: d = d[d.index >= pd.Timestamp(start)]
    if end is not None: d = d[d.index <= pd.Timestamp(end)]
    if len(d) < 30: raise ValueError("Date range too short: need at least 30 bars.")
    o, c, E, X, idx = d.open.values, d.close.values, d.en.values, d.ex.values, d.index
    n = len(d); cash, pos, ep, ev, ed, pend = float(capital), 0.0, 0.0, 0.0, None, 0
    eq = np.empty(n); trades = []

    def mk(xd, xp, val, is_open=False):
        return dict(entry=ed, exit=xd, ep=ep, xp=xp, pnl=val - ev, ret=val / ev - 1, days=(xd - ed).days, open=is_open)

    for i in range(n):
        if pend == 1 and pos == 0:
            pos = cash * (1 - fee) / o[i]; ep = o[i]; ev = cash; ed = idx[i]; cash = 0.0
        elif pend == -1 and pos > 0:
            cash = pos * o[i] * (1 - fee); trades.append(mk(idx[i], o[i], cash)); pos = 0.0
        pend = 0
        if pos > 0:
            r = c[i] / ep - 1
            if X[i] or (sl and r <= -sl / 100) or (tp and r >= tp / 100): pend = -1
        elif E[i]:
            pend = 1
        eq[i] = cash + pos * c[i]
    if pos > 0:
        cash = pos * c[-1] * (1 - fee); trades.append(mk(idx[-1], c[-1], cash, True)); eq[-1] = cash
    eqs = pd.Series(eq, index=idx)
    tr = pd.DataFrame(trades, columns=["entry", "exit", "ep", "xp", "pnl", "ret", "days", "open"])
    yrs = max((idx[-1] - idx[0]).days / 365.25, 1e-9)
    dr = eqs.pct_change().dropna()
    dd_ = eqs / eqs.cummax() - 1
    wins, loss = tr[tr.pnl > 0].pnl.sum(), -tr[tr.pnl <= 0].pnl.sum()
    stats = dict(ret=eq[-1] / capital - 1, cagr=(eq[-1] / capital) ** (1 / yrs) - 1,
                 maxdd=float(dd_.min()), sharpe=float(dr.mean() / dr.std() * np.sqrt(252)) if dr.std() > 0 else 0.0,
                 win=float((tr.pnl > 0).mean()) if len(tr) else 0.0, trades=len(tr),
                 pf=float(wins / loss) if loss > 0 else (float("inf") if wins > 0 else 0.0),
                 bh=float(c[-1] / d.close.values[0] - 1), final=float(eq[-1]))
    return dict(equity=eqs, bh=capital * d.close / d.close.iloc[0], dd=dd_, trades=tr, stats=stats, close=d.close)
