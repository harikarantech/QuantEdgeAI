"""Matplotlib drawing helpers styled for the QuantEdge dark terminal."""
import numpy as np, pandas as pd
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from .helpers import C, compact
from . import database as db, indicators as ind

PAL = lambda: [C["acc"], "#3b82f6", "#8b5cf6", "#f5b942", "#f0506e", "#22d3ee", "#a3e635", "#fb923c", "#94a3b8", "#e879f9"]


def style(ax, grid=None):
    ax.set_facecolor(C["card"])
    for k, s in ax.spines.items(): s.set_color(C["line"])
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors=C["mute"], labelsize=8, length=2)
    ax.grid(bool(db.cfg["grid"] if grid is None else grid), color=C["line"], lw=.5, alpha=.7)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: compact(v)))
    ax.set_axisbelow(True)


def datefmt(ax):
    loc = mdates.AutoDateLocator(minticks=4, maxticks=8)
    ax.xaxis.set_major_locator(loc); ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))


def empty(ax, msg="No data"):
    ax.set_facecolor(C["card"]); ax.axis("off"); ax.text(.5, .5, msg, color=C["mute"], ha="center", va="center", transform=ax.transAxes)


def line(ax, s, color=None, fill=True, lw=1.6, label=None):
    color = color or C["acc"]
    ax.plot(s.index, s.values, color=color, lw=lw, label=label)
    if fill: ax.fill_between(s.index, s.values, s.values.min(), color=color, alpha=.10)


def candles(ax, df):
    x = mdates.date2num(df.index.to_pydatetime()); up = (df.close >= df.open).values
    col = np.where(up, C["up"], C["down"]).tolist(); w = max(0.2, 0.7 * np.median(np.diff(x))) if len(x) > 1 else .6
    ax.vlines(x, df.low, df.high, colors=col, lw=.8)
    ax.bar(x, (df.close - df.open).abs().clip(lower=1e-9), bottom=np.minimum(df.open, df.close), width=w, color=col)
    ax.xaxis_date()


def price_volume(fig, df, kind="Line"):
    fig.clear()
    if db.cfg["show_volume"]:
        gs = fig.add_gridspec(4, 1); ax = fig.add_subplot(gs[:3]); av = fig.add_subplot(gs[3], sharex=ax)
    else:
        ax = fig.add_subplot(111); av = None
    if kind == "Candles": candles(ax, df)
    else: line(ax, df.close, C["up"] if df.close.iloc[-1] >= df.close.iloc[0] else C["down"])
    style(ax)
    if av is not None:
        up = (df.close >= df.open).values
        av.bar(df.index, df.volume, color=np.where(up, C["up"], C["down"]).tolist(), alpha=.6, width=.7)
        style(av); av.set_ylabel("Vol", color=C["mute"], fontsize=8); ax.tick_params(labelbottom=False); datefmt(av)
    else: datefmt(ax)


def indicator_panel(fig, df, bands=False):
    fig.clear(); gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1])
    a = fig.add_subplot(gs[0]); b = fig.add_subplot(gs[1], sharex=a); c = fig.add_subplot(gs[2], sharex=a)
    full = df; cl = full.close
    e20, e50 = ind.ema(cl, 20), ind.ema(cl, 50); r = ind.rsi(cl); m, s, h = ind.macd(cl)
    a.plot(cl.index, cl, color=C["text"], lw=1.2, label="Close"); a.plot(e20.index, e20, color=C["acc"], lw=1, label="EMA 20")
    a.plot(e50.index, e50, color=C["amber"], lw=1, label="EMA 50")
    if bands:
        mm, sd = cl.rolling(20).mean(), cl.rolling(20).std(); a.fill_between(cl.index, mm - 2 * sd, mm + 2 * sd, color=C["blue"], alpha=.12, label="Bollinger")
    a.legend(loc="upper left", fontsize=7, frameon=False, labelcolor=C["mute"], ncol=4)
    b.plot(r.index, r, color="#8b5cf6", lw=1.1); b.axhline(70, color=C["down"], ls="--", lw=.7); b.axhline(30, color=C["up"], ls="--", lw=.7)
    b.set_ylim(0, 100); b.set_ylabel("RSI", color=C["mute"], fontsize=8)
    c.bar(h.index, h, color=np.where(h >= 0, C["up"], C["down"]).tolist(), alpha=.7, width=.8)
    c.plot(m.index, m, color=C["text"], lw=.9); c.plot(s.index, s, color=C["amber"], lw=.9); c.set_ylabel("MACD", color=C["mute"], fontsize=8)
    for ax in (a, b, c): style(ax)
    b.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    a.tick_params(labelbottom=False); b.tick_params(labelbottom=False); datefmt(c)
    return a


