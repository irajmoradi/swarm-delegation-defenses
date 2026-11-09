"""Plan D (paper P2) method figure, NeurIPS style, round 3 (second reviewer critique: CIs, missing arms, two loop-backs, grayscale).
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
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import planD_data  # noqa: E402  (loads every number from the run files and asserts it against P2)

D = planD_data.load()
T = planD_data.tables(D)

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

W, H = 5.5, 5.15
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
txt((wk0 + wk1) / 2, ym + 0.12, "Worker", size=F2, color=BLUE_D, weight="bold", ha="center")
txt((wk0 + wk1) / 2, ym - 0.06, "openai/", size=7.2, color=INK2, ha="center")
txt((wk0 + wk1) / 2, ym - 0.18, "gpt-oss-20b", size=7.2, color=INK2, ha="center")
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

# block badge (pre-execution path, amber), hung from the block arrow
bb_y = dtop + 0.17
ax.plot([(co1 + df0) / 2, (co1 + df0) / 2], [ym + 0.12, bb_y - 0.1], color=AMBER, lw=0.7, zorder=4)
label_box(co0 + 0.1, bb_y, [("defense block", "ab"), (" (pre-execution): counts as an attempt; ends if scripted", "a")],
          AMBER_F, AMBER, size=7.2, r=0.1)

# refusal ledger below the defense box. READ: solid grey arrow up into the defense (pre-dispatch).
# WRITE: dashed grey arrow from the worker-refusal path into the cylinder's side (post-call). Separate paths.
cyl_x, cyl_y = df0 + 0.32, dbot - 0.4
cylinder(cyl_x, cyl_y, 0.22, 0.17)
txt(cyl_x - 0.17, cyl_y, "trial-wide\nrefusal ledger\n(all requests\nand passes)", size=7.0, color=INK2, ha="right",
    va="center").set_linespacing(1.05)
arrow((cyl_x, cyl_y + 0.125), (cyl_x, dbot - 0.01), color=MUTED, lw=0.9, hs=0.8)              # read
runs(cyl_x + 0.07, (cyl_y + 0.125 + dbot) / 2, [("read", "b"), (" by (ii), (iii) (pre-dispatch)", "")],
     size=7.2, color=MUTED)
ly = cyl_y - 0.36
rx = oc1 - 0.2
ax.plot([rx, rx], [rf_y - 0.25, ly], color=RED, lw=1.4, zorder=3)
ax.plot([rx, (co0 + co1) / 2], [ly, ly], color=RED, lw=1.4, zorder=3)
arrow(((co0 + co1) / 2, ly), ((co0 + co1) / 2, ym - bh - 0.01), color=RED, lw=1.4)
ax.plot([rx], [cyl_y], marker="o", ms=3.2, color=RED, zorder=6)
arrow((rx, cyl_y), (cyl_x + 0.13, cyl_y), color=LINE, lw=0.9, hs=0.8, ls=(0, (3, 2)))           # write
runs((cyl_x + rx) / 2 - 0.55, cyl_y - 0.11, [("write", "b"), (": record refused text (post-call)", "")], size=7.2,
     color=MUTED)
_parts = [("re-ask (up to ", "r"), ("W", "ir"), (" = 3 attempts)", "r")]
_lab = [("worker refusal", "rb"), (" (post-call)", "r")]
_w = sum(width(s_, F3, "bold" if "b" in f_ else "normal") for s_, f_ in _lab) + 0.28 + \
    sum(width(s_, F3, style="italic" if "i" in f_ else "normal") for s_, f_ in _parts)
_x = (co1 + rx) / 2 - _w / 2
_x = runs(_x, ly - 0.15, _lab)
arrow((_x + 0.06, ly - 0.15), (_x + 0.22, ly - 0.15), color=RED, lw=1.2, hs=0.9)
runs(_x + 0.28, ly - 0.15, _parts)

# ======================================================================= (b) coordinators and results
yB = ly - 0.45
ax.plot([M, W - M], [yB + 0.2, yB + 0.2], color="#E3E3E0", lw=0.7)
runs(M, yB, [("(b)", "b"), ("  Coordinator modes and results", "b")], size=F1, color=INK)

# bar styles (grayscale-safe: hatched white, then light / mid / dark blue)
SCRIPT_FC, SCRIPT_HATCH = "white", "////"
SER = [("scripted", SCRIPT_FC), ("LLM, unprompted", "#C9D9E6"), ("LLM, explicit", "#6F97B4"),
       ("LLM, reason hidden", "#24485F")]
plt.rcParams["hatch.color"] = "#7A7A76"
plt.rcParams["hatch.linewidth"] = 0.6


def swatch(x, y, k, s=0.13):
    """Legend swatch for series k, identical to its bar style."""
    ax.add_patch(Rectangle((x, y - s / 2), s, s, fc=SER[k][1], ec="#7A7A76" if k == 0 else "none", lw=0.6,
                           hatch=SCRIPT_HATCH if k == 0 else None, zorder=6))
    return x + s + 0.05


sx0 = M
y1 = yB - 0.33
x = swatch(sx0, y1, 0)
txt(x, y1, "Scripted", size=F2, color=INK, weight="bold")
y2 = y1 - 0.27
x = label_box(sx0, y2, [("p", "i")], GREY_F, GREY_E)
arrow((x + 0.03, y2), (x + 0.2, y2), lw=0.9, hs=0.8)
x = label_box(x + 0.23, y2, [("refuse", "")], GREY_F, GREY_E)
arrow((x + 0.03, y2), (x + 0.2, y2), lw=0.9, hs=0.8)
x = label_box(x + 0.23, y2, [("p", "i")], GREY_F, GREY_E)
runs(x + 0.07, y2, [("same text, fresh call", "m")], size=7.2)
runs(sx0, y2 - 0.22, [("up to ", ""), ("W", "i"), (" = 3 calls;  never re-ask: ", ""), ("W", "i"), (" = 1", "")],
     size=F4)

y3 = y2 - 0.5
txt(sx0, y3, "LLM coordinator (openai/gpt-oss-20b)", size=F2, color=BLUE_D, weight="bold")
y4 = y3 - 0.27
x = label_box(sx0, y4, [("p", "i"), (" + reason", "")], BLUE_F, BLUE)
arrow((x + 0.03, y4), (x + 0.2, y4), lw=0.9, hs=0.8, color=BLUE)
x = label_box(x + 0.23, y4, [("rephrase ", ""), ("p′", "i")], BLUE_F, BLUE)
x = label_box(x + 0.05, y4, [("re-route", "")], BLUE_F, BLUE)
x = label_box(x + 0.05, y4, [("stop", "")], BLUE_F, BLUE)
y5 = y4 - 0.27
x = sx0
for k, lab in ((1, "unprompted"), (2, "explicit"), (3, "reason hidden")):
    x = swatch(x, y5, k)
    x = runs(x, y5, [(lab, "")], size=F4) + 0.13

# --- grouped bars with Wilson 95% CIs (n = 216 forbidden requests per bar; values = P2 4.6 / adaptive csv)
cx0 = 2.92
foot_y = M + 0.1                                   # in-plot footnote
sb, st = M + 0.5, M + 1.04                          # utility strip
cb, ct = st + 0.1, yB - 0.12                         # violation bars
cax = fig.add_axes([cx0 / W, cb / H, (W - M - cx0) / W, (ct - cb) / H])
uax = fig.add_axes([cx0 / W, sb / H, (W - M - cx0) / W, (st - sb) / H], sharex=cax)
groups = ["none", "exact\nledger", "text\nsimilarity", "intent\nscreen"]
pct = T["pct"]
N = D["n_forb"][("none", "scripted")]


def wilson(p, n=N, z=1.959964):
    k = round(p / 100 * n) / n
    d = 1 + z * z / n
    c = (k + z * z / (2 * n)) / d
    h = z * np.sqrt(k * (1 - k) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


bw = 0.18
for k in range(4):
    for g in range(4):
        v = pct[k][g]
        xg = g + (k - 1.5) * bw
        if v is None:
            if g != 2:                                         # defined marker: condition not run
                cax.plot([xg], [1.0], marker="x", ms=4, mew=0.9, color=MUTED, zorder=4)
            continue
        cax.bar(xg, v, bw * 0.9, color=SER[k][1], edgecolor="#7A7A76" if k == 0 else "none", lw=0.6,
                hatch=SCRIPT_HATCH if k == 0 else None, zorder=3)
        lo, hi = wilson(v, n=T["n"][k][g])                     # scripted text similarity: 6 trials
        cax.plot([xg, xg], [lo, hi], color=INK, lw=0.7, zorder=4)
        for yy in (lo, hi):
            cax.plot([xg - 0.03, xg + 0.03], [yy, yy], color=INK, lw=0.7, zorder=4)
# text similarity: scripted bar from the 6-trial four-arm run (n = 432, P2 4.3); not run with the LLM coordinator
_b0 = 2 - 0.5 * bw - 0.48 * bw
cax.add_patch(Rectangle((_b0, 0.2), 2 + 1.5 * bw + 0.48 * bw - _b0, 30.5, fc="#F4F4F2", ec=GREY_E, lw=0.6,
                        ls=(0, (2, 2)), zorder=1))
cax.text(2 + 0.5 * bw, 16, "LLM\ncoord.\nnot\nrun", fontsize=6.6, color=MUTED, ha="center", va="center",
         linespacing=1.15, zorder=5)
cax.text(2 - 1.5 * bw, wilson(D["sem_viol"], n=D["sem_n"])[1] + 0.6, "\u2020", fontsize=7, color=INK2, ha="center", va="bottom")
cax.set_xticks(range(4))
cax.tick_params(axis="x", labelbottom=False)
cax.set_xlim(-0.48, 3.48)
cax.set_ylim(0, 33)
cax.set_yticks([0, 10, 20, 30])
cax.tick_params(axis="y", labelsize=7.2, colors=MUTED, length=2)
cax.tick_params(axis="x", length=0, pad=3)
cax.set_ylabel("forbidden executed (%)", fontsize=7.4, color=INK2, labelpad=3)
for sp in ("top", "right"):
    cax.spines[sp].set_visible(False)
for sp in ("left", "bottom"):
    cax.spines[sp].set_color(GREY_E)
    cax.spines[sp].set_linewidth(0.7)
cax.yaxis.grid(True, color="#ECECEA", lw=0.6, zorder=0)
cax.set_axisbelow(True)
cax.plot([0.775], [0.93], transform=cax.transAxes, marker="x", ms=4, mew=0.9, color=MUTED, clip_on=False)
cax.text(0.80, 0.93, "= not run", transform=cax.transAxes, fontsize=6.8, color=MUTED, va="center")

# --- utility strip: allowed requests blocked (%), same x positions and styles.
# Values: adaptive_primeintellect.csv `allowed_blocked` (n = 216 allowed per bar); scripted text similarity =
# host-B four-arm run, all 6 trials (analysis_split/split.csv false_block 0.4097 = P2 4.3's 41.0%).
blocked = T["blocked"]
for k in range(4):
    for g in range(4):
        v = blocked[k][g]
        xg = g + (k - 1.5) * bw
        if v is None:
            if g != 2:
                uax.plot([xg], [3.0], marker="x", ms=3.5, mew=0.8, color=MUTED, zorder=4)
            continue
        uax.bar(xg, max(v, 0.0), bw * 0.9, color=SER[k][1], edgecolor="#7A7A76" if k == 0 else "none", lw=0.6,
                hatch=SCRIPT_HATCH if k == 0 else None, zorder=3)
uax.add_patch(Rectangle((_b0, 0.3), 2 + 1.5 * bw + 0.48 * bw - _b0, 52, fc="#F4F4F2", ec=GREY_E, lw=0.6,
                        ls=(0, (2, 2)), zorder=1))
uax.text(2 - 1.5 * bw, 42.5, f"{D['sem_false_block']:.0f}%\u2020", fontsize=6.8, color=RED, ha="center", va="bottom", weight="bold")
uax.text(-0.44, 49, "allowed blocked (%)", fontsize=7.2, color=INK2, ha="left", va="center")
uax.text(-0.44, 31, f"all other bars \u2264 {planD_data.max_other_blocked(D):.1f}%", fontsize=6.8, color=MUTED, ha="left", va="center")
uax.set_ylim(0, 56)
uax.set_yticks([0, 40])
uax.tick_params(axis="y", labelsize=7.0, colors=MUTED, length=2)
uax.set_xticks(range(4))
uax.set_xticklabels(groups, fontsize=7.4, color=INK2, linespacing=1.0)
uax.tick_params(axis="x", length=0, pad=3)
for sp in ("top", "right"):
    uax.spines[sp].set_visible(False)
for sp in ("left", "bottom"):
    uax.spines[sp].set_color(GREY_E)
    uax.spines[sp].set_linewidth(0.7)
uax.set_axisbelow(True)
# in-plot footnote
txt(cx0 - 0.42, foot_y, "\u2020 6 trials (n = 432); other bars 3 trials (n = 216)", size=7.0, color=MUTED)

fig.savefig(OUT + ".png", dpi=300, facecolor="white")
fig.savefig(OUT + ".pdf", facecolor="white")
with open(OUT + "_caption.txt", "w") as _f:            # caption rendered from the same loaded values
    _f.write(planD_data.caption_neurips(D))
print("saved", OUT, "| panel b title y", round(yB, 2))
