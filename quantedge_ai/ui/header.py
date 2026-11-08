import customtkinter as ctk
from core.helpers import C, Label, market_status


class Header(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["bg"], corner_radius=0, height=70)
        self.pack_propagate(False)
        l = ctk.CTkFrame(self, fg_color="transparent"); l.pack(side="left", padx=22)
        self.t = Label(l, "", 22, bold=True); self.t.pack(anchor="w", pady=(10, 0))
        self.s = Label(l, "", 11, C["mute"]); self.s.pack(anchor="w")
        r = ctk.CTkFrame(self, fg_color="transparent"); r.pack(side="right", padx=22)
        Label(r, " DEMO DATA ", 10, "#04120e", True, fg_color=C["amber"], corner_radius=5).pack(side="right", padx=(12, 0))
        self.clock = Label(r, "", 11, C["mute"]); self.clock.pack(side="right", padx=(12, 0))
        self.nse = Label(r, "", 11, C["mute"], True); self.nse.pack(side="right", padx=(12, 0))
        Label(r, "CRYPTO ● 24/7", 11, C["acc"], True).pack(side="right", padx=(12, 0))
        self.tick()

    def set(self, t, s): self.t.configure(text=t); self.s.configure(text=s)

    def tick(self):
        now, op = market_status()
        self.nse.configure(text="NSE ● OPEN" if op else "NSE ● CLOSED", text_color=C["up"] if op else C["down"])
        self.clock.configure(text=now.strftime("%a %d %b  %H:%M:%S IST"))
        self.after(1000, self.tick)
