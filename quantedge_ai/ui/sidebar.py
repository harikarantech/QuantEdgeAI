import customtkinter as ctk
from PIL import Image
from core.helpers import C, F, Label, make_logo, mix
import os

NAV = [("Overview", "◈"), ("Live Markets", "◉"), ("AI Signals", "⚡"), ("Strategy Lab", "⚗"), ("Backtesting", "⏱"),
       ("Portfolio", "▤"), ("Risk Analytics", "⚠"), ("Market Research", "⌕"), ("Reports", "▦"), ("Settings", "⚙")]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select, assets_dir):
        super().__init__(master, fg_color=C["panel"], corner_radius=0, width=230)
        self.pack_propagate(False); self.on_select = on_select; self.btns = {}
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x", padx=18, pady=(22, 18))
        logo = Image.open(make_logo(os.path.join(assets_dir, "logo.png")))
        ctk.CTkLabel(top, text="", image=ctk.CTkImage(logo, size=(38, 38))).pack(side="left")
        t = ctk.CTkFrame(top, fg_color="transparent"); t.pack(side="left", padx=10)
        Label(t, "QUANTEDGE", 16, bold=True).pack(anchor="w"); Label(t, "AI TRADING TERMINAL", 8, C["acc"], True).pack(anchor="w")
        for name, ic in NAV:
            b = ctk.CTkButton(self, text=f"  {ic}   {name}", anchor="w", height=40, corner_radius=8, fg_color="transparent",
                              hover_color=C["card"], text_color=C["mute"], font=F(13, True), command=lambda n=name: on_select(n))
            b.pack(fill="x", padx=12, pady=2); self.btns[name] = b
        foot = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["line"])
        foot.pack(side="bottom", fill="x", padx=14, pady=16)
        Label(foot, "● DEMO MODE", 11, C["amber"], True).pack(anchor="w", padx=12, pady=(10, 0))
        Label(foot, "Prices and AI signals are\nsynthetic samples, not real\nmarket information.", 10, C["mute"], justify="left").pack(anchor="w", padx=12, pady=(2, 10))

    def set_active(self, name):
        for n, b in self.btns.items():
            on = n == name
            b.configure(fg_color=C["card"] if on else "transparent", text_color=C["acc"] if on else C["mute"])
