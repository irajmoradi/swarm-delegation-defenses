"""Plan D (paper P2) method figure, NeurIPS style, round 2 (reviewer critique applied).
Flat vector schematic: thin-outlined light boxes; blue = coordinator / worker / pass; red = forbidden path
(re-ask loop, violation); amber = block; greys elsewhere. 5.5 in wide; vector PDF + 300-dpi PNG.
Earlier versions: planD_method_v1prof.* (first professional), planD_method_v3style.* (icon style).

Facts checked against:
  planD/overnight/ledger_v3.py   defenses none / exact / semantic (MiniLM cosine > tau = 0.85) /
      intent screen; scripted loop: up to W attempts, fresh worker call each attempt, a block ENDS the request
  planD/overnight/ledger_adaptive.py         LLM coordinator: send|stop, same|new worker, may rephrase; at most
      W dispatch attempts, blocked attempts count; conditions unprompted / explicit / bare (= reason hidden)
  swarm_hackathon/paper_p2/P2_DRAFT.md 3.1 (never-re-ask rule = cut the none arm after attempt 1), 4.6
  swarm_hackathon/paper_p2/figs/adaptive_primeintellect.csv   bar values (column `violation`)

    python -I planD_method.py  ->  planD_method.png (300 dpi) + planD_method.pdf
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planD_method")
for f in ("Regular", "Bold", "Italic"):
    p = f"/usr/share/fonts/truetype/liberation/LiberationSans-{f}.ttf"
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams.update({"font.family": ["Liberation Sans", "Helvetica", "Arial", "DejaVu Sans"],
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

INK, INK2, MUTED, LINE = "#1F1F1F", "#3A3A3A", "#6B6B6B", "#9C9C9C"
BLUE, BLUE_F, BLUE_D = "#3F6E8C", "#EAF1F6", "#2E5670"
RED, RED_F = "#B5523A", "#F7E6E0"
AMBER, AMBER_F = "#B7791F", "#FBF0DC"
GREY_F, GREY_E = "#F5F5F3", "#B8B8B4"
SHADES = ["#A9C3D6", "#6F97B4", "#2E5670"]        # LLM coordinator: unprompted, explicit, reason hidden

W, H = 5.5, 4.45
F1, F2, F3, F4 = 9.5, 8.6, 8.0, 7.6
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")
REN = fig.canvas.get_renderer()


def box(x0, y0, x1, y1, fc=GREY_F, ec=GREY_E, lw=0.8, r=0.05, z=1, ls="-"):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


def txt(x, y, s, size=F3, color=INK2, ha="left", va="center", weight="normal", style="normal", z=6):
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, fontstyle=style,
                   zorder=z)


def width(s, size=F3, weight="normal", style="normal"):
    t = txt(0, 0, s, size=size, weight=weight, style=style)
    w = t.get_window_extent(renderer=REN).width / fig.dpi
    t.remove()
    return w


def runs(x, y, parts, size=F3, color=INK2, ha="left", z=6):
    """parts = [(text, flags)]: 'i' italic (variables), 'b' bold, 'r' red, 'a' amber, 'm' muted, 'u' blue."""
    def kw(f):
        c = RED if "r" in f else AMBER if "a" in f else MUTED if "m" in f else BLUE_D if "u" in f else color
        return dict(size=size, color=c, weight="bold" if "b" in f else "normal",
                    style="italic" if "i" in f else "normal")
    total = sum(width(s, size, kw(f)["weight"], kw(f)["style"]) for s, f in parts)
    if ha == "center":
        x -= total / 2
    for s, f in parts:
        k = kw(f)
        txt(x, y, s, z=z, **k)
        x += width(s, size, k["weight"], k["style"])
    return x


def arrow(p0, p1, color=INK2, lw=1.1, ls="-", z=4, hs=1.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=f"-|>,head_length={0.32 * hs},head_width={0.18 * hs}",
                                 color=color, lw=lw, ls=ls, zorder=z, mutation_scale=10, shrinkA=0, shrinkB=0))


def label_box(x, y, parts, fc, ec, size=F4, r=0.04, h=0.2, padx=0.07):
    """A small rounded label (mixed runs inside); returns its right edge."""
    w = sum(width(s, size, "bold" if "b" in f else "normal", "italic" if "i" in f else "normal")
            for s, f in parts) + 2 * padx
    ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec,
                                lw=0.7, zorder=5))
    runs(x + padx, y, parts, size=size)
    return x + w


def cylinder(x, y, w=0.2, h=0.16, ec=MUTED):
    e = w * 0.32
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=6))
    for xx in (x - w / 2, x + w / 2):
        ax.plot([xx, xx], [y - h / 2, y + h / 2], color=ec, lw=0.8, zorder=7)
    ax.add_patch(Ellipse((x, y + h / 2), w, e, fc="white", ec=ec, lw=0.8, zorder=8))
    th = np.linspace(np.pi, 2 * np.pi, 30)
    ax.plot(x + w / 2 * np.cos(th), y - h / 2 + e / 2 * np.sin(th), color=ec, lw=0.8, zorder=7)


M = 0.05
# ======================================================================= (a) delegation loop
yA = H - 0.17
runs(M, yA, [("(a)", "b"), ("  Delegation loop for one request", "b")], size=F1, color=INK)
ym = H - 1.0
bh = 0.26

rq0, rq1 = M, M + 0.6
box(rq0, ym - bh, rq1, ym + bh)
txt((rq0 + rq1) / 2, ym + 0.1, "Request", size=F3, color=INK, weight="bold", ha="center")
txt((rq0 + rq1) / 2, ym - 0.06, "allowed or", size=7.2, color=MUTED, ha="center")
txt((rq0 + rq1) / 2, ym - 0.18, "forbidden", size=7.2, color=MUTED, ha="center")

co0, co1 = rq1 + 0.16, rq1 + 0.16 + 0.86
box(co0, ym - bh, co1, ym + bh, fc=BLUE_F, ec=BLUE)
txt((co0 + co1) / 2, ym + 0.08, "Coordinator", size=F2, color=BLUE_D, weight="bold", ha="center")
txt((co0 + co1) / 2, ym - 0.12, "scripted or LLM", size=F3, color=INK2, ha="center")
arrow((rq1 + 0.02, ym), (co0 - 0.02, ym))

# defense stack (alternative filters, one per run)
df0, df1 = co1 + 0.36, co1 + 0.36 + 1.5
filters = [("(i)", [("none", "")]), ("(ii)", [("exact ledger", "")]),
           ("(iii)", [("text similarity", ""), (" (cos > ", "m"), ("τ", "im"), (")", "m")]),
           ("(iv)", [("intent screen (LLM)", "")])]
fh = 0.16
dtop = ym + 0.42
dbot = dtop - 0.29 - len(filters) * fh - 0.04
box(df0, dbot, df1, dtop, fc="white", ec=GREY_E)
txt(df0 + 0.09, dtop - 0.14, "Defense", size=F2, color=INK, weight="bold")
txt(df1 - 0.09, dtop - 0.14, "one per run", size=7.2, color=MUTED, ha="right")
for k, (lab, parts) in enumerate(filters):
    yk = dtop - 0.34 - k * fh
    txt(df0 + 0.09, yk, lab, size=F3, color=MUTED)
    runs(df0 + 0.38, yk, parts)
arrow((co1 + 0.02, ym - 0.06), (df0 - 0.02, ym - 0.06), color=BLUE, lw=1.3)          # dispatch
arrow((df0 - 0.02, ym + 0.12), (co1 + 0.02, ym + 0.12), color=AMBER, lw=1.3)        # block

wk0, wk1 = df1 + 0.34, df1 + 0.34 + 0.74
box(wk0, ym - bh, wk1, ym + bh, fc=BLUE_F, ec=BLUE)
txt((wk0 + wk1) / 2, ym + 0.08, "Worker", size=F2, color=BLUE_D, weight="bold", ha="center")
txt((wk0 + wk1) / 2, ym - 0.12, "gpt-oss-20b", size=7.6, color=INK2, ha="center")
arrow((df1 + 0.02, ym), (wk0 - 0.02, ym), color=BLUE, lw=1.3)                        # pass
txt((df1 + wk0) / 2, ym + 0.11, "pass", size=7.4, color=BLUE_D, ha="center", weight="bold")

oc0, oc1 = wk1 + 0.16, W - M
ex_y, rf_y = ym + 0.36, ym - 0.36
box(oc0, ex_y - 0.25, oc1, ex_y + 0.25)
txt(oc0 + 0.07, ex_y + 0.11, "Execute", size=F3, color=INK, weight="bold")
txt(oc0 + 0.07, ex_y - 0.05, "forbidden:", size=7.2, color=RED)
txt(oc0 + 0.07, ex_y - 0.17, "violation", size=7.2, color=RED, weight="bold")
box(oc0, rf_y - 0.25, oc1, rf_y + 0.25)
txt(oc0 + 0.07, rf_y + 0.11, "Refuse", size=F3, color=INK, weight="bold")
txt(oc0 + 0.07, rf_y - 0.05, "with a", size=7.2, color=MUTED)
txt(oc0 + 0.07, rf_y - 0.17, "reason", size=7.2, color=MUTED)
arrow((wk1 + 0.02, ym + 0.06), (oc0 - 0.02, ex_y - 0.04))
arrow((wk1 + 0.02, ym - 0.06), (oc0 - 0.02, rf_y + 0.04))

# block badge, hung from the block arrow
bb_y = dtop + 0.17
ax.plot([(co1 + df0) / 2, (co1 + df0) / 2], [ym + 0.12, bb_y - 0.1], color=AMBER, lw=0.7, zorder=4)
label_box(co0 + 0.1, bb_y, [("block", "ab"), (" (counts as attempt; ends if scripted)", "a")], AMBER_F, AMBER,
          size=7.2, r=0.1)

# refusal ledger attached to the bottom edge of the defense box; read by (ii) and (iii)
cyl_x, cyl_y = df0 + 0.3, dbot - 0.12
cylinder(cyl_x, cyl_y, 0.22, 0.17)
runs(cyl_x + 0.17, cyl_y - 0.02, [("refusal ledger", ""), ("  read by (ii), (iii)", "m")], size=F4)
# record refused text: dashed grey from Refuse into the ledger
ry = cyl_y - 0.26
dash = (0, (3, 2))
ax.plot([oc0, oc0 - 0.1], [rf_y - 0.13, rf_y - 0.13], color=LINE, lw=0.9, ls=dash, zorder=3)
ax.plot([oc0 - 0.1, oc0 - 0.1], [rf_y - 0.13, ry], color=LINE, lw=0.9, ls=dash, zorder=3)
ax.plot([oc0 - 0.1, cyl_x], [ry, ry], color=LINE, lw=0.9, ls=dash, zorder=3)
arrow((cyl_x, ry), (cyl_x, cyl_y - 0.11), color=LINE, lw=0.9, hs=0.8)
txt((cyl_x + oc0 - 0.1) / 2 + 0.25, ry - 0.09, "record refused text", size=7.2, color=MUTED, ha="center")

# re-ask loop (red)
ly = ry - 0.32
ax.plot([oc1 - 0.2, oc1 - 0.2], [rf_y - 0.25, ly], color=RED, lw=1.4, zorder=3)
ax.plot([oc1 - 0.2, (co0 + co1) / 2], [ly, ly], color=RED, lw=1.4, zorder=3)
arrow(((co0 + co1) / 2, ly), ((co0 + co1) / 2, ym - bh - 0.01), color=RED, lw=1.4)
_parts = [("re-ask (up to ", "r"), ("W", "ir"), (" = 3 attempts)", "r")]
_w = width("refuse", F3) + 0.26 + sum(width(s_, F3, style="italic" if "i" in f_ else "normal") for s_, f_ in _parts)
_x = (co1 + oc1) / 2 - _w / 2
_x = runs(_x, ly - 0.15, [("refuse", "r")])
arrow((_x + 0.06, ly - 0.15), (_x + 0.22, ly - 0.15), color=RED, lw=1.2, hs=0.9)
runs(_x + 0.28, ly - 0.15, _parts)

# ======================================================================= (b) coordinators and results
yB = ly - 0.42
ax.plot([M, W - M], [yB + 0.2, yB + 0.2], color="#E3E3E0", lw=0.7)
runs(M, yB, [("(b)", "b"), ("  Coordinator modes and results", "b")], size=F1, color=INK)
sx0, sx1 = M, M + 2.4
y1 = yB - 0.33
txt(sx0, y1, "Scripted", size=F2, color=INK, weight="bold")
y2 = y1 - 0.26
x = label_box(sx0, y2, [("p", "i")], GREY_F, GREY_E)
arrow((x + 0.03, y2), (x + 0.2, y2), lw=0.9, hs=0.8)
x = label_box(x + 0.23, y2, [("refuse", "")], GREY_F, GREY_E)
arrow((x + 0.03, y2), (x + 0.2, y2), lw=0.9, hs=0.8)
x = label_box(x + 0.23, y2, [("p", "i")], GREY_F, GREY_E)
runs(x + 0.07, y2, [("same text, fresh call", "m")], size=7.2)
runs(sx0, y2 - 0.22, [("up to ", ""), ("W", "i"), (" = 3 calls;  never re-ask: ", ""), ("W", "i"), (" = 1", "")],
     size=F4)

y3 = y2 - 0.52
txt(sx0, y3, "LLM coordinator", size=F2, color=BLUE_D, weight="bold")
y4 = y3 - 0.26
x = label_box(sx0, y4, [("p", "i"), (" + reason", "")], BLUE_F, BLUE)
arrow((x + 0.03, y4), (x + 0.2, y4), lw=0.9, hs=0.8, color=BLUE)
x = label_box(x + 0.23, y4, [("rephrase ", ""), ("p′", "i")], BLUE_F, BLUE)
x = label_box(x + 0.05, y4, [("re-route", "")], BLUE_F, BLUE)
x = label_box(x + 0.05, y4, [("stop", "")], BLUE_F, BLUE)
y5 = y4 - 0.26
x = sx0
for k, lab in enumerate(["unprompted", "explicit", "reason hidden"]):
    x = label_box(x, y5, [(lab, "")], "white", SHADES[k], r=0.085, h=0.17) + 0.06

# --- grouped bars (right); values from adaptive_primeintellect.csv (`violation` x 100)
cx0 = sx1 + 0.45
cb, ct = M + 0.3, yB - 0.36
cax = fig.add_axes([cx0 / W, cb / H, (W - M - cx0) / W, (ct - cb) / H])
defs = ["none", "exact\nledger", "intent\nscreen"]
vals = {"scripted": [25.46, 10.19, 7.41], "unprompted": [22.69, 13.89, 10.19], "explicit": [18.06, 19.44, 8.80],
        "reason hidden": [23.61, 19.91, np.nan]}
series = [("scripted", "#BDBDB8"), ("unprompted", SHADES[0]), ("explicit", SHADES[1]), ("reason hidden", SHADES[2])]
bw = 0.19
xs = np.arange(3)
for j, (name, col) in enumerate(series):
    off = (j - 1.5) * bw
    cax.bar(xs + off, np.nan_to_num(np.array(vals[name])), bw * 0.9, color=col, edgecolor="none", zorder=3)
cax.text(2 + 1.5 * bw, 0.8, "n/a", fontsize=6.4, color=MUTED, ha="center", va="bottom", rotation=90)
cax.set_xticks(xs)
cax.set_xticklabels(defs, fontsize=F4, color=INK2, linespacing=1.0)
cax.set_xlim(-0.5, 2.55)
cax.set_ylim(0, 32)
cax.set_yticks([0, 10, 20, 30])
cax.tick_params(axis="y", labelsize=7.2, colors=MUTED, length=2)
cax.tick_params(axis="x", length=0, pad=3)
cax.set_ylabel("forbidden requests executed (%)", fontsize=7.4, color=INK2, labelpad=3)
for sp in ("top", "right"):
    cax.spines[sp].set_visible(False)
for sp in ("left", "bottom"):
    cax.spines[sp].set_color(GREY_E)
    cax.spines[sp].set_linewidth(0.7)
cax.yaxis.grid(True, color="#ECECEA", lw=0.6, zorder=0)
cax.set_axisbelow(True)
handles = [Rectangle((0, 0), 1, 1, color=c) for _, c in series]
leg = cax.legend(handles, ["scripted", "LLM, unprompted", "LLM, explicit", "LLM, reason hidden"], fontsize=6.8,
                 ncol=2, frameon=False, loc="lower left", bbox_to_anchor=(-0.02, 1.0), handlelength=0.9,
                 handletextpad=0.35, columnspacing=0.8, labelspacing=0.25, borderaxespad=0.1)
for t_ in leg.get_texts():
    t_.set_color(INK2)
cax.annotate("LLM rephrases past\nthe exact ledger:\n10% to 14–20%", xy=(1 + 1.5 * bw, 20.4),
             xytext=(1.36, 27.2), fontsize=6.8, color=RED, ha="left", va="center", zorder=6,
             arrowprops=dict(arrowstyle="-", color=RED, lw=0.7, shrinkA=1, shrinkB=1))

fig.savefig(OUT + ".png", dpi=300, facecolor="white")
fig.savefig(OUT + ".pdf", facecolor="white")
print("saved", OUT, "| panel b title y", round(yB, 2))
