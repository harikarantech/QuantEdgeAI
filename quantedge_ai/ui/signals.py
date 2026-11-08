import customtkinter as ctk
from core.helpers import *
from core import demo_data as dd, signals as sg, chart_engine as ch


def bind_all(w, cb):
    w.bind("<Button-1>", lambda e: cb(), add="+")
    for c in w.winfo_children(): bind_all(c, cb)


class Signals(Screen):
    title = "AI Signals"; subtitle = "BUY / SELL / HOLD from EMA, RSI, MACD and momentum · DEMO signals on synthetic data, not advice"

    def __init__(self, master, app):
        super().__init__(master, app); self.sym = None; self.cards = {}
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        l = ctk.CTkFrame(self, fg_color="transparent", width=440); l.grid(row=0, column=0, sticky="nsew", padx=(0, 6)); l.pack_propagate(False)
        top = ctk.CTkFrame(l, fg_color="transparent"); top.pack(fill="x")
        self.flt = Seg(top, ("ALL", "BUY", "SELL", "HOLD"), lambda v: self.build_cards()); self.flt.set("ALL"); self.flt.pack(side="left")
        self.count = Label(top, "", 11, C["mute"]); self.count.pack(side="right")
        self.sc = ctk.CTkScrollableFrame(l, fg_color="transparent"); self.sc.pack(fill="both", expand=True, pady=(6, 0))
        self.sc.grid_columnconfigure((0, 1), weight=1, uniform="k")
        r = ctk.CTkFrame(self, fg_color="transparent"); r.grid(row=0, column=1, sticky="nsew"); r.grid_columnconfigure(0, weight=1); r.grid_rowconfigure(2, weight=3); r.grid_rowconfigure(3, weight=1)
        self.title_l = Label(r, "", 16, bold=True); self.title_l.grid(row=0, column=0, sticky="w", pady=(0, 4))
        tr = ctk.CTkFrame(r, fg_color="transparent"); tr.grid(row=1, column=0, sticky="ew"); tr.grid_columnconfigure(tuple(range(6)), weight=1, uniform="t")
        self.t = [Stat(tr, l_, 16) for l_ in ("Signal", "RSI (14)", "MACD hist", "EMA 20 / 50", "Momentum 10d", "Trend")]
        for i, t in enumerate(self.t): t.grid(row=0, column=i, sticky="ew", padx=3)
        cc = Card(r, "Price · RSI · MACD", "DEMO"); cc.grid(row=2, column=0, sticky="nsew", pady=6); self.cp = ChartPanel(cc.body); self.cp.pack(fill="both", expand=True)
        hc = Card(r, "Signal history", "DEMO"); hc.grid(row=3, column=0, sticky="nsew")
        self.hist = Table(hc.body, ("Date", "Signal", "Price", "Confidence", "Score"), (90, 70, 90, 90, 70), height=4); self.hist.pack(fill="both", expand=True)

    def on_show(self, symbol=None, **kw):
        self.snaps = {s["sym"]: s for s in sg.all_snapshots()}
        self.build_cards(); self.select(symbol if symbol in self.snaps else (self.sym or "RELIANCE"))

    def build_cards(self):
        for w in self.sc.winfo_children(): w.destroy()
        f = self.flt.get(); lst = [s for s in self.snaps.values() if f == "ALL" or s["signal"] == f]
        lst.sort(key=lambda s: -s["conf"]); self.cards = {}
        n = {k: sum(s["signal"] == k for s in self.snaps.values()) for k in ("BUY", "SELL", "HOLD")}
        self.count.configure(text=f"BUY {n['BUY']} · SELL {n['SELL']} · HOLD {n['HOLD']}")
        for i, s in enumerate(lst):
            col = {"BUY": C["up"], "SELL": C["down"], "HOLD": C["amber"]}[s["signal"]]
            c = ctk.CTkFrame(self.sc, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["line"]); c.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
            top = ctk.CTkFrame(c, fg_color="transparent"); top.pack(fill="x", padx=10, pady=(8, 0))
            Label(top, s["sym"], 14, bold=True).pack(side="left")
            Label(top, s["signal"], 11, "#04120e", True, fg_color=col, corner_radius=6, width=52).pack(side="right")
            Label(c, dd.ASSET[s["sym"]]["name"], 10, C["mute"]).pack(anchor="w", padx=10)
            b = ctk.CTkProgressBar(c, height=6, progress_color=col, fg_color=C["line"]); b.set(s["conf"] / 100); b.pack(fill="x", padx=10, pady=(6, 2))
            Label(c, f"Conf {s['conf']:.0f}% · RSI {s['rsi']:.0f} · {s['trend']}", 10, C["mute"]).pack(anchor="w", padx=10, pady=(0, 8))
            bind_all(c, lambda sym=s["sym"]: self.select(sym)); self.cards[s["sym"]] = c

    def select(self, sym):
        self.sym = sym; s = self.snaps[sym]
        for k, c in self.cards.items(): c.configure(border_color=C["acc"] if k == sym else C["line"])
        col = {"BUY": C["up"], "SELL": C["down"], "HOLD": C["amber"]}[s["signal"]]
        self.title_l.configure(text=f"{sym} · {dd.ASSET[sym]['name']}   —   DEMO signal")
        vals = [(s["signal"], f"{s['conf']:.0f}% confidence", col), (f"{s['rsi']:.1f}", "Overbought" if s["rsi"] > 70 else "Oversold" if s["rsi"] < 30 else "Neutral", None),
                (f"{s['hist']:+.2f}", "Bullish" if s["hist"] > 0 else "Bearish", colr(s["hist"])), (f"{compact(s['ema20'])}", f"EMA50 {compact(s['ema50'])}", None),
                (pct(s["mom"]), "momentum", colr(s["mom"])), (s["trend"], "EMA 20 vs 50", colr(1 if s["trend"] == "Uptrend" else -1 if s["trend"] == "Downtrend" else 0) if s["trend"] != "Sideways" else C["amber"])]
        for t, (v, sub, c) in zip(self.t, vals): t.set(v, sub, c)
        df = dd.series(sym); ch.indicator_panel(self.cp.fig, df.iloc[-300:]); self.cp.draw()
        h = sg.changes(sym, 10)
        self.hist.set([(d.strftime("%d %b %Y"), r.signal, inr(r.close), f"{r.conf:.0f}%", f"{r.score:+.2f}") for d, r in h.iterrows()],
                      ["pos" if r.signal == "BUY" else "neg" if r.signal == "SELL" else "amb" for _, r in h.iterrows()])


import pandas as pd
