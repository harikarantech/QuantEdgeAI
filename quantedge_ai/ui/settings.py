import customtkinter as ctk
from tkinter import messagebox, filedialog
from core.helpers import *
from core import database as db, demo_data as dd
from ui.sidebar import NAV


class Settings(Screen):
    title = "Settings"; subtitle = "Appearance, charts, data sources and preferences · saved locally in SQLite"

    def __init__(self, master, app):
        super().__init__(master, app); self.w = {}
        self.grid_columnconfigure((0, 1), weight=1, uniform="c"); sc = self
        def card(t, r, c): k = Card(self, t); k.grid(row=r, column=c, sticky="nsew", padx=4, pady=4); k.body.grid_columnconfigure(1, weight=1); return k.body
        a = card("Appearance", 0, 0); ch_ = card("Charts", 0, 1); d = card("Data source", 1, 0); p = card("Preferences", 1, 1)
        self.drop(a, 0, "Theme", "theme", list(PALETTES)); self.drop(a, 1, "Accent colour", "accent", list(ACCENTS)); self.drop(a, 2, "UI scale", "scale", ["90%", "100%", "110%", "125%"])
        self.drop(a, 3, "Up / down colours", "candle_style", list(UPDOWN)); Label(a, "Theme, accent, scale and colours apply after restart.", 10, C["mute"]).grid(row=4, column=0, columnspan=2, sticky="w", pady=6)
        Btn(a, "Save & restart now", self.save_restart, width=160).grid(row=5, column=0, columnspan=2, sticky="w")
        self.drop(ch_, 0, "Default timeframe", "default_tf", ["1W", "1M", "3M", "6M", "1Y", "3Y"]); self.drop(ch_, 1, "Default chart type", "chart_type", ["Line", "Candles"])
        self.sw(ch_, 2, "Show grid lines", "grid"); self.sw(ch_, 3, "Show volume panel", "show_volume")
        Label(d, "Mode", 12).grid(row=0, column=0, sticky="w", pady=4); Label(d, "DEMO (synthetic, built-in)", 12, C["amber"], True).grid(row=0, column=1, sticky="w")
        Label(d, "Local CSV folder", 12).grid(row=1, column=0, sticky="w", pady=4); self.csv = Entry(d, 260); self.csv.grid(row=1, column=1, sticky="ew"); self.csv.insert(0, db.cfg["csv_dir"])
        b = ctk.CTkFrame(d, fg_color="transparent"); b.grid(row=2, column=0, columnspan=2, sticky="w", pady=4); Btn(b, "Browse…", self.browse, "ghost", 90).pack(side="left"); Btn(b, "Apply & test", self.apply_csv, width=110).pack(side="left", padx=6)
        self.dmsg = Label(d, "Files named SYMBOL.csv (Date,Open,High,Low,Close,Volume) replace the demo series for that symbol. No APIs, no cloud.", 10, C["mute"], wraplength=420, justify="left"); self.dmsg.grid(row=3, column=0, columnspan=2, sticky="w")
        self.drop(p, 0, "Start screen", "startup", [n for n, _ in NAV]); self.sw(p, 1, "Confirm before deleting", "confirm_delete")
        Label(p, "Default capital ₹", 12).grid(row=2, column=0, sticky="w", pady=4); self.cap = Entry(p, 130); self.cap.insert(0, str(int(db.cfg["capital"]))); self.cap.grid(row=2, column=1, sticky="w")
        Label(p, "Trading fee (bps)", 12).grid(row=3, column=0, sticky="w", pady=4); self.fee = Entry(p, 130); self.fee.insert(0, str(db.cfg["fee_bps"])); self.fee.grid(row=3, column=1, sticky="w")
        bb = ctk.CTkFrame(p, fg_color="transparent"); bb.grid(row=4, column=0, columnspan=2, sticky="w", pady=8)
        Btn(bb, "Save settings", self.save, width=120).pack(side="left"); Btn(bb, "Defaults", self.defaults, "ghost", 90).pack(side="left", padx=6); Btn(bb, "Reset demo portfolio", self.reseed, "danger", 150).pack(side="left")
        self.msg = Label(p, "", 11, C["acc"]); self.msg.grid(row=5, column=0, columnspan=2, sticky="w")

    def drop(self, m, r, lab, key, vals):
        Label(m, lab, 12).grid(row=r, column=0, sticky="w", pady=4); o = Drop(m, vals, None, 180); o.set(str(db.cfg[key])); o.grid(row=r, column=1, sticky="w"); self.w[key] = o

    def sw(self, m, r, lab, key):
        s = ctk.CTkSwitch(m, text=lab, progress_color=C["acc"], font=F(12)); s.grid(row=r, column=0, columnspan=2, sticky="w", pady=6); (s.select if db.cfg[key] else s.deselect)(); self.w[key] = s

    def browse(self):
        p = filedialog.askdirectory()
        if p: self.csv.delete(0, "end"); self.csv.insert(0, p)

    def apply_csv(self):
        p = self.csv.get().strip(); db.cfg_set("csv_dir", p); dd.clear_cache()
        n = sum(dd._csv(a["sym"]) is not None for a in dd.ASSETS) if p else 0
        self.dmsg.configure(text=f"{n} CSV file(s) loaded; other symbols stay on DEMO data." if p else "CSV folder cleared: all symbols use DEMO data.", text_color=C["acc"])

    def save(self):
        try: cap, fee = float(self.cap.get()), float(self.fee.get()); assert cap > 0 and fee >= 0
        except Exception: return messagebox.showerror("Invalid input", "Capital must be positive and fee must be a number ≥ 0.")
        for k, w in self.w.items(): db.cfg_set(k, bool(w.get()) if isinstance(w, ctk.CTkSwitch) else w.get())
        db.cfg_set("capital", cap); db.cfg_set("fee_bps", fee); self.msg.configure(text="Saved. Chart settings apply immediately; theme settings after restart.")
        for f in self.app.frames.values(): f.on_show() if f is not self and f.winfo_ismapped() else None

    def save_restart(self): self.save(); self.app.restart()

    def defaults(self):
        if messagebox.askyesno("Defaults", "Restore default settings?"): db.reset_settings(); self.app.restart()

    def reseed(self):
        if messagebox.askyesno("Reset", "Replace portfolio and strategies with the DEMO starters?"): db.seed_demo(True); self.msg.configure(text="Demo portfolio and strategies restored.")
