"""Theme, formatting and reusable CustomTkinter widgets."""
import sys, os, datetime as dt
import customtkinter as ctk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from . import database as db

FONT = "Segoe UI" if sys.platform.startswith("win") else ("SF Pro Display" if sys.platform == "darwin" else "DejaVu Sans")
MONO = "Consolas" if sys.platform.startswith("win") else ("Menlo" if sys.platform == "darwin" else "DejaVu Sans Mono")
C = dict(bg="#0a1220", panel="#0d1728", card="#111d33", line="#1f2d47", text="#e6edf7", mute="#8696b1",
         acc="#10d9a0", up="#10d9a0", down="#f0506e", amber="#f5b942", blue="#3b82f6")
PALETTES = {"Navy Terminal": dict(bg="#0a1220", panel="#0d1728", card="#111d33", line="#1f2d47"),
            "Charcoal": dict(bg="#0b0d10", panel="#12161b", card="#171c23", line="#262d38"),
            "Midnight Teal": dict(bg="#06131a", panel="#0a1b25", card="#0e2530", line="#1a3744")}
ACCENTS = {"Emerald": "#10d9a0", "Teal": "#14b8a6", "Cyan": "#22d3ee", "Amber": "#f5b942"}
UPDOWN = {"Green / Red": ("#10d9a0", "#f0506e"), "Blue / Orange": ("#3b82f6", "#fb923c")}


def apply_theme():
    C.update(PALETTES.get(db.cfg["theme"], PALETTES["Navy Terminal"]))
    C["acc"] = ACCENTS.get(db.cfg["accent"], C["acc"])
    C["up"], C["down"] = UPDOWN.get(db.cfg["candle_style"], UPDOWN["Green / Red"])


def F(size=12, bold=False):
    return ctk.CTkFont(family=FONT, size=size, weight="bold" if bold else "normal")


def mix(h, o="#ffffff", t=.15):
    a = [int(h[i:i + 2], 16) for i in (1, 3, 5)]; b = [int(o[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def inr(x, d=2, sign=False):
    s = f"{abs(x):.{d}f}"; ip, _, fp = s.partition("."); tail, head, parts = ip[-3:], ip[:-3], []
    while len(head) > 2: parts.insert(0, head[-2:]); head = head[:-2]
    if head: parts.insert(0, head)
    out = ",".join(parts + [tail]) + (("." + fp) if fp else "")
    pre = "-" if x < 0 else ("+" if sign else "")
    return f"{pre}₹{out}"


def pct(x, d=2): return f"{x:+.{d}f}%"
def colr(x): return C["up"] if x >= 0 else C["down"]
def sgn_tag(x): return "pos" if x >= 0 else "neg"


def compact(v):
    a = abs(v)
    if a >= 1e7: return f"{v / 1e7:.1f}Cr"
    if a >= 1e5: return f"{v / 1e5:.1f}L"
    if a >= 1000: return f"{v:,.0f}"
    return f"{v:.1f}" if a >= 10 else f"{v:.2f}"


def market_status():
    now = dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)
    open_ = now.weekday() < 5 and dt.time(9, 15) <= now.time() <= dt.time(15, 30)
    return now, open_


def make_logo(path):
    from PIL import Image, ImageDraw
    if os.path.exists(path): return path
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 120, 120), 26, fill="#10d9a0")
    d.rounded_rectangle((20, 20, 108, 108), 18, fill="#0a1220")
    d.ellipse((34, 34, 82, 82), outline="#10d9a0", width=9)
    d.line((70, 70, 98, 98), fill="#10d9a0", width=10)
    d.polygon([(84, 40), (100, 40), (100, 56)], fill="#14b8a6")
    im.save(path); return path


# ---------- widgets ----------
def Label(master, text="", size=12, color=None, bold=False, **kw):
    return ctk.CTkLabel(master, text=text, font=F(size, bold), text_color=color or C["text"], **kw)


