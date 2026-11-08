import customtkinter as ctk
from tkinter import messagebox
from core.helpers import *
from core import database as db, demo_data as dd, analytics as an, chart_engine as ch


class Portfolio(Screen):
    title = "Portfolio Management"; subtitle = "Positions, allocation and P&L · quantities and entries are yours, prices are DEMO"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.grid_columnconfigure(tuple(range(10)), weight=1, uniform="c"); self.grid_rowconfigure(1, weight=3); self.grid_rowconfigure(2, weight=2)
        self.tiles = [Stat(self, l, 20) for l in ("Market Value", "Invested", "Unrealised P&L", "Day P&L", "Positions")]
        for i, t in enumerate(self.tiles): t.grid(row=0, column=i * 2, columnspan=2, sticky="nsew", padx=3, pady=3)
        p = Card(self, "Positions", "DEMO PRICES"); p.grid(row=1, column=0, columnspan=6, sticky="nsew", padx=3, pady=3)
        self.tab = Table(p.body, ("Symbol", "Qty", "Entry", "Last", "Value", "P&L", "P&L %", "Weight"), (80, 60, 85, 85, 100, 95, 70, 65), height=8, on_select=lambda v: self.fill(v)); self.tab.pack(fill="both", expand=True)
        a = Card(self, "Allocation & P&L", "DEMO"); a.grid(row=1, column=6, columnspan=4, sticky="nsew", padx=3, pady=3); self.cp = ChartPanel(a.body); self.cp.pack(fill="both", expand=True)
        f = Card(self, "Add / edit position"); f.grid(row=2, column=0, columnspan=6, sticky="nsew", padx=3, pady=3); F_ = f.body; F_.grid_columnconfigure((0, 1, 2), weight=1)
        for i, t in enumerate(("ASSET", "QUANTITY", "ENTRY PRICE ₹")): Label(F_, t, 10, C["mute"], True).grid(row=0, column=i, sticky="w", padx=6)
        self.asset = Drop(F_, [a_["sym"] for a_ in dd.ASSETS if a_["cls"] != "Index"], lambda v: self.autoprice(), 150); self.asset.grid(row=1, column=0, sticky="w", padx=6)
        self.qty = Entry(F_, 120); self.qty.grid(row=1, column=1, sticky="w", padx=6); self.ent = Entry(F_, 130); self.ent.grid(row=1, column=2, sticky="w", padx=6)
        b = ctk.CTkFrame(F_, fg_color="transparent"); b.grid(row=2, column=0, columnspan=3, sticky="w", pady=10)
        Btn(b, "Add / merge", lambda: self.add(True), width=110).pack(side="left", padx=4); Btn(b, "Update selected", lambda: self.add(False), "ghost", 130).pack(side="left", padx=4)
        Btn(b, "Remove selected", self.remove, "danger", 130).pack(side="left", padx=4); Btn(b, "Use last price", self.autoprice, "ghost", 120).pack(side="left", padx=4)
        self.msg = Label(F_, "", 11, C["mute"]); self.msg.grid(row=3, column=0, columnspan=3, sticky="w", padx=6)
        pf = Card(self, "Performance (current holdings)", "DEMO"); pf.grid(row=2, column=6, columnspan=4, sticky="nsew", padx=3, pady=3)
        self.pt = Table(pf.body, ("Period", "Return", "P&L ₹"), (80, 90, 120), height=6); self.pt.pack(fill="both", expand=True)

    def on_show(self, symbol=None, **kw):
        if symbol and symbol in dd.ASSET and dd.ASSET[symbol]["cls"] != "Index": self.asset.set(symbol); self.autoprice(); self.qty.delete(0, "end")
        self.refresh()

    def autoprice(self, *a): self.ent.delete(0, "end"); self.ent.insert(0, f"{dd.quote(self.asset.get())['last']:.2f}")

    def fill(self, v):
        self.asset.set(v[0]); p = next(x for x in db.positions() if x["symbol"] == v[0])
        for e, val in ((self.qty, p["qty"]), (self.ent, p["entry"])): e.delete(0, "end"); e.insert(0, f"{val:g}" if e is self.qty else f"{val:.2f}")

    def refresh(self):
        t = an.pos_table(); val, cost = t.value.sum(), t.cost.sum(); pnl = val - cost; day = t.day.sum(); T = self.tiles
        T[0].set(inr(val, 0)); T[1].set(inr(cost, 0)); T[2].set(inr(pnl, 0, True), pct(pnl / cost * 100 if cost else 0), colr(pnl), colr(pnl)); T[3].set(inr(day, 0, True), "", colr(day)); T[4].set(str(len(t)))
        self.tab.set([(r.symbol, f"{r.qty:g}", compact(r.entry), compact(r.last), inr(r.value, 0), inr(r.pnl, 0, True), pct(r.pnl_pct, 1), f"{r.weight:.1f}%") for r in t.itertuples()],
                     [sgn_tag(r.pnl) for r in t.itertuples()], iids=list(t.symbol))
        f = self.cp.fig; f.clear(); gs = f.add_gridspec(2, 1, height_ratios=[1.3, 1]); a = f.add_subplot(gs[0]); b = f.add_subplot(gs[1])
        if len(t): ch.donut(a, list(t.symbol), list(t.value), inr(val / 1e5, 1).replace("₹", "₹") + "L"); ch.hbar(b, list(t.symbol), list(t.pnl_pct))
        else: ch.empty(a, "No positions"); ch.empty(b, "")
        self.cp.draw(); pt = an.period_table(); self.pt.set([(l, pct(r), inr(p_, 0, True)) for l, r, p_ in pt], [sgn_tag(r) for _, r, _ in pt])

    def add(self, merge):
        try: q, e = float(self.qty.get()), float(self.ent.get()); assert q > 0 and e > 0
        except Exception: return messagebox.showerror("Invalid input", "Quantity and entry price must be positive numbers.")
        db.upsert_position(self.asset.get(), q, e, merge); self.msg.configure(text=f"{'Added to' if merge else 'Updated'} {self.asset.get()}.", text_color=C["acc"]); self.refresh()

    def remove(self):
        v = self.tab.selected()
        if not v: return messagebox.showinfo("Select a position", "Click a row in the positions table first.")
        if db.cfg["confirm_delete"] and not messagebox.askyesno("Remove", f"Remove {v[0]} from the portfolio?"): return
        db.remove_position(v[0]); self.msg.configure(text=f"Removed {v[0]}.", text_color=C["amber"]); self.refresh()