def curves(ax, items, ylabel=""):
    for i, (lab, s, col) in enumerate(items):
        ax.plot(s.index, s.values, color=col or PAL()[i % 10], lw=1.6 if i == 0 else 1.2, label=lab)
    style(ax); datefmt(ax); ax.legend(loc="upper left", fontsize=8, frameon=False, labelcolor=C["mute"])
    if ylabel: ax.set_ylabel(ylabel, color=C["mute"], fontsize=8)


def drawdown(ax, dd):
    ax.fill_between(dd.index, dd.values * 100, 0, color=C["down"], alpha=.35); ax.plot(dd.index, dd.values * 100, color=C["down"], lw=.9)
    style(ax); datefmt(ax); ax.set_ylabel("Drawdown %", color=C["mute"], fontsize=8)


def histogram(ax, r, var_pct=None):
    ax.hist(r * 100, bins=40, color=C["acc"], alpha=.75, edgecolor=C["card"])
    if var_pct: ax.axvline(-var_pct, color=C["down"], ls="--", lw=1.2, label=f"VaR 95% (-{var_pct:.2f}%)"); ax.legend(fontsize=8, frameon=False, labelcolor=C["mute"])
    style(ax); ax.set_xlabel("Daily return %", color=C["mute"], fontsize=8)


def donut(ax, labels, vals, center=""):
    ax.pie(vals, colors=[PAL()[i % 10] for i in range(len(vals))], startangle=90, counterclock=False,
           wedgeprops=dict(width=.38, edgecolor=C["card"], linewidth=2))
    ax.set_aspect("equal"); ax.legend(labels, loc="center left", bbox_to_anchor=(1.0, .5), fontsize=8, frameon=False, labelcolor=C["mute"])
    if center: ax.text(0, 0, center, ha="center", va="center", color=C["text"], fontsize=10, fontweight="bold")


def hbar(ax, labels, vals, fmt="{:+.1f}%", signed=True):
    cols = [(C["up"] if v >= 0 else C["down"]) if signed else C["acc"] for v in vals]
    ax.barh(labels, vals, color=cols, height=.6); style(ax); ax.invert_yaxis(); ax.axvline(0, color=C["line"], lw=1)
    for i, v in enumerate(vals): ax.text(v, i, " " + fmt.format(v), va="center", ha="left" if v >= 0 else "right", color=C["mute"], fontsize=8)
    ax.margins(x=.18)


def grouped(ax, cats, series):
    w = .8 / len(series); x = np.arange(len(cats))
    for i, (lab, vals, col) in enumerate(series): ax.bar(x + i * w - .4 + w / 2, vals, w, label=lab, color=col)
    ax.set_xticks(x); ax.set_xticklabels(cats); style(ax); ax.axhline(0, color=C["line"], lw=1)
    ax.legend(fontsize=8, frameon=False, labelcolor=C["mute"])


def regression(ax, s):
    x = np.arange(len(s)); k, b = np.polyfit(x, s.values, 1); fit = k * x + b; sd = np.std(s.values - fit)
    ax.plot(s.index, s.values, color=C["text"], lw=1.2); ax.plot(s.index, fit, color=C["acc"], lw=1.4)
    ax.fill_between(s.index, fit - 2 * sd, fit + 2 * sd, color=C["acc"], alpha=.10)
    ax.axhline(s.max(), color=C["down"], ls=":", lw=.8); ax.axhline(s.min(), color=C["up"], ls=":", lw=.8)
    style(ax); datefmt(ax)
    r2 = 1 - np.sum((s.values - fit) ** 2) / np.sum((s.values - s.values.mean()) ** 2)
    return k, r2
