import customtkinter as ctk
from tkinter import messagebox
from core.helpers import *
from core import database as db, demo_data as dd, backtest as bt, chart_engine as ch


class StrategyLab(Screen):
    title = "Strategy Lab"; subtitle = "Build, tune, save and compare rule-based strategies · tested on DEMO data"

    def __init__(self, master, app):
        super().__init__(master, app); self.pe = {}
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)
        b = Card(self, "Strategy builder", width=400); b.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 6)); b.pack_propagate(False); B = b.body
        Label(B, "Name", 11, C["mute"], True).pack(anchor="w"); self.name = Entry(B, 360); self.name.pack(fill="x", pady=(0, 6))
        Label(B, "Technical indicator / rule set", 11, C["mute"], True).pack(anchor="w")
        self.type = Drop(B, bt.TYPES, self.type_changed, 360); self.type.pack(fill="x", pady=(0, 6))
        Label(B, "Parameters", 11, C["mute"], True).pack(anchor="w"); self.pf = ctk.CTkFrame(B, fg_color="transparent"); self.pf.pack(fill="x"); self.pf.grid_columnconfigure(0, weight=1)
        Label(B, "Trading rules", 11, C["mute"], True).pack(anchor="w", pady=(6, 0))
        r = ctk.CTkFrame(B, fg_color="transparent"); r.pack(fill="x"); r.grid_columnconfigure((1, 3), weight=1)
        Label(r, "Stop-loss %", 11).grid(row=0, column=0, sticky="w"); self.sl = Entry(r, 70); self.sl.grid(row=0, column=1, padx=6, sticky="w")
        Label(r, "Take-profit %", 11).grid(row=0, column=2, sticky="w"); self.tp = Entry(r, 70); self.tp.grid(row=0, column=3, padx=6, sticky="w")
        self.sw_t = ctk.CTkSwitch(B, text="Trend filter: only enter above EMA(100)", progress_color=C["acc"], font=F(11)); self.sw_t.pack(anchor="w", pady=(8, 2))
        self.sw_r = ctk.CTkSwitch(B, text="RSI filter: skip entries when RSI > 75", progress_color=C["acc"], font=F(11)); self.sw_r.pack(anchor="w", pady=2)
        self.summary = Label(B, "", 11, C["acc"], wraplength=360, justify="left"); self.summary.pack(anchor="w", pady=8)
        t = ctk.CTkFrame(B, fg_color="transparent"); t.pack(fill="x")
        self.asset = Drop(t, [a["sym"] for a in dd.ASSETS], None, 130); self.asset.set("RELIANCE"); self.asset.pack(side="left")
        Btn(t, "Quick test", self.quick, "ghost", 100).pack(side="left", padx=6)
        self.qres = Label(B, "", 11, C["mute"], wraplength=360, justify="left"); self.qres.pack(anchor="w", pady=4)
        self.mini = ChartPanel(B, (3.6, 1.6)); self.mini.pack(fill="both", expand=True)
        bb = ctk.CTkFrame(B, fg_color="transparent"); bb.pack(fill="x", pady=(6, 0))
        Btn(bb, "Save strategy", self.save, width=120).pack(side="left"); Btn(bb, "New", self.new, "ghost", 70).pack(side="left", padx=6); Btn(bb, "Delete", self.delete, "danger", 80).pack(side="right")
        s = Card(self, "Saved strategies"); s.grid(row=0, column=1, sticky="nsew", pady=(0, 6))
        self.tab = Table(s.body, ("Name", "Type", "Parameters", "SL %", "TP %"), (190, 150, 260, 60, 60), height=6, on_select=lambda v: self.load(v[0])); self.tab.pack(fill="both", expand=True)
        c = Card(self, "Strategy comparison", "DEMO"); c.grid(row=1, column=1, sticky="nsew"); c.body.grid_columnconfigure(0, weight=3); c.body.grid_columnconfigure(1, weight=2); c.body.grid_rowconfigure(1, weight=1)
        ctl = ctk.CTkFrame(c.body, fg_color="transparent"); ctl.grid(row=0, column=0, columnspan=2, sticky="ew")
        Label(ctl, "Asset", 11, C["mute"], True).pack(side="left"); self.casset = Drop(ctl, [a["sym"] for a in dd.ASSETS], None, 130); self.casset.set("RELIANCE"); self.casset.pack(side="left", padx=6)
        self.cper = Drop(ctl, ["1Y", "2Y", "All"], None, 80); self.cper.set("2Y"); self.cper.pack(side="left"); Btn(ctl, "Compare all saved", self.compare, width=140).pack(side="left", padx=8)
        self.cp = ChartPanel(c.body); self.cp.grid(row=1, column=0, sticky="nsew")
        self.ct = Table(c.body, ("Strategy", "Return", "Sharpe", "Max DD", "Win %"), (140, 70, 60, 70, 60), height=6); self.ct.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

    def on_show(self, **kw): self.refresh(); self.compare() if not self.cp.fig.axes else None

    def refresh(self):
        ss = db.strategies()
        self.tab.set([(s["name"], s["type"], ", ".join(f"{k}={v:g}" for k, v in s["params"].items() if not isinstance(v, bool)), f"{s['sl']:g}", f"{s['tp']:g}") for s in ss], iids=[s["name"] for s in ss])
        if not self.name.get() and ss: self.load(ss[0]["name"])

    def type_changed(self, t, values=None):
        for w in self.pf.winfo_children(): w.destroy()
        self.pe = {}
        for i, (k, dv) in enumerate(bt.TYPES[t].items()):
            Label(self.pf, k.replace("_", " ").title(), 11).grid(row=i, column=0, sticky="w", pady=2)
            e = Entry(self.pf, 90); e.insert(0, str((values or {}).get(k, dv))); e.grid(row=i, column=1, sticky="e", pady=2); self.pe[k] = (e, type(dv))
        self.update_summary()

    def read(self):
        p = {k: (int(float(e.get())) if tp is int else float(e.get())) for k, (e, tp) in self.pe.items()}
        p["trend_filter"] = bool(self.sw_t.get()); p["rsi_filter"] = bool(self.sw_r.get())
        return p, float(self.sl.get() or 0), float(self.tp.get() or 0)

    def update_summary(self):
        try: p, sl, tp = self.read(); self.summary.configure(text="Rule: " + bt.describe(self.type.get(), p, sl, tp))
        except ValueError: self.summary.configure(text="Check numeric parameters.")

    def load(self, name):
        s = db.strategy(name)
        if not s: return
        self.name.delete(0, "end"); self.name.insert(0, s["name"]); self.type.set(s["type"]); self.type_changed(s["type"], s["params"])
        for e, v in ((self.sl, s["sl"]), (self.tp, s["tp"])): e.delete(0, "end"); e.insert(0, f"{v:g}")
        (self.sw_t.select if s["params"].get("trend_filter") else self.sw_t.deselect)(); (self.sw_r.select if s["params"].get("rsi_filter") else self.sw_r.deselect)()
        self.update_summary()

    def new(self):
        self.name.delete(0, "end"); self.name.insert(0, "My Strategy"); t = self.type.get(); self.type_changed(t)
        for e in (self.sl, self.tp): e.delete(0, "end"); e.insert(0, "0")

    def save(self):
        try: p, sl, tp = self.read()
        except ValueError: return messagebox.showerror("Invalid input", "Parameters, stop-loss and take-profit must be numbers.")
        n = self.name.get().strip()
        if not n: return messagebox.showerror("Name required", "Give the strategy a name.")
        db.save_strategy(n, self.type.get(), p, sl, tp); self.refresh(); self.tab.select(n); self.update_summary(); self.qres.configure(text=f"Saved “{n}”.", text_color=C["acc"])

    def delete(self):
        n = self.name.get().strip()
        if not db.strategy(n): return
        if db.cfg["confirm_delete"] and not messagebox.askyesno("Delete", f"Delete strategy “{n}”?"): return
        db.delete_strategy(n); self.name.delete(0, "end"); self.refresh()

    def quick(self):
        try:
            p, sl, tp = self.read(); r = bt.run(dd.series(self.asset.get()), self.type.get(), p, sl, tp, db.cfg["capital"], fee=db.cfg["fee_bps"] / 1e4)
        except Exception as e: return messagebox.showerror("Test failed", str(e))
        s = r["stats"]; self.update_summary()
        self.qres.configure(text=f"{self.asset.get()} (DEMO): return {pct(s['ret'] * 100)} · Sharpe {s['sharpe']:.2f} · MaxDD {pct(s['maxdd'] * 100)} · win {s['win'] * 100:.0f}% · {s['trades']} trades", text_color=colr(s["ret"]))
        f = self.mini.fig; f.clear(); ax = f.add_subplot(111); ch.line(ax, r["equity"], C["up"] if s["ret"] >= 0 else C["down"]); ch.style(ax); ch.datefmt(ax); self.mini.draw()

    def compare(self):
        sym = self.casset.get(); per = self.cper.get(); df = dd.series(sym)
        start = None if per == "All" else df.index[-1] - pd.Timedelta(days=365 * int(per[0])); rows, tags, items = [], [], []
        for s in db.strategies():
            try: r = bt.run(df, s["type"], s["params"], s["sl"], s["tp"], 100, start, fee=db.cfg["fee_bps"] / 1e4)
            except Exception: continue
            st = r["stats"]; rows.append((s["name"], pct(st["ret"] * 100, 1), f"{st['sharpe']:.2f}", pct(st["maxdd"] * 100, 1), f"{st['win'] * 100:.0f}%")); tags.append(sgn_tag(st["ret"])); items.append((s["name"], r["equity"], None))
        if items: items.append(("Buy & hold", r["bh"], C["mute"]))
        f = self.cp.fig; f.clear(); ax = f.add_subplot(111)
        if items: ch.curves(ax, items, "Equity (base 100)")
        else: ch.empty(ax, "No saved strategies")
        self.cp.draw(); self.ct.set(rows, tags)


import pandas as pd
