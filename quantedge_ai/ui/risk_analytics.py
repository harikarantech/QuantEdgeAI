import customtkinter as ctk
from core.helpers import *
from core import analytics as an, chart_engine as ch


class RiskAnalytics(Screen):
    title = "Risk Analytics"; subtitle = "Volatility, drawdown, VaR and concentration of the current portfolio · DEMO price history"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.grid_columnconfigure(tuple(range(6)), weight=1, uniform="c"); self.grid_rowconfigure(1, weight=3); self.grid_rowconfigure(2, weight=2)
        self.tiles = [Stat(self, l, 20) for l in ("Risk Score", "Volatility (ann.)", "Max Drawdown", "Sharpe (rf=0)", "VaR 95% · 1 day", "CVaR 95% · 1 day")]
        for i, t in enumerate(self.tiles): t.grid(row=0, column=i, sticky="nsew", padx=3, pady=3)
        self.cps = []
        for i, (t, c) in enumerate((("Drawdown", 2), ("Return distribution", 2), ("Concentration", 2))):
            k = Card(self, t, "DEMO"); k.grid(row=1, column=i * 2, columnspan=2, sticky="nsew", padx=3, pady=3); cp = ChartPanel(k.body, (4, 3)); cp.pack(fill="both", expand=True); self.cps.append(cp)
        al = Card(self, "Risk alerts"); al.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=3, pady=3); self.al = ctk.CTkScrollableFrame(al.body, fg_color="transparent"); self.al.pack(fill="both", expand=True)
        rc = Card(self, "Risk contribution (covariance based)", "DEMO"); rc.grid(row=2, column=3, columnspan=3, sticky="nsew", padx=3, pady=3)
        self.rc = Table(rc.body, ("Asset", "Weight", "Ann. vol", "Risk share"), (100, 80, 80, 90), height=6); self.rc.pack(fill="both", expand=True)

    def on_show(self, **kw):
        r = an.risk(); T = self.tiles
        if not r:
            for t in T: t.set("–", "add positions")
            return
        sc = {"Low": C["up"], "Moderate": C["amber"], "High": C["down"]}[r["label"]]
        T[0].set(f"{r['score']:.0f}/100", r["label"], sc, sc); T[1].set(f"{r['vol'] * 100:.1f}%"); T[2].set(pct(r["maxdd"] * 100), "peak to trough", C["down"])
        T[3].set(f"{r['sharpe']:.2f}"); T[4].set(inr(r["var"], 0), f"{r['var'] / r['value'] * 100:.2f}% of value", C["amber"]); T[5].set(inr(r["cvar"], 0), "expected shortfall", C["down"])
        f = self.cps[0].fig; f.clear(); ch.drawdown(f.add_subplot(111), r["dd"]); self.cps[0].draw()
        f = self.cps[1].fig; f.clear(); ch.histogram(f.add_subplot(111), r["rets"], r["var"] / r["value"] * 100); self.cps[1].draw()
        t = r["table"].sort_values("weight"); f = self.cps[2].fig; f.clear(); ch.hbar(f.add_subplot(111), list(t.symbol), list(t.weight), "{:.1f}%", False); self.cps[2].draw()
        for w in self.al.winfo_children(): w.destroy()
        col = {"HIGH": C["down"], "MEDIUM": C["amber"], "LOW": C["blue"]}
        for sev, msg in r["alerts"]:
            row = ctk.CTkFrame(self.al, fg_color="transparent"); row.pack(fill="x", pady=2)
            Label(row, f" {sev} ", 9, "#04120e", True, fg_color=col[sev], corner_radius=4, width=62).pack(side="left"); Label(row, msg, 11, wraplength=520, justify="left").pack(side="left", padx=8)
        c = sorted(r["contrib"], key=lambda x: -x[3]); self.rc.set([(s, f"{w:.1f}%", f"{v:.1f}%", f"{m:.1f}%") for s, w, v, m in c], ["neg" if m > w * 1.2 else "" for s, w, v, m in c])
