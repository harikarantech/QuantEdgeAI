import os, sys, subprocess, datetime as dt
import customtkinter as ctk, pandas as pd
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages
from core.helpers import *
from core import database as db, demo_data as dd, analytics as an, backtest as bt, chart_engine as ch

OUT = os.path.join(db.ROOT, "exports")
KINDS = ["Performance Report", "Portfolio Report", "Strategy Report", "Risk Report"]


def build(kind, sym, strat):
    """Return (title, text lines, [chart fn(ax, title)])"""
    L, charts, now = [], [], dt.datetime.now().strftime("%d %b %Y %H:%M")
    L += [f"QUANTEDGE AI — {kind.upper()}", f"Generated {now}", "*** DEMO DATA: synthetic prices and signals, not real market information ***", ""]
    t = an.pos_table(); val, cost = t.value.sum(), t.cost.sum()
    if kind == "Performance Report":
        h = an.history(); L += ["PORTFOLIO PERFORMANCE", f"  Market value : {inr(val, 0)}", f"  Invested     : {inr(cost, 0)}", f"  Unrealised   : {inr(val - cost, 0, True)} ({pct((val / cost - 1) * 100 if cost else 0)})", ""]
        L += ["  Period    Return      P&L"] + [f"  {l:<8} {pct(r):>8}  {inr(p, 0, True):>14}" for l, r, p in an.period_table()]
        charts.append(lambda ax: ch.line(ax, h.iloc[-365:], C["acc"]) or ch.style(ax) or ch.datefmt(ax))
    elif kind == "Portfolio Report":
        L += ["HOLDINGS", f"  {'Symbol':<11}{'Qty':>9}{'Entry':>12}{'Last':>12}{'Value':>14}{'P&L %':>9}{'Wt':>7}"]
        L += [f"  {r.symbol:<11}{r.qty:>9g}{r.entry:>12,.2f}{r.last:>12,.2f}{r.value:>14,.0f}{r.pnl_pct:>8.1f}%{r.weight:>6.1f}%" for r in t.itertuples()]
        L += ["", f"  TOTAL value {inr(val, 0)}   P&L {inr(val - cost, 0, True)}"]
        charts += [lambda ax: ch.donut(ax, list(t.symbol), list(t.value)), lambda ax: ch.hbar(ax, list(t.symbol), list(t.pnl_pct))]
    elif kind == "Strategy Report":
        s = db.strategy(strat)
        if not s: return kind, L + ["No strategy selected."], []
        r = bt.run(dd.series(sym), s["type"], s["params"], s["sl"], s["tp"], db.cfg["capital"], fee=db.cfg["fee_bps"] / 1e4); x = r["stats"]
        L += [f"STRATEGY: {s['name']} on {sym} (DEMO)", "  " + bt.describe(s["type"], s["params"], s["sl"], s["tp"]), "", f"  Total return : {pct(x['ret'] * 100)}   CAGR {pct(x['cagr'] * 100)}", f"  Max drawdown : {pct(x['maxdd'] * 100)}   Sharpe {x['sharpe']:.2f}",
              f"  Win rate     : {x['win'] * 100:.0f}% over {x['trades']} trades   Buy&hold {pct(x['bh'] * 100)}", "", "  RECENT TRADES"]
        L += [f"  {tr.entry:%d %b %y} → {tr.exit:%d %b %y}  {tr.ret * 100:+6.1f}%  {inr(tr.pnl, 0, True)}" for tr in r["trades"].tail(12).itertuples()]
        charts += [lambda ax: ch.curves(ax, [(s["name"], r["equity"], C["acc"]), ("Buy & hold", r["bh"], C["mute"])]), lambda ax: ch.drawdown(ax, r["dd"])]
    else:
        r = an.risk()
        if not r: return kind, L + ["Not enough data."], []
        L += ["RISK SUMMARY", f"  Risk score  : {r['score']:.0f}/100 ({r['label']})", f"  Volatility  : {r['vol'] * 100:.1f}% annualised", f"  Max drawdown: {pct(r['maxdd'] * 100)}", f"  Sharpe      : {r['sharpe']:.2f} (rf = 0)",
              f"  VaR 95% 1d  : {inr(r['var'], 0)}   CVaR {inr(r['cvar'], 0)}", "", "ALERTS"] + [f"  [{a}] {m}" for a, m in r["alerts"]]
        charts += [lambda ax: ch.drawdown(ax, r["dd"]), lambda ax: ch.histogram(ax, r["rets"], r["var"] / r["value"] * 100)]
    return kind, L, charts


