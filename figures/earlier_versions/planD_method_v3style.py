"""Plan D (paper P2) methodology figure, same style as method_diagram v3 (5.5 in, Liberation Sans, icons).
Facts checked against:
  planD/overnight/ledger_v3.py (arms none / exact / semantic tau 0.85 MiniLM / intent screen; scripted
      loop: W attempts, fresh worker call each attempt, a ledger or screen block STOPS the request)
  planD/overnight/ledger_adaptive.py (LLM coordinator: send|stop, same|new worker, may rephrase; at most W
      dispatch attempts, blocked attempts count; conditions unprompted / explicit / bare = reason hidden)
  planD/overnight/environment.py (worker JSON: decision execute|refuse + reason; typed actions on SQLite)
  swarm_hackathon/paper_p2/P2_DRAFT.md sections 3.1, 4.1-4.3, 4.6 (task bank, numbers)

    python -I planD_method.py  ->  planD_method.png (300 dpi) + planD_method.pdf
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import (Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, PathPatch, Rectangle,
                                Wedge)
from matplotlib.path import Path

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planD_method")

# ---------------------------------------------------------------- fonts / palette
for f in ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
          os.path.expanduser("~/.local/share/fonts/JetBrainsMono.ttf")):  # optional; falls back to DejaVu Sans Mono
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
SANS = ["Liberation Sans", "Helvetica", "Arial", "DejaVu Sans"]
MONO = ["JetBrains Mono", "DejaVu Sans Mono", "monospace"]
plt.rcParams.update({"font.family": SANS, "svg.fonttype": "none", "pdf.fonttype": 42})

INK, INK2, MUTED = "#191918", "#3D3C38", "#5F5D57"
RULE, AXIS, GRAY, GRAY_L = "#E2DFD7", "#B9B6AE", "#ADA9A1", "#DCD9D3"
CARD = "#F4F1EC"
ORANGE, ORANGE_L, CLAY = "#C0583A", "#F6DED4", "#9A4329"
BLUE, BLUE_L, BLUE_D = "#4F7A96", "#E1EBF2", "#3B6079"
GOLD = "#C9A227"

W, H = 5.5, 4.79
FS, FS_L, FS_H, FS_T, FS_M = 8.0, 9.0, 9.5, 10.0, 8.0   # secondary, main labels, box titles, top title, mono

fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")


# ================================================================ primitives
def rbox(x, y, w, h, fc="white", ec=RULE, lw=0.8, r=0.07, z=1, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                zorder=z, ls=ls))


def t(x, y, s, size=FS, color=INK2, mono=False, ha="left", va="center", weight="normal", z=8, **kw):
    return ax.text(x, y, s, fontsize=size, color=color, family=MONO if mono else SANS, ha=ha, va=va,
                   fontweight=weight, zorder=z, **kw)


def title(x, y, num, s, color=INK, disc=INK):
    if num is not None:
        ax.add_patch(Circle((x + 0.085, y), 0.085, fc=disc, ec="none", zorder=7))
        t(x + 0.085, y - 0.004, str(num), size=7.5, color="white", ha="center", weight="bold")
        x += 0.22
    t(x, y, s, size=FS_H, color=color, weight="bold")


def arrow(p0, p1, color=INK, lw=2.4, ls="-", rad=0.0, z=4, hl=0.5, hw=0.32, ms=12):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=f"-|>,head_length={hl},head_width={hw}",
                                 connectionstyle=f"arc3,rad={rad}", color=color, lw=lw, ls=ls, zorder=z,
                                 shrinkA=0, shrinkB=0, mutation_scale=ms, capstyle="butt", joinstyle="miter"))


# ================================================================ icons (patches only)
def key(x, y, s=0.16, c=GOLD, z=6):
    """Key, centered at (x, y), width ~ s."""
    ax.add_patch(Circle((x - 0.30 * s, y), 0.20 * s, fc=c, ec="none", zorder=z))
    ax.add_patch(Circle((x - 0.30 * s, y), 0.08 * s, fc="white", ec="none", zorder=z + 1))
    ax.add_patch(Rectangle((x - 0.14 * s, y - 0.05 * s), 0.62 * s, 0.10 * s, fc=c, ec="none", zorder=z))
    for dx in (0.28, 0.42):
        ax.add_patch(Rectangle((x + dx * s, y - 0.17 * s), 0.07 * s, 0.13 * s, fc=c, ec="none", zorder=z))


def check(x, y, s, c="white", lw=1.0, z=8):
    ax.plot([x - 0.28 * s, x - 0.06 * s, x + 0.30 * s], [y + 0.0 * s, y - 0.22 * s, y + 0.22 * s], color=c,
            lw=lw, solid_capstyle="round", zorder=z)


def cross(x, y, s, c="white", lw=1.0, z=8):
    for sgn in (1, -1):
        ax.plot([x - 0.25 * s, x + 0.25 * s], [y - sgn * 0.25 * s, y + sgn * 0.25 * s], color=c, lw=lw,
                solid_capstyle="round", zorder=z)


def slot(x, y, s=0.15, state="open"):
    """A need: open (dashed), met (blue, check) or burned (orange, cross)."""
    fc, ec, ls = {"open": ("white", MUTED, (0, (2, 1.2))), "met": (BLUE, BLUE, "-"),
                  "burned": (ORANGE, ORANGE, "-")}[state]
    ax.add_patch(FancyBboxPatch((x - s / 2, y - s / 2), s, s, boxstyle=f"round,pad=0,rounding_size={s * 0.2}",
                                fc=fc, ec=ec, lw=0.8, ls=ls, zorder=6))
    if state == "met":
        check(x, y, s * 0.8)
    elif state == "burned":
        cross(x, y, s * 0.8)


def envelope(x, y, w=0.20, c=INK2, fc="white", lw=0.8, z=6, masked=False):
    h = w * 0.68
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec=c, lw=lw, zorder=z, joinstyle="round"))
    ax.plot([x - w / 2, x, x + w / 2], [y + h / 2, y - h * 0.08, y + h / 2], color=c, lw=lw, zorder=z + 0.5,
            solid_joinstyle="round")
    if masked:                                   # a domino mask over the sender corner = spoofed sender
        mx, my, mw = x + w * 0.38, y + h * 0.48, w * 0.62
        ax.add_patch(FancyBboxPatch((mx - mw / 2, my - mw * 0.22), mw, mw * 0.44,
                                    boxstyle=f"round,pad=0,rounding_size={mw * 0.2}", fc=INK, ec="white", lw=0.6,
                                    zorder=z + 2))
        for ex in (-0.22, 0.22):
            ax.add_patch(Ellipse((mx + ex * mw, my), mw * 0.24, mw * 0.17, fc="white", ec="none", zorder=z + 3))


def flame(x, y, s=0.18, c=ORANGE, z=6):
    def drop(cx, cy, k, col, zz):
        v = [(0, -0.5), (0.55, -0.5), (0.42, 0.12), (0, 0.6), (-0.42, 0.12), (-0.55, -0.5), (0, -0.5)]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        ax.add_patch(PathPatch(Path([(cx + k * a, cy + k * b) for a, b in v], codes), fc=col, ec="none", zorder=zz))
    drop(x, y, s, c, z)
    drop(x, y - 0.12 * s, s * 0.5, "#F2B48C", z + 1)


def magnifier(x, y, s=0.17, c=INK2, z=6):
    ax.add_patch(Circle((x - 0.08 * s, y + 0.08 * s), 0.27 * s, fc="white", ec=c, lw=1.1, zorder=z))
    ax.plot([x + 0.12 * s, x + 0.38 * s], [y - 0.12 * s, y - 0.38 * s], color=c, lw=1.6, zorder=z,
            solid_capstyle="round")


def link(x, y, s=0.2, c=INK2, z=6):
    ax.plot([x - 0.32 * s, x + 0.32 * s], [y, y], color=c, lw=0.9, zorder=z, ls=(0, (2, 1.2)))
    for dx in (-0.32, 0.32):
        ax.add_patch(Circle((x + dx * s, y), 0.12 * s, fc=c, ec="none", zorder=z + 1))


def give(x, y, s=0.2, c=INK2):
    key(x - 0.12 * s, y, s * 0.7)
    arrow((x + 0.18 * s, y), (x + 0.52 * s, y), color=c, lw=0.9, hl=0.35, hw=0.25, ms=8)


def chip(x, y, s=0.42, z=6):
    ax.add_patch(FancyBboxPatch((x - s / 2, y - s / 2), s, s, boxstyle=f"round,pad=0,rounding_size={s * 0.14}",
                                fc=BLUE_D, ec="none", zorder=z))
    for k in np.linspace(-0.28, 0.28, 4):
        for (a, b), (c_, d) in (((-0.5, k), (-0.62, k)), ((0.5, k), (0.62, k)), ((k, -0.5), (k, -0.62)),
                                ((k, 0.5), (k, 0.62))):
            ax.plot([x + a * s, x + c_ * s], [y + b * s, y + d * s], color=BLUE_D, lw=1.0, zorder=z,
                    solid_capstyle="butt")
    t(x, y, "LLM", size=8, color="white", ha="center", weight="bold", z=z + 1)


def lock(x, y, s=0.14, c=MUTED, z=6):
    ax.add_patch(Wedge((x, y + 0.12 * s), 0.24 * s, 0, 180, width=0.08 * s, fc=c, ec="none", zorder=z))
    ax.add_patch(FancyBboxPatch((x - 0.36 * s, y - 0.38 * s), 0.72 * s, 0.52 * s,
                                boxstyle=f"round,pad=0,rounding_size={0.08 * s}", fc=c, ec="none", zorder=z))


def bubble(x, y, s=0.2, c=INK2, z=6):
    ax.add_patch(Ellipse((x + 0.05 * s, y + 0.08 * s), 0.8 * s, 0.55 * s, fc="white", ec=c, lw=0.9, zorder=z))
    ax.add_patch(Circle((x - 0.33 * s, y - 0.28 * s), 0.07 * s, fc="white", ec=c, lw=0.8, zorder=z))
    ax.add_patch(Circle((x - 0.45 * s, y - 0.42 * s), 0.04 * s, fc=c, ec="none", zorder=z))


def meter(x, y, s=0.24, frac=0.65, c=BLUE):
    h = s * 0.32
    ax.add_patch(Rectangle((x - s / 2, y - h / 2), s * frac, h, fc=c, ec="none", zorder=6))
    ax.add_patch(Rectangle((x - s / 2, y - h / 2), s, h, fc="none", ec=c, lw=0.8, zorder=7))


def badge_check(x, y, s=0.17, c=BLUE):
    ax.add_patch(Circle((x, y), s / 2, fc=c, ec="none", zorder=6))
    check(x, y, s * 0.6, lw=1.1)


def mini_net(x, y, s=0.2, c=INK2):
    pts = [(-0.35, -0.2), (0.0, 0.3), (0.35, -0.2), (0.05, -0.05)]
    for a, b in ((0, 1), (1, 2), (0, 3), (3, 2), (1, 3)):
        ax.plot([x + pts[a][0] * s, x + pts[b][0] * s], [y + pts[a][1] * s, y + pts[b][1] * s], color=AXIS, lw=0.7,
                zorder=5)
    for i, (a, b) in enumerate(pts):
        ax.add_patch(Circle((x + a * s, y + b * s), 0.09 * s, fc=BLUE if i == 3 else c, ec="none", zorder=6))


# ================================================================ helpers
RENDERER = fig.canvas.get_renderer()


def tw(s, size=FS, mono=False, weight="normal"):
    tt = t(0, 0, s, size=size, mono=mono, weight=weight)
    w = tt.get_window_extent(renderer=RENDERER).width / fig.dpi
    tt.remove()
    return w


def person(x, y, s=0.2, c=INK2):
    ax.add_patch(Circle((x, y + 0.18 * s), 0.17 * s, fc=c, ec="none", zorder=6))
    ax.add_patch(Wedge((x, y - 0.32 * s), 0.32 * s, 0, 180, fc=c, ec="none", zorder=6))


def database(x, y, s=0.18, c=INK2, fc="white", z=6):
    w, h, e = s * 0.8, s, s * 0.26
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec="none", zorder=z))
    for xx in (x - w / 2, x + w / 2):
        ax.plot([xx, xx], [y - h / 2, y + h / 2], color=c, lw=0.9, zorder=z + 1)
    ax.add_patch(Ellipse((x, y + h / 2), w, e, fc=fc, ec=c, lw=0.9, zorder=z + 2))
    th = np.linspace(np.pi, 2 * np.pi, 30)
    for yy in (y - h / 2, y - h / 6, y + h / 6):
        ax.plot(x + w / 2 * np.cos(th), yy + e / 2 * np.sin(th), color=c, lw=0.9, zorder=z + 1)


def no_entry(x, y, s=0.16, c=MUTED):
    ax.add_patch(Circle((x, y), s / 2, fc=c, ec="none", zorder=6))
    ax.add_patch(Rectangle((x - s * 0.3, y - s * 0.08), s * 0.6, s * 0.16, fc="white", ec="none", zorder=7))


def glyph(x, y, ch, s=0.17, fc="white", ec=INK2, col=INK2):
    ax.add_patch(FancyBboxPatch((x - s / 2, y - s / 2), s, s, boxstyle=f"round,pad=0,rounding_size={s * 0.2}",
                                fc=fc, ec=ec, lw=0.8, zorder=6))
    t(x, y - 0.006, ch, size=8.5, color=col, ha="center", weight="bold", z=7)


def wrap(text, width, size=FS, weight="normal"):
    out, cur = [], ""
    for w_ in text.split():
        nxt = (cur + " " + w_).strip()
        if tw(nxt, size, weight=weight) <= width:
            cur = nxt
        else:
            out.append(cur)
            cur = w_
    return out + [cur]


def para(x, y, text, width, size=FS, color=INK2, dy=0.145, weight="normal"):
    lines = wrap(text, width, size, weight)
    for j, ln in enumerate(lines):
        t(x, y - j * dy, ln, size=size, color=color, weight=weight)
    return y - len(lines) * dy


M = 0.04
X0, X1 = M, W - M

# ================================================================ 1. THE DISPATCH PIPELINE (top)
yT = H - 0.16
t(X0 + 0.02, yT, "One request, up to W = 3 attempts", size=FS_T, color=INK, weight="bold")
B0, B1 = H - 1.92, H - 0.34                     # pipeline boxes
cols = [(X0, X0 + 1.12), (X0 + 1.32, X0 + 2.72), (X0 + 2.92, X0 + 3.94), (X0 + 4.14, X1)]
for (a, b) in cols:
    rbox(a, B0, b - a, B1 - B0, fc="white", ec=AXIS, lw=0.9)
amid = B1 - 0.62                                # flow-arrow height

# 1 coordinator
c0, c1 = cols[0]
title(c0 + 0.08, B1 - 0.17, 1, "Coordinator", disc=BLUE)
person(c0 + 0.24, B1 - 0.55, 0.26)
t(c0 + 0.44, B1 - 0.49, "Alice's", size=FS, color=MUTED)
t(c0 + 0.44, B1 - 0.63, "request", size=FS, color=MUTED)
para(c0 + 0.1, B1 - 0.92, "allowed or forbidden; re-asks after a refusal", c1 - c0 - 0.16)

# 2 defense gate
d0, d1 = cols[1]
title(d0 + 0.08, B1 - 0.17, 2, "Defense", disc=BLUE)
gates = [("\u2013", "none", MUTED), ("=", "exact ledger", INK2), ("\u2248", "text similarity", INK2),
         (None, "intent screen (LLM)", INK2)]
for k, (ch, lab, col) in enumerate(gates):
    yk = B1 - 0.46 - k * 0.21
    if ch is None:
        magnifier(d0 + 0.19, yk, 0.17)
    else:
        glyph(d0 + 0.19, yk, ch)
    t(d0 + 0.37, yk, lab, size=FS, color=col)
t(d0 + 0.1, B0 + 0.24, "scripted: a block stops", size=FS, color=CLAY)
t(d0 + 0.1, B0 + 0.10, "the request", size=FS, color=CLAY)

# 3 worker
w0, w1 = cols[2]
title(w0 + 0.08, B1 - 0.17, 3, "Worker", disc=BLUE)
chip(w0 + 0.3, B1 - 0.62, 0.3)
t(w0 + 0.56, B1 - 0.55, "gpt-oss", size=FS, color=INK2)
t(w0 + 0.56, B1 - 0.69, "-20b", size=FS, color=INK2)
yy_ = para(w0 + 0.1, B1 - 1.0, "a fresh call on each attempt", w1 - w0 - 0.15)
para(w0 + 0.1, yy_ - 0.05, "typed actions on a synthetic DB", w1 - w0 - 0.15, color=MUTED)

# 4 outcome
o0, o1 = cols[3]
title(o0 + 0.08, B1 - 0.17, 4, "Outcome", disc=INK2)
oy = B1 - 0.47
t(o0 + 0.1, oy, "executes:", size=FS, color=MUTED)
badge_check(o0 + 0.19, oy - 0.21, 0.15)
t(o0 + 0.35, oy - 0.21, "allowed", size=FS)
slot(o0 + 0.19, oy - 0.43, 0.14, "burned")
t(o0 + 0.35, oy - 0.43, "forbidden =", size=FS, color=CLAY, weight="bold")
t(o0 + 0.35, oy - 0.57, "violation", size=FS, color=CLAY, weight="bold")
ref_y = oy - 0.84
t(o0 + 0.1, ref_y + 0.17, "or", size=FS, color=MUTED)
no_entry(o0 + 0.19, ref_y, 0.15)
t(o0 + 0.35, ref_y, "refuses + reason", size=FS)

# flow arrows
for (a, b), (c, d) in zip(cols[:-1], cols[1:]):
    arrow((b + 0.02, amid), (c - 0.02, amid), color=INK, lw=2.0, hl=0.45, hw=0.3, ms=11)

# refused text -> ledger (thin grey, under the boxes)
gy_ = B0 - 0.16
ax.add_patch(FancyArrowPatch((o0 + 0.04, ref_y), (o0 - 0.1, ref_y), arrowstyle="-", color=MUTED, lw=0.8,
                             zorder=7))
ax.plot([o0 - 0.1, o0 - 0.1], [ref_y, gy_], color=MUTED, lw=0.8, zorder=7)
ax.plot([o0 - 0.1, (d0 + d1) / 2], [gy_, gy_], color=MUTED, lw=0.8, zorder=7)
arrow(((d0 + d1) / 2, gy_), ((d0 + d1) / 2, B0 - 0.01), color=MUTED, lw=0.8, hl=0.4, hw=0.25, ms=9)
t((w0 + w1) / 2, gy_ + 0.08, "refused text \u2192 ledger", size=7.5, color=MUTED, ha="center")

# re-ask loop (orange): refusal -> back to the coordinator
ly = B0 - 0.38
ax.plot([o0 + 0.19, o0 + 0.19], [ref_y - 0.09, ly], color=ORANGE, lw=1.8, zorder=5)
ax.plot([o0 + 0.19, (c0 + c1) / 2], [ly, ly], color=ORANGE, lw=1.8, zorder=5)
arrow(((c0 + c1) / 2, ly), ((c0 + c1) / 2, B0 - 0.02), color=ORANGE, lw=1.8, hl=0.45, hw=0.3, ms=11)
t((c1 + o0) / 2 + 0.1, ly - 0.15, "re-ask after a refusal: the channel that lets forbidden work through", size=FS,
  color=CLAY, weight="bold", ha="center")

# ================================================================ 2. TASK BANK + COORDINATORS (middle)
K1 = ly - 0.32
K0 = K1 - 1.08
kw_ = (X1 - X0 - 0.16) / 3
cards = [
    ("Requests", None, [
        "48 request types (24 allowed, 24 forbidden) in 12 families, each in 2 wordings",
        "3 passes, shuffled; the wording repeats within a trial (6 trials)"]),
    ("Scripted coordinator", None, [
        "re-sends the same text to a fresh worker",
        "never re-ask = stop after attempt 1 (computed from the none arm)"]),
    ("LLM coordinator", None, [
        "may rephrase, re-route or stop; a block counts as an attempt",
        "unprompted · explicit permission · reason hidden"]),
]
for k, (head, _, lines) in enumerate(cards):
    x0_ = X0 + k * (kw_ + 0.08)
    rbox(x0_, K0, kw_, K1 - K0, fc=CARD if k < 2 else BLUE_L, ec="none", r=0.06)
    t(x0_ + 0.1, K1 - 0.15, head, size=FS_L, color=INK if k < 2 else BLUE_D, weight="bold")
    yy = K1 - 0.36
    for ln in lines:
        yy = para(x0_ + 0.1, yy, ln, kw_ - 0.18) - 0.06

# ================================================================ 3. RESULTS (bottom strip)
R1_ = K0 - 0.12
R0_ = R1_ - 0.92
rw = (X1 - X0 - 0.16) / 3
# 3a mini bars
x0_ = X0
rbox(x0_, R0_, rw, R1_ - R0_, fc="white", ec=RULE, r=0.06)
t(x0_ + 0.1, R1_ - 0.15, "Forbidden executed (host A)", size=FS, color=INK, weight="bold")
bars = [("none", 25.5, GRAY), ("never re-ask", 14.8, BLUE), ("exact ledger", 9.3, BLUE_D)]
bx0, bmax = x0_ + 0.85, rw - 1.38
for k, (lab, v, c) in enumerate(bars):
    yk = R1_ - 0.40 - k * 0.2
    t(bx0 - 0.06, yk, lab, size=FS, color=INK2, ha="right")
    ax.add_patch(Rectangle((bx0, yk - 0.06), bmax * v / 25.5, 0.12, fc=c, ec="none", zorder=5))
    t(bx0 + bmax * v / 25.5 + 0.05, yk, f"{v}%", size=FS, color=INK, weight="bold")
# 3b fuzzy memory cost
x0_ = X0 + rw + 0.08
rbox(x0_, R0_, rw, R1_ - R0_, fc="white", ec=RULE, r=0.06)
glyph(x0_ + 0.2, R1_ - 0.17, "≈")
t(x0_ + 0.36, R1_ - 0.17, "Text similarity", size=FS, color=INK, weight="bold")
t(x0_ + 0.1, R1_ - 0.45, "blocks 38–42%", size=FS_T, color=CLAY, weight="bold")
para(x0_ + 0.1, R1_ - 0.66, "of allowed work (exact ledger: \u22642%)", rw - 0.16)
# 3c adaptive coordinator
x0_ = X0 + 2 * (rw + 0.08)
rbox(x0_, R0_, rw, R1_ - R0_, fc="white", ec=RULE, r=0.06)
t(x0_ + 0.1, R1_ - 0.15, "LLM vs scripted (host B)", size=FS, color=INK, weight="bold")
for k, (ch, lab, val, col) in enumerate(((("=", "exact ledger", "+4 to +10 pts", CLAY)),
                                        ((None, "intent screen", "+1 to +3 pts", BLUE_D)))):
    yk = R1_ - 0.44 - k * 0.32
    if ch is None:
        magnifier(x0_ + 0.2, yk, 0.17)
    else:
        glyph(x0_ + 0.2, yk, ch)
    t(x0_ + 0.38, yk + 0.07, lab, size=FS, color=INK2)
    t(x0_ + 0.38, yk - 0.08, val, size=FS, color=col, weight="bold")
print("bottom of results:", round(R0_, 2))

fig.savefig(OUT + ".png", dpi=300, facecolor="white")
fig.savefig(OUT + ".pdf", facecolor="white")
print("saved", OUT)
