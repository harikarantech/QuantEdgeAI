import customtkinter as ctk, pandas as pd
from tkinter import messagebox, filedialog
from core.helpers import *
from core import database as db, demo_data as dd, backtest as bt, chart_engine as ch


class Backtesting(Screen):
    title = "Backtesting"; subtitle = "Test saved strategies on historical bars · DEMO data, next-bar execution, fees included"

    def __init__(self, master, app):
        super().__init__(master, app); self.res = None
        self.grid_columnconfigure(tuple(range(8)), weight=1, uniform="s"); self.grid_rowconfigure(2, weight=1)
        ctl = Card(self); ctl.grid(row=0, column=0, columnspan=8, sticky="ew", padx=3, pady=3); k = ctl.body
        def lab(t, c): Label(k, t, 10, C["mute"], True).grid(row=0, column=c, sticky="w", padx=6)
        lab("ASSET", 0); lab("STRATEGY", 1); lab("RANGE", 2); lab("START (YYYY-MM-DD)", 3); lab("END", 4); lab("INITIAL CAPITAL ₹", 5)
        self.asset = Drop(k, [a["sym"] for a in dd.ASSETS], None, 130); self.asset.set("RELIANCE"); self.asset.grid(row=1, column=0, padx=6)
        self.strat = Drop(k, ["-"], None, 200); self.strat.grid(row=1, column=1, padx=6)
        self.rng = Drop(k, ["6M", "1Y", "2Y", "3Y", "Custom"], self.preset, 90); self.rng.set("2Y"); self.rng.grid(row=1, column=2, padx=6)
        self.start = Entry(k, 120); self.start.grid(row=1, column=3, padx=6); self.end = Entry(k, 120); self.end.grid(row=1, column=4, padx=6)
        self.cap = Entry(k, 120); self.cap.grid(row=1, column=5, padx=6); self.cap.insert(0, str(int(db.cfg["capital"])))
        Btn(k, "▶ Run backtest", self.run, width=130).grid(row=1, column=6, padx=10)
        self.tiles = [Stat(self, l, 18) for l in ("Total Return", "CAGR", "Max Drawdown", "Sharpe", "Win Rate", "Trades", "Profit Factor", "Buy & Hold")]
        for i, t in enumerate(self.tiles): t.grid(row=1, column=i, sticky="nsew", padx=3, pady=3)
        e = Card(self, "Equity curve & drawdown", "DEMO"); e.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=3, pady=3); self.cp = ChartPanel(e.body); self.cp.pack(fill="both", expand=True)
        t = Card(self, "Trade history", "DEMO"); t.grid(row=2, column=4, columnspan=4, sticky="nsew", padx=3, pady=3)
        self.tt = Table(t.body, ("#", "Entry", "Exit", "Entry ₹", "Exit ₹", "P&L ₹", "Ret %"), (30, 78, 78, 70, 70, 100, 62), height=10); self.tt.pack(fill="both", expand=True)
        Btn(t.body, "Export trades CSV", self.export, "ghost", 150).pack(anchor="e", pady=(6, 0))

    def on_show(self, symbol=None, strategy=None, **kw):
        names = [s["name"] for s in db.strategies()] or ["-"]; self.strat.configure(values=names)
        if self.strat.get() not in names: self.strat.set(names[0])
        if strategy in names: self.strat.set(strategy)
        if symbol in dd.ASSET: self.asset.set(symbol)
        if not self.end.get(): self.preset("2Y")
        self.run()

    def preset(self, v):
        if v == "Custom": return
        df = dd.series(self.asset.get()); end = df.index[-1]; days = {"6M": 182, "1Y": 365, "2Y": 730, "3Y": 1095}[v]
        for e, val in ((self.start, (end - pd.Timedelta(days=days)).strftime("%Y-%m-%d")), (self.end, end.strftime("%Y-%m-%d"))): e.delete(0, "end"); e.insert(0, val)

    def run(self):
        s = db.strategy(self.strat.get())
        if not s: return messagebox.showinfo("No strategy", "Create a strategy in Strategy Lab first.")
        try:
            cap = float(self.cap.get().replace(",", "")); st, en = pd.to_datetime(self.start.get()), pd.to_datetime(self.end.get())
            if en <= st or cap <= 0: raise ValueError("End must be after start and capital must be positive.")
            r = bt.run(dd.series(self.asset.get()), s["type"], s["params"], s["sl"], s["tp"], cap, st, en, db.cfg["fee_bps"] / 1e4)
        except Exception as ex: return messagebox.showerror("Backtest error", f"{ex}")
        self.res = r; x = r["stats"]; T = self.tiles
        T[0].set(pct(x["ret"] * 100), inr(x["final"], 0), colr(x["ret"]), colr(x["ret"])); T[1].set(pct(x["cagr"] * 100), "annualised", colr(x["cagr"]))
        T[2].set(pct(x["maxdd"] * 100), "peak to trough", C["down"]); T[3].set(f"{x['sharpe']:.2f}", "rf = 0", C["acc"] if x["sharpe"] > 1 else None)
        T[4].set(f"{x['win'] * 100:.0f}%", f"{x['trades']} closed trades"); T[5].set(str(x["trades"]), f"fee {db.cfg['fee_bps']} bps")
        T[6].set("∞" if x["pf"] == float("inf") else f"{x['pf']:.2f}", "gross win / loss"); T[7].set(pct(x["bh"] * 100), "benchmark", colr(x["bh"]))
        f = self.cp.fig; f.clear(); gs = f.add_gridspec(4, 1); a = f.add_subplot(gs[:3]); b = f.add_subplot(gs[3], sharex=a)
        ch.curves(a, [(s["name"], r["equity"], C["acc"]), ("Buy & hold", r["bh"], C["mute"])]); a.tick_params(labelbottom=False)
        tr = r["trades"]
        if len(tr): a.scatter(tr.entry, r["equity"].reindex(tr.entry, method="nearest").values, marker="^", color=C["up"], s=22, zorder=5); a.scatter(tr.exit, r["equity"].reindex(tr.exit, method="nearest").values, marker="v", color=C["down"], s=22, zorder=5)
        ch.drawdown(b, r["dd"]); self.cp.draw()
        self.tt.set([(i + 1, t.entry.strftime("%d %b %y"), t.exit.strftime("%d %b %y") + ("*" if t.open else ""), compact(t.ep), compact(t.xp), inr(t.pnl, 0, True), pct(t.ret * 100, 1)) for i, t in tr.iterrows()],
                    [sgn_tag(t.pnl) for _, t in tr.iterrows()])

    def export(self):
        if self.res is None or self.res["trades"].empty: return messagebox.showinfo("Nothing to export", "Run a backtest with trades first.")
        p = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"trades_{self.asset.get()}.csv")
        if p: self.res["trades"].to_csv(p, index=False); messagebox.showinfo("Exported", p)
