import customtkinter as ctk, numpy as np, pandas as pd
from tkinter import messagebox
from core.helpers import *
from core import database as db, demo_data as dd, signals as sg, indicators as ind, chart_engine as ch


class Research(Screen):
    title = "Market Research"; subtitle = "Asset overview, performance, technicals, trend analysis and notes · DEMO data"

    def __init__(self, master, app):
        super().__init__(master, app); self.sym = None
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        l = Card(self, "Search assets", "DEMO", width=300); l.grid(row=0, column=0, sticky="nsew", padx=(0, 6)); l.pack_propagate(False)
        self.list = AssetList(l.body, self.pick); self.list.pack(fill="both", expand=True)
        self.tabs = ctk.CTkTabview(self, fg_color=C["card"], segmented_button_selected_color=C["acc"], segmented_button_selected_hover_color=mix(C["acc"]),
                                   segmented_button_unselected_color=C["panel"], segmented_button_fg_color=C["panel"], text_color=C["text"], border_width=1, border_color=C["line"])
        self.tabs.grid(row=0, column=1, sticky="nsew")
        for n in ("Overview", "Performance", "Technicals", "Trend", "Workspace"): self.tabs.add(n)
        o = self.tabs.tab("Overview"); o.grid_columnconfigure(tuple(range(6)), weight=1, uniform="c"); o.grid_rowconfigure(2, weight=1)
        self.head = Label(o, "", 18, bold=True); self.head.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 6))
        self.ot = [Stat(o, l, 15) for l in ("Last", "1Y return", "Volatility", "52W range", "Avg volume", "Beta vs NIFTY")]
        for i, t in enumerate(self.ot): t.grid(row=1, column=i, sticky="ew", padx=3)
        self.ocp = ChartPanel(o); self.ocp.grid(row=2, column=0, columnspan=6, sticky="nsew", pady=6)
        self.odesc = Label(o, "", 11, C["mute"], wraplength=900, justify="left"); self.odesc.grid(row=3, column=0, columnspan=6, sticky="w")
        p = self.tabs.tab("Performance"); p.grid_columnconfigure(0, weight=3); p.grid_columnconfigure(1, weight=2); p.grid_rowconfigure(0, weight=1)
        self.pcp = ChartPanel(p); self.pcp.grid(row=0, column=0, sticky="nsew"); self.ptab = Table(p, ("Period", "Asset", "NIFTY 50", "Excess"), (70, 80, 80, 80), height=8); self.ptab.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        t = self.tabs.tab("Technicals"); t.grid_columnconfigure(0, weight=3); t.grid_columnconfigure(1, weight=1); t.grid_rowconfigure(0, weight=1)
        self.tcp = ChartPanel(t); self.tcp.grid(row=0, column=0, sticky="nsew"); self.ttab = Table(t, ("Indicator", "Value", "Reading"), (110, 80, 80), height=8); self.ttab.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        r = self.tabs.tab("Trend"); r.grid_columnconfigure(0, weight=3); r.grid_columnconfigure(1, weight=1); r.grid_rowconfigure(0, weight=1)
        self.rcp = ChartPanel(r); self.rcp.grid(row=0, column=0, sticky="nsew"); self.rtxt = Label(r, "", 12, justify="left", wraplength=300); self.rtxt.grid(row=0, column=1, sticky="nw", padx=12)
        w = self.tabs.tab("Workspace"); w.grid_columnconfigure(0, weight=1); w.grid_rowconfigure(1, weight=1)
        self.wl = Label(w, "", 13, bold=True); self.wl.grid(row=0, column=0, sticky="w")
        self.note = ctk.CTkTextbox(w, fg_color=C["panel"], border_color=C["line"], border_width=1, text_color=C["text"], font=F(12)); self.note.grid(row=1, column=0, sticky="nsew", pady=6)
        b = ctk.CTkFrame(w, fg_color="transparent"); b.grid(row=2, column=0, sticky="w")
        Btn(b, "Save note", self.save_note, width=100).pack(side="left"); Btn(b, "★ Watchlist", self.watch, "ghost", 100).pack(side="left", padx=6)
        Btn(b, "+ Portfolio", lambda: self.app.goto("Portfolio", symbol=self.sym), "ghost", 100).pack(side="left"); Btn(b, "Backtest ›", lambda: self.app.goto("Backtesting", symbol=self.sym), "ghost", 100).pack(side="left", padx=6)
        self.wmsg = Label(b, "", 11, C["acc"]); self.wmsg.pack(side="left", padx=8)

    def on_show(self, symbol=None, **kw): self.list.refresh(); self.pick(symbol or self.sym or "TCS"); self.list.select(self.sym)

    def pick(self, sym):
        if sym == self.sym and self.ocp.fig.axes: return
        if self.sym: db.set_note(self.sym, self.note.get("1.0", "end").strip())
        self.sym = sym; a = dd.ASSET[sym]; df = dd.series(sym); c = df.close; q = dd.quote(sym); r = c.pct_change().dropna()
        nf = dd.series("NIFTY50").close; self.head.configure(text=f"{sym} · {a['name']}   [{a['cls']} · {a['sector']} · {dd.source(sym)}]")
        y = c[c.index >= c.index[-1] - pd.Timedelta(days=365)]; j = pd.concat([c.pct_change(), nf.pct_change()], axis=1).dropna().iloc[-250:]; beta = j.cov().iloc[0, 1] / j.iloc[:, 1].var()
        for t, (v, s, col) in zip(self.ot, ((inr(q["last"]), pct(q["pct"]), colr(q["pct"])), (pct((y.iloc[-1] / y.iloc[0] - 1) * 100), "", colr(y.iloc[-1] - y.iloc[0])), (f"{r.std() * np.sqrt(252) * 100:.1f}%", "annualised", None),
                                      (f"{compact(y.min())}–{compact(y.max())}", "", None), (compact(df.volume.iloc[-60:].mean()), "60d avg", None), (f"{beta:.2f}", "vs DEMO index", None))): t.set(v, s, col, col)
        f = self.ocp.fig; f.clear(); ax = f.add_subplot(111); ch.line(ax, dd.window(c.to_frame("c"), "1Y").c, C["acc"]); ch.style(ax); ch.datefmt(ax); self.ocp.draw()
        self.odesc.configure(text=f"{a['name']} is a DEMO {a['cls'].lower()} in the {a['sector']} segment. All prices here are synthetic samples generated for demonstration; they are not real market information.")
        pr, rows = [], []
        for lab, d in (("1W", 7), ("1M", 30), ("3M", 91), ("6M", 182), ("1Y", 365)):
            ar = c.iloc[-1] / c[c.index <= c.index[-1] - pd.Timedelta(days=d)].iloc[-1] * 100 - 100; nr = nf.iloc[-1] / nf[nf.index <= nf.index[-1] - pd.Timedelta(days=d)].iloc[-1] * 100 - 100; pr.append((lab, ar, nr)); rows.append((lab, pct(ar), pct(nr), pct(ar - nr)))
        f = self.pcp.fig; f.clear(); ax = f.add_subplot(111); ch.grouped(ax, [p[0] for p in pr], [(sym, [p[1] for p in pr], C["acc"]), ("NIFTY 50", [p[2] for p in pr], C["blue"])]); self.pcp.draw()
        self.ptab.set(rows, [sgn_tag(float(x[3][:-1])) for x in rows])
        ch.indicator_panel(self.tcp.fig, df.iloc[-300:], bands=True); self.tcp.draw(); s = sg.snapshot(sym); bb = c.iloc[-1]
        rd = [("RSI (14)", f"{s['rsi']:.1f}", "Overbought" if s["rsi"] > 70 else "Oversold" if s["rsi"] < 30 else "Neutral"), ("MACD hist", f"{s['hist']:+.2f}", "Bullish" if s["hist"] > 0 else "Bearish"),
              ("EMA 20/50", "20>50" if s["ema20"] > s["ema50"] else "20<50", "Bullish" if s["ema20"] > s["ema50"] else "Bearish"), ("Momentum 10d", pct(s["mom"], 1), "Bullish" if s["mom"] > 0 else "Bearish"),
              ("Price vs EMA50", pct((bb / s["ema50"] - 1) * 100, 1), "Above" if bb > s["ema50"] else "Below"), ("DEMO signal", s["signal"], f"{s['conf']:.0f}% conf")]
        self.ttab.set(rd, ["pos" if x[2] in ("Bullish", "Above", "Oversold") else "neg" if x[2] in ("Bearish", "Below", "Overbought") else "" for x in rd])
        seg = c.iloc[-120:]; f = self.rcp.fig; f.clear(); k, r2 = ch.regression(f.add_subplot(111), seg); self.rcp.draw()
        mo = k / seg.mean() * 21 * 100
        self.rtxt.configure(text=f"Trend (120 bars)\n\nDirection: {'Up' if k > 0 else 'Down'}\nSlope: {mo:+.1f}% per month\nTrend strength (R²): {r2:.2f}\nSupport (120d low): {inr(seg.min())}\nResistance (120d high): {inr(seg.max())}\nPosition in range: {(bb - seg.min()) / (seg.max() - seg.min()) * 100:.0f}%\n\nRegression channel = ±2σ of residuals.\nDEMO analysis, not advice.")
        self.wl.configure(text=f"Research workspace · {sym}"); self.note.delete("1.0", "end"); self.note.insert("1.0", db.get_note(sym)); self.wmsg.configure(text="")

    def save_note(self): db.set_note(self.sym, self.note.get("1.0", "end").strip()); self.wmsg.configure(text="Note saved.")

    def watch(self):
        w = list(db.cfg["watchlist"])
        if self.sym not in w: w.append(self.sym); db.cfg_set("watchlist", w)
        self.wmsg.configure(text=f"{self.sym} is on your watchlist.")
