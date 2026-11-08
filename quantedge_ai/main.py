"""QUANTEDGE AI — AI Trading Intelligence Terminal (DEMO data). Run: python main.py"""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import customtkinter as ctk
from core import database as db, helpers as H

SCREENS = {  # nav name -> (module, class)
    "Overview": ("dashboard", "Dashboard"), "Live Markets": ("markets", "Markets"), "AI Signals": ("signals", "Signals"),
    "Strategy Lab": ("strategy_lab", "StrategyLab"), "Backtesting": ("backtesting", "Backtesting"),
    "Portfolio": ("portfolio", "Portfolio"), "Risk Analytics": ("risk_analytics", "RiskAnalytics"),
    "Market Research": ("research", "Research"), "Reports": ("reports", "Reports"), "Settings": ("settings", "Settings"),
}


class App(ctk.CTk):
    def __init__(self):
        db.init(); H.apply_theme()
        ctk.set_appearance_mode("dark")
        try: ctk.set_widget_scaling(int(db.cfg["scale"].rstrip("%")) / 100)
        except Exception: pass
        super().__init__(fg_color=H.C["bg"])
        from ui.sidebar import Sidebar
        from ui.header import Header
        self.title("QUANTEDGE AI — Trading Intelligence Terminal (DEMO)")
        self.geometry("1480x900"); self.minsize(1240, 760)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.sidebar = Sidebar(self, self.show, os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        right = ctk.CTkFrame(self, fg_color="transparent"); right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1); right.grid_rowconfigure(1, weight=1)
        self.header = Header(right); self.header.grid(row=0, column=0, sticky="ew")
        self.content = ctk.CTkFrame(right, fg_color="transparent"); self.content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        self.content.grid_columnconfigure(0, weight=1); self.content.grid_rowconfigure(0, weight=1)
        self.frames, self.current = {}, None
        try:
            from PIL import ImageTk, Image
            self._ico = ImageTk.PhotoImage(Image.open(os.path.join(os.path.dirname(__file__), "assets", "logo.png"))); self.iconphoto(True, self._ico)
        except Exception: pass

    def show(self, name, **kw):
        if name not in self.frames:
            mod, cls = SCREENS[name]
            self.frames[name] = getattr(importlib.import_module(f"ui.{mod}"), cls)(self.content, self)
            self.frames[name].grid(row=0, column=0, sticky="nsew")
        if self.current and self.current != name: self.frames[self.current].grid_remove()
        f = self.frames[name]; f.grid(); self.current = name
        self.sidebar.set_active(name); self.header.set(f.title, f.subtitle); f.on_show(**kw)

    goto = show

    def restart(self):
        os.execl(sys.executable, sys.executable, *sys.argv)


def main():
    app = App()
    if "--selftest" in sys.argv:
        for n in SCREENS:
            app.show(n); app.update_idletasks(); app.update(); print("OK", n)
        app.destroy(); return
    app.show(db.cfg.get("startup", "Overview") if db.cfg.get("startup") in SCREENS else "Overview")
    app.mainloop()


if __name__ == "__main__":
    main()
