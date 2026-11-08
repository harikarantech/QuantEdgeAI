import numpy as np, pandas as pd


def sma(s, n): return s.rolling(n).mean()
def ema(s, n): return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    d = s.diff(); up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def macd(s, f=12, sl=26, sg=9):
    m = ema(s, f) - ema(s, sl); sig = ema(m, sg)
    return m, sig, m - sig


def score_series(df):
    """Composite DEMO score: EMA20/50 trend, MACD histogram, RSI extremes, 10-day momentum."""
    c = df.close; e20, e50 = ema(c, 20), ema(c, 50); r = rsi(c); _, _, h = macd(c); mom = c.pct_change(10)
    sc = np.sign(e20 - e50) + np.sign(h) + np.where(r < 35, 1.0, np.where(r > 70, -1.0, 0.0)) + np.tanh(mom * 8)
    return pd.Series(sc, index=c.index).fillna(0)