class Reports(Screen):
    title = "Reports"; subtitle = "Generate performance, portfolio, strategy and risk reports · export PDF / CSV"

    def __init__(self, master, app):
        super().__init__(master, app); self.last = None
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        c = Card(self, "Report setup", width=330); c.grid(row=0, column=0, sticky="nsew", padx=(0, 6)); c.pack_propagate(False); k = c.body
        Label(k, "Report type", 11, C["mute"], True).pack(anchor="w"); self.kind = Drop(k, KINDS, lambda v: self.preview(), 290); self.kind.pack(pady=(0, 8))
        Label(k, "Strategy (strategy report)", 11, C["mute"], True).pack(anchor="w"); self.strat = Drop(k, ["-"], lambda v: self.preview(), 290); self.strat.pack(pady=(0, 8))
        Label(k, "Asset (strategy report)", 11, C["mute"], True).pack(anchor="w"); self.asset = Drop(k, [a["sym"] for a in dd.ASSETS], lambda v: self.preview(), 290); self.asset.set("RELIANCE"); self.asset.pack(pady=(0, 14))
        Btn(k, "Generate preview", self.preview, width=290).pack(pady=3); Btn(k, "Export PDF", self.pdf, "ghost", 290).pack(pady=3); Btn(k, "Export CSV (data tables)", self.csv, "ghost", 290).pack(pady=3)
        Btn(k, "Open exports folder", self.open, "ghost", 290).pack(pady=3); self.msg = Label(k, "", 11, C["acc"], wraplength=290, justify="left"); self.msg.pack(anchor="w", pady=8)
        p = Card(self, "Preview", "DEMO"); p.grid(row=0, column=1, sticky="nsew")
        self.box = ctk.CTkTextbox(p.body, fg_color=C["panel"], text_color=C["text"], font=ctk.CTkFont(family=MONO, size=12), border_width=1, border_color=C["line"]); self.box.pack(fill="both", expand=True)

    def on_show(self, **kw):
        n = [s["name"] for s in db.strategies()] or ["-"]; self.strat.configure(values=n)
        if self.strat.get() not in n: self.strat.set(n[0])
        self.preview()

    def preview(self, *a):
        self.last = build(self.kind.get(), self.asset.get(), self.strat.get()); self.box.configure(state="normal"); self.box.delete("1.0", "end"); self.box.insert("1.0", "\n".join(self.last[1])); self.box.configure(state="disabled")

    def pdf(self):
        self.preview(); kind, lines, charts = self.last; os.makedirs(OUT, exist_ok=True); path = os.path.join(OUT, f"QuantEdge_{kind.replace(' ', '_')}_{dt.datetime.now():%Y%m%d_%H%M%S}.pdf")
        try:
            with PdfPages(path) as pp:
                f = Figure(figsize=(8.27, 11.69), facecolor=C["bg"]); f.text(.07, .96, "\n".join(lines[:70]), va="top", family="monospace", fontsize=8, color=C["text"]); pp.savefig(f, facecolor=C["bg"])
                for i in range(0, len(charts), 2):
                    f = Figure(figsize=(8.27, 11.69), facecolor=C["bg"], layout="constrained")
                    for j, fn in enumerate(charts[i:i + 2]): ax = f.add_subplot(2, 1, j + 1); ax.set_facecolor(C["card"]); fn(ax)
                    pp.savefig(f, facecolor=C["bg"])
        except Exception as e: return messagebox.showerror("PDF failed", str(e))
        self.msg.configure(text=f"PDF saved:\n{path}")

    def csv(self):
        os.makedirs(OUT, exist_ok=True); k = self.kind.get(); path = os.path.join(OUT, f"QuantEdge_{k.replace(' ', '_')}_{dt.datetime.now():%Y%m%d_%H%M%S}.csv")
        if k in ("Portfolio Report", "Performance Report"): df = an.pos_table()
        elif k == "Risk Report": r = an.risk(); df = pd.DataFrame(r["contrib"], columns=["asset", "weight_pct", "ann_vol_pct", "risk_share_pct"]) if r else pd.DataFrame()
        else:
            s = db.strategy(self.strat.get()); df = bt.run(dd.series(self.asset.get()), s["type"], s["params"], s["sl"], s["tp"], db.cfg["capital"])["trades"] if s else pd.DataFrame()
        df.to_csv(path, index=False); self.msg.configure(text=f"CSV saved:\n{path}")

    def open(self):
        os.makedirs(OUT, exist_ok=True)
        try: os.startfile(OUT) if sys.platform.startswith("win") else subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", OUT])
        except Exception: self.msg.configure(text=f"Folder: {OUT}")