def Btn(master, text, command=None, kind="primary", width=110, **kw):
    fg, tc = {"primary": (C["acc"], "#04120e"), "ghost": (C["line"], C["text"]), "danger": (C["down"], "#ffffff")}[kind]
    return ctk.CTkButton(master, text=text, command=command, width=width, height=30, corner_radius=6, fg_color=fg,
                         text_color=tc, hover_color=mix(fg), font=F(12, True), **kw)


def Seg(master, values, command=None, **kw):
    return ctk.CTkSegmentedButton(master, values=list(values), command=command, fg_color=C["panel"], selected_color=C["acc"],
                                  selected_hover_color=mix(C["acc"]), unselected_color=C["panel"], unselected_hover_color=C["line"],
                                  text_color=C["text"], font=F(11, True), **kw)


def Drop(master, values, command=None, width=150, **kw):
    return ctk.CTkOptionMenu(master, values=list(values), command=command, width=width, height=30, fg_color=C["panel"],
                             button_color=C["line"], button_hover_color=mix(C["line"]), dropdown_fg_color=C["card"],
                             dropdown_hover_color=C["line"], dropdown_text_color=C["text"], text_color=C["text"], font=F(12), **kw)


def Entry(master, width=120, **kw):
    return ctk.CTkEntry(master, width=width, height=30, fg_color=C["panel"], border_color=C["line"], text_color=C["text"],
                        placeholder_text_color=C["mute"], font=F(12), **kw)


class Card(ctk.CTkFrame):
    def __init__(self, master, title="", badge=None, **kw):
        super().__init__(master, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["line"], **kw)
        if title:
            h = ctk.CTkFrame(self, fg_color="transparent"); h.pack(fill="x", padx=14, pady=(10, 0))
            Label(h, title.upper(), 11, C["mute"], True).pack(side="left")
            if badge: Label(h, badge, 9, C["amber"], True).pack(side="right")
        self.body = ctk.CTkFrame(self, fg_color="transparent"); self.body.pack(fill="both", expand=True, padx=10, pady=8)


class Stat(ctk.CTkFrame):
    def __init__(self, master, label, size=22):
        super().__init__(master, fg_color=C["card"], corner_radius=10, border_width=1, border_color=C["line"])
        Label(self, label.upper(), 10, C["mute"], True).pack(anchor="w", padx=14, pady=(10, 0))
        self.v = Label(self, "-", size, bold=True); self.v.pack(anchor="w", padx=14)
        self.s = Label(self, "", 11, C["mute"]); self.s.pack(anchor="w", padx=14, pady=(0, 8))

    def set(self, value, sub="", color=None, subcolor=None):
        self.v.configure(text=value, text_color=color or C["text"]); self.s.configure(text=sub, text_color=subcolor or C["mute"])


_styled = [False]


def style_tree():
    s = ttk.Style(); s.theme_use("clam")
    s.configure("Q.Treeview", background=C["card"], fieldbackground=C["card"], foreground=C["text"], rowheight=26,
                borderwidth=0, bordercolor=C["card"], lightcolor=C["card"], darkcolor=C["card"], font=(FONT, 10))
    s.configure("Q.Treeview.Heading", background=C["panel"], foreground=C["mute"], relief="flat", font=(FONT, 9, "bold"), borderwidth=0, bordercolor=C["panel"], lightcolor=C["panel"], darkcolor=C["panel"])
    s.map("Q.Treeview", background=[("selected", C["line"])], foreground=[("selected", C["text"])])
    s.map("Q.Treeview.Heading", background=[("active", C["line"])])


