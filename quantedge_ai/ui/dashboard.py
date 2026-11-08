import customtkinter as ctk
from core.helpers import *
from core import database as db, demo_data as dd, analytics as an, signals as sg, chart_engine as ch
from tkinter import messagebox


class Dashboard(Screen):
    title = "Overview"; subtitle = "Portfolio, markets and signals at a glance · all figures are DEMO"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.grid_columnconfigure(tuple(range(10)), weight=1, uniform="c"); self.grid_rowconfigure(1, weight=3); self.grid_rowconfigure(2, weight=2)
        self.tiles = [Stat(self, l) for l in ("Portfolio Value", "Daily P&L", "Total Return", "Win Rate", "Risk Score")]
        for i, t in enumerate(self.tiles): t.grid(row=0, column=i * 2, columnspan=2, sticky="nsew", padx=4, pady=4)
        eq = Card(self, "Portfolio equity", "DEMO"); eq.grid(row=1, column=0, columnspan=6, sticky="nsew", padx=4, pady=4)
        self.tf = Seg(eq.body, ("1M", "3M", "6M", "1Y", "All"), lambda v: self.draw_equity()); self.tf.set("6M"); self.tf.pack(anchor="e")
        self.eq = ChartPanel(eq.body); self.eq.pack(fill="both", expand=True)
        mo = Card(self, "Market overview", "DEMO"); mo.grid(row=1, column=6, columnspan=4, sticky="nsew", padx=4, pady=4)
        self.mt = Table(mo.body, ("Index", "Level", "Chg %"), (140, 100, 80), height=3, on_select=lambda v: self.app.goto("Live Markets", symbol=v[0])); self.mt.pack(fill="x")
        self.breadth = Label(mo.body, "", 11, C["mute"]); self.breadth.pack(anchor="w", pady=(10, 2))
        self.movers = Table(mo.body, ("Top movers", "Last", "Chg %"), (140, 100, 80), height=5, on_select=lambda v: self.app.goto("Live Markets", symbol=v[0])); self.movers.pack(fill="both", expand=True)
        wl = Card(self, "Watchlist", "DEMO"); wl.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=4, pady=4)
        self.wl = Table(wl.body, ("Symbol", "Last", "Chg %"), (90, 90, 70), height=6, on_select=lambda v: self.app.goto("Live Markets", symbol=v[0])); self.wl.pack(fill="both", expand=True)
        sg_ = Card(self, "Recent signals", "DEMO"); sg_.grid(row=2, column=3, columnspan=4, sticky="nsew", padx=4, pady=4)
        self.sg = Table(sg_.body, ("Date", "Symbol", "Signal", "Conf %"), (90, 90, 70, 70), height=6, on_select=lambda v: self.app.goto("AI Signals", symbol=v[1])); self.sg.pack(fill="both", expand=True)
        mi = Card(self, "Market intelligence", "DEMO"); mi.grid(row=2, column=7, columnspan=3, sticky="nsew", padx=4, pady=4)
        self.mi = ctk.CTkFrame(mi.body, fg_color="transparent"); self.mi.pack(fill="both", expand=True)

    def draw_equity(self):
        h = an.history(); f = self.eq.fig; f.clear(); ax = f.add_subplot(111)
        if len(h) == 0: ch.empty(ax, "Add positions in Portfolio"); self.eq.draw(); return
        tf = self.tf.get(); h = dd.window(h.to_frame("v"), tf).v if tf != "All" else h
        ch.line(ax, h, C["acc"]); ch.style(ax); ch.datefmt(ax); self.eq.draw()

    def on_show(self, **kw):
        t = an.pos_table(); val = t.value.sum(); cost = t.cost.sum(); day = t.day.sum(); tot = val - cost
        self.tiles[0].set(inr(val, 0), f"{len(t)} positions", None)
        self.tiles[1].set(inr(day, 0, True), pct(day / (val - day) * 100 if val else 0), colr(day), colr(day))
        self.tiles[2].set(pct(tot / cost * 100 if cost else 0), inr(tot, 0, True) + " unrealised", colr(tot), colr(tot))
        wr, sn = an.default_win_rate()
        self.tiles[3].set(f"{wr:.0f}%" if wr is not None else "–", f"Backtest · {sn}" if wr is not None else "no strategies", C["acc"])
        r = an.risk()
        if r: self.tiles[4].set(f"{r['score']:.0f}/100", r["label"] + " risk", {"Low": C["up"], "Moderate": C["amber"], "High": C["down"]}[r["label"]])
        idx = [a for a in dd.ASSETS if a["cls"] == "Index"]
        self.mt.set([(a["name"].replace(" Index", ""), f"{dd.quote(a['sym'])['last']:,.0f}", pct(dd.quote(a['sym'])['pct'])) for a in idx],
                    [sgn_tag(dd.quote(a["sym"])["pct"]) for a in idx], iids=[a["sym"] for a in idx])
        qs = [(a["sym"], dd.quote(a["sym"])) for a in dd.ASSETS if a["cls"] != "Index"]
        adv = sum(q["pct"] > 0 for _, q in qs); self.breadth.configure(text=f"Breadth: {adv} advancing · {len(qs) - adv} declining (DEMO)")
        mv = sorted(qs, key=lambda x: -abs(x[1]["pct"]))[:5]
        self.movers.set([(s, compact(q["last"]), pct(q["pct"])) for s, q in mv], [sgn_tag(q["pct"]) for _, q in mv], iids=[s for s, _ in mv])
        wl = [s for s in db.cfg["watchlist"] if s in dd.ASSET]
        self.wl.set([(s, compact(dd.quote(s)["last"]), pct(dd.quote(s)["pct"])) for s in wl], [sgn_tag(dd.quote(s)["pct"]) for s in wl], iids=wl)
        rec = sg.recent(8)
        self.sg.set([(d.strftime("%d %b"), s, sig, f"{c:.0f}") for d, s, sig, c in rec], ["pos" if x[2] == "BUY" else "neg" if x[2] == "SELL" else "amb" for x in rec])
        self.draw_equity(); self.intel(qs, t)

    def intel(self, qs, t):
        for w in self.mi.winfo_children(): w.destroy()
        snaps = sg.all_snapshots(); os_ = min(snaps, key=lambda s: s["rsi"]); ob = max(snaps, key=lambda s: s["rsi"])
        up = max(snaps, key=lambda s: s["mom"]); buys = [s for s in snaps if s["signal"] == "BUY"]
        lines = [(C["up"], f"Strongest 10d momentum: {up['sym']} ({up['mom']:+.1f}%)"), (C["amber"], f"Most overbought: {ob['sym']} RSI {ob['rsi']:.0f}"),
                 (C["blue"], f"Most oversold: {os_['sym']} RSI {os_['rsi']:.0f}"), (C["acc"], f"{len(buys)} of {len(snaps)} assets carry a BUY signal")]
        if len(t): top = t.sort_values("weight").iloc[-1]; lines.append((C["down"] if top.weight > 20 else C["mute"], f"Largest holding {top.symbol} = {top.weight:.1f}% of portfolio"))
        for c, s in lines: Label(self.mi, "▌ " + s, 11, c, wraplength=300, justify="left").pack(anchor="w", pady=3)
        Label(self.mi, "Auto-generated from synthetic DEMO data.\nNot market information or advice.", 9, C["mute"], justify="left").pack(anchor="w", pady=(8, 0))
