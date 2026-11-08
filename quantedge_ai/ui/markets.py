import customtkinter as ctk
from core.helpers import *
from core import database as db, demo_data as dd, chart_engine as ch


class Markets(Screen):
    title = "Live Markets"; subtitle = "Search assets, watchlists, price and volume charts · DEMO quotes (daily bars)"

    def __init__(self, master, app):
        super().__init__(master, app); self.sym = None
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        left = Card(self, "Assets", "DEMO", width=330); left.grid(row=0, column=0, sticky="nsew", padx=(0, 6)); left.pack_propagate(False)
        self.list = AssetList(left.body, self.pick, ("All", "Stocks", "Crypto", "Index", "★ Watch"), watch=lambda: db.cfg["watchlist"]); self.list.pack(fill="both", expand=True)
        r = ctk.CTkFrame(self, fg_color="transparent"); r.grid(row=0, column=1, sticky="nsew"); r.grid_columnconfigure(0, weight=1); r.grid_rowconfigure(2, weight=1)
        h = ctk.CTkFrame(r, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["line"]); h.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.name = Label(h, "", 18, bold=True); self.name.pack(side="left", padx=16, pady=12)
        self.price = Label(h, "", 20, bold=True); self.price.pack(side="left", padx=(20, 8))
        self.chg = Label(h, "", 13, bold=True); self.chg.pack(side="left")
        self.src = Label(h, "", 9, "#04120e", True, fg_color=C["amber"], corner_radius=5); self.src.pack(side="right", padx=16)
        self.stat = Label(h, "", 11, C["mute"]); self.stat.pack(side="right", padx=8)
        c = ctk.CTkFrame(r, fg_color="transparent"); c.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.tf = Seg(c, ("1W", "1M", "3M", "6M", "1Y", "3Y"), lambda v: self.render()); self.tf.set(db.cfg["default_tf"]); self.tf.pack(side="left")
        self.kind = Seg(c, ("Line", "Candles"), lambda v: self.render()); self.kind.set(db.cfg["chart_type"]); self.kind.pack(side="left", padx=10)
        Btn(c, "Research ›", lambda: self.app.goto("Market Research", symbol=self.sym), "ghost", 90).pack(side="right")
        Btn(c, "+ Portfolio", lambda: self.app.goto("Portfolio", symbol=self.sym), "ghost", 90).pack(side="right", padx=6)
        self.watch = Btn(c, "☆ Watch", self.toggle, "ghost", 90); self.watch.pack(side="right")
        cc = Card(r, "Price & volume", "DEMO"); cc.grid(row=2, column=0, sticky="nsew"); self.cp = ChartPanel(cc.body); self.cp.pack(fill="both", expand=True)
        self.ohlc = ctk.CTkFrame(r, fg_color="transparent"); self.ohlc.grid(row=3, column=0, sticky="ew", pady=(6, 0)); self.ohlc.grid_columnconfigure(tuple(range(5)), weight=1)
        self.tiles = [Stat(self.ohlc, l, 15) for l in ("Open", "High", "Low", "Volume", "52W Range")]
        for i, t in enumerate(self.tiles): t.grid(row=0, column=i, sticky="ew", padx=3)

    def on_show(self, symbol=None, **kw):
        self.list.refresh()
        self.pick(symbol or self.sym or "RELIANCE")
        self.list.select(self.sym)

    def pick(self, sym):
        if sym == self.sym and self.cp.fig.axes: return
        self.sym = sym; self.render()

    def toggle(self):
        w = list(db.cfg["watchlist"]); w.remove(self.sym) if self.sym in w else w.append(self.sym)
        db.cfg_set("watchlist", w); self.render(); self.list.refresh()

    def render(self):
        s = self.sym; a = dd.ASSET[s]; q = dd.quote(s); df = dd.series(s); w = dd.window(df, self.tf.get())
        self.name.configure(text=f"{s} · {a['name']}"); self.price.configure(text=inr(q["last"]))
        self.chg.configure(text=f"{q['chg']:+,.2f} ({pct(q['pct'])})", text_color=colr(q["chg"]))
        self.src.configure(text=f" {dd.source(s)} DATA "); self.stat.configure(text=a["cls"] if a["sector"] == a["cls"] else f"{a['cls']} · {a['sector']}")
        self.watch.configure(text="★ Watching" if s in db.cfg["watchlist"] else "☆ Watch")
        l = df.iloc[-1]; y = df[df.index >= df.index[-1] - pd.Timedelta(days=365)]
        for t, v in zip(self.tiles, (inr(l.open), inr(l.high), inr(l.low), compact(l.volume), f"{compact(y.low.min())} – {compact(y.high.max())}")): t.set(v)
        ch.price_volume(self.cp.fig, w, self.kind.get()); self.cp.draw()


import pandas as pd