class Table(ctk.CTkFrame):
    def __init__(self, master, cols, widths=None, height=8, on_select=None):
        super().__init__(master, fg_color="transparent")
        style_tree()
        self.cols = list(cols)
        self.tree = ttk.Treeview(self, columns=self.cols, show="headings", height=height, style="Q.Treeview", selectmode="browse", takefocus=0)
        self.tree.configure(selectmode="browse")
        for i, c in enumerate(self.cols):
            self.tree.heading(c, text=c, anchor="w" if i == 0 else "e", command=lambda c=c: self.sort(c))
            self.tree.column(c, width=(widths[i] if widths else 90), minwidth=40, anchor="w" if i == 0 else "e", stretch=True)
        sb = ctk.CTkScrollbar(self, command=self.tree.yview, width=10, height=1); self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        self.tree.tag_configure("pos", foreground=C["up"]); self.tree.tag_configure("neg", foreground=C["down"])
        self.tree.tag_configure("amb", foreground=C["amber"])
        self._rev = {}
        if on_select: self.tree.bind("<<TreeviewSelect>>", lambda e: (lambda v: v and on_select(v))(self.selected()))

    def set(self, rows, tags=None, iids=None):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            self.tree.insert("", "end", iid=(str(iids[i]) if iids else None), values=list(r), tags=((tags[i],) if tags and tags[i] else ()))

    def selected(self):
        s = self.tree.selection(); return self.tree.item(s[0], "values") if s else None

    def select(self, iid):
        if self.tree.exists(iid): self.tree.selection_set(iid); self.tree.see(iid)

    def sort(self, col):
        def key(v):
            try: return float(str(v).replace("₹", "").replace(",", "").replace("%", "").replace("+", "").replace("∞", "1e18"))
            except ValueError: return str(v)
        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children()]
        self._rev[col] = not self._rev.get(col, False)
        try: rows.sort(key=lambda x: key(x[0]), reverse=self._rev[col])
        except TypeError: rows.sort(key=lambda x: str(x[0]), reverse=self._rev[col])
        for i, (_, k) in enumerate(rows): self.tree.move(k, "", i)


class ChartPanel(ctk.CTkFrame):
    def __init__(self, master, figsize=(6, 3)):
        super().__init__(master, fg_color="transparent")
        self.fig = Figure(figsize=figsize, facecolor=C["card"], layout="constrained")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        w = self.canvas.get_tk_widget(); w.configure(bg=C["card"], highlightthickness=0); w.pack(fill="both", expand=True)

    def draw(self): self.canvas.draw_idle()


class AssetList(ctk.CTkFrame):
    """Search box + class filter + asset table with live DEMO quotes."""
    CLS = {"Stocks": "Stock", "Crypto": "Crypto", "Index": "Index"}

    def __init__(self, master, on_pick, filters=("All", "Stocks", "Crypto", "Index"), watch=None, height=14):
        super().__init__(master, fg_color="transparent")
        from . import demo_data as dd
        self.dd, self.on_pick, self.watch = dd, on_pick, watch
        self.box = Entry(self, width=200, placeholder_text="Search symbol or name…"); self.box.pack(fill="x", pady=(0, 6))
        self.box.bind("<KeyRelease>", lambda e: self.refresh())
        self.seg = Seg(self, filters, lambda v: self.refresh()); self.seg.pack(fill="x", pady=(0, 6)); self.seg.set(filters[0])
        self.tab = Table(self, ("Symbol", "Last", "Chg %"), (90, 90, 70), height=height, on_select=lambda v: on_pick(v[0]))
        self.tab.pack(fill="both", expand=True); self.refresh()

    def refresh(self):
        f = self.seg.get(); rows, tags = [], []
        only = self.watch() if (f.startswith("★") and self.watch) else None
        for a in self.dd.search(self.box.get(), "All" if f.startswith("★") or f == "All" else self.CLS.get(f, f), only):
            q = self.dd.quote(a["sym"]); rows.append((a["sym"], compact(q["last"]), pct(q["pct"]))); tags.append(sgn_tag(q["pct"]))
        self.tab.set(rows, tags, iids=[r[0] for r in rows])

    def select(self, sym):
        self.tab.select(sym)


class Screen(ctk.CTkFrame):
    title = ""; subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent"); self.app = app

    def on_show(self, **kw): pass
