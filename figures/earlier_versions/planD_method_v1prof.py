"""Plan D (paper P2) method figure, NeurIPS style: flat vector schematic, thin outlines, light fills, a blue for
coordinator/worker, one warm accent for the forbidden path (re-ask leak, violation), greys elsewhere.
5.5 in wide; vector PDF + 300-dpi PNG. (The earlier icon-style version is planD_method_v3style.*.)

Facts checked against:
  planD/overnight/ledger_v3.py   arms none / exact / semantic (MiniLM cosine > tau = 0.85) / intent
      screen (one gpt-oss-20b call sees policy + request; fails open); scripted loop: up to W attempts, a fresh
      worker call each attempt, a ledger or screen block ENDS the request (lines 178-183)
  planD/overnight/ledger_adaptive.py         LLM coordinator: send|stop, same|new worker, may rephrase; at most
      W dispatch attempts, blocked attempts count; conditions unprompted / explicit / bare (= reason hidden)
  planD/overnight/environment.py             worker JSON decision execute|refuse + reason; typed actions
  swarm_hackathon/paper_p2/P2_DRAFT.md       3.1 (task bank, never-re-ask rule), 4.1-4.3, 4.6 (table values)

    python -I planD_method.py  ->  planD_method.png (300 dpi) + planD_method.pdf
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "planD_method")
for f in ("Regular", "Bold", "Italic"):
    p = f"/usr/share/fonts/truetype/liberation/LiberationSans-{f}.ttf"
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams.update({"font.family": ["Liberation Sans", "Helvetica", "Arial", "DejaVu Sans"],
                     "pdf.fonttype": 42, "svg.fonttype": "none"})

# palette: blue (agents), warm accent (forbidden path), greys
INK, INK2, MUTED, LINE = "#1F1F1F", "#3A3A3A", "#6B6B6B", "#9C9C9C"
BLUE, BLUE_F, BLUE_D = "#3F6E8C", "#EAF1F6", "#2E5670"
WARM, WARM_F = "#B5523A", "#F7E6E0"
GREY_F, GREY_E = "#F5F5F3", "#B8B8B4"

W, H = 5.5, 4.2
F1, F2, F3 = 9.5, 8.6, 8.0          # panel titles, box titles, body
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.set_aspect("equal")
ax.axis("off")
REN = fig.canvas.get_renderer()


def box(x0, y0, x1, y1, fc=GREY_F, ec=GREY_E, lw=0.8, r=0.05, z=1):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z))


def txt(x, y, s, size=F3, color=INK2, ha="left", va="center", weight="normal", style="normal", z=5):
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, fontstyle=style,
                   zorder=z)


def width(s, size=F3, weight="normal", style="normal"):
    t = txt(0, 0, s, size=size, weight=weight, style=style)
    w = t.get_window_extent(renderer=REN).width / fig.dpi
    t.remove()
    return w


def runs(x, y, parts, size=F3, color=INK2, ha="left"):
    """Mixed runs: parts = [(text, flags)], flags: 'i' italic (variables), 'b' bold, 'w' warm, 'm' muted."""
    total = sum(width(s, size, "bold" if "b" in f else "normal", "italic" if "i" in f else "normal")
                for s, f in parts)
    if ha == "center":
        x -= total / 2
    for s, f in parts:
        kw = dict(size=size, color=WARM if "w" in f else MUTED if "m" in f else color,
                  weight="bold" if "b" in f else "normal", style="italic" if "i" in f else "normal")
        txt(x, y, s, **kw)
        x += width(s, size, kw["weight"], kw["style"])
    return x


def arrow(p0, p1, color=INK2, lw=1.1, rad=0.0, ls="-", z=4, hs=1.0):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=f"-|>,head_length={0.32 * hs},head_width={0.18 * hs}",
                                 connectionstyle=f"arc3,rad={rad}", color=color, lw=lw, ls=ls, zorder=z,
                                 mutation_scale=10, shrinkA=0, shrinkB=0))


def doc_glyph(x, y, s=0.16, ec=MUTED):
    w, h, c = s * 0.78, s, s * 0.25
    ax.add_patch(Polygon([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2 - c),
                          (x + w / 2 - c, y + h / 2), (x - w / 2, y + h / 2)], closed=True, fc="white", ec=ec,
                         lw=0.7, zorder=6))
    for k in range(3):
        yy = y + h * 0.18 - k * h * 0.22
        ax.plot([x - w * 0.3, x + w * 0.3], [yy, yy], color=ec, lw=0.5, zorder=7)


def db_glyph(x, y, s=0.16, ec=MUTED):
    w, h, e = s * 0.85, s, s * 0.28
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="white", ec="none", zorder=6))
    for xx in (x - w / 2, x + w / 2):
        ax.plot([xx, xx], [y - h / 2, y + h / 2], color=ec, lw=0.7, zorder=7)
    ax.add_patch(Ellipse((x, y + h / 2), w, e, fc="white", ec=ec, lw=0.7, zorder=8))
    import numpy as np
    th = np.linspace(np.pi, 2 * np.pi, 30)
    ax.plot(x + w / 2 * np.cos(th), y - h / 2 + e / 2 * np.sin(th), color=ec, lw=0.7, zorder=7)


M = 0.05
# ============================================================== (a) the delegation loop
yA = H - 0.17
runs(M, yA, [("(a)", "b"), ("  Delegation loop for one request", "b")], size=F1, color=INK)
ym = H - 1.12                                    # main row centre
bh = 0.27                                        # half box height

# request
rq0, rq1 = M, M + 0.66
box(rq0, ym - bh, rq1, ym + bh)
txt((rq0 + rq1) / 2, ym + 0.1, "Request", size=F3, color=INK, weight="bold", ha="center")
txt((rq0 + rq1) / 2, ym - 0.06, "allowed or", size=7.2, color=MUTED, ha="center")
txt((rq0 + rq1) / 2, ym - 0.18, "forbidden", size=7.2, color=MUTED, ha="center")

# coordinator
co0, co1 = rq1 + 0.18, rq1 + 0.18 + 0.86
box(co0, ym - bh, co1, ym + bh, fc=BLUE_F, ec=BLUE)
txt((co0 + co1) / 2, ym + 0.08, "Coordinator", size=F2, color=BLUE_D, weight="bold", ha="center")
txt((co0 + co1) / 2, ym - 0.12, "scripted or LLM", size=F3, color=INK2, ha="center")
arrow((rq1 + 0.02, ym), (co0 - 0.02, ym))

# defense stack, sitting on the dispatch arrow
df0, df1 = co1 + 0.24, co1 + 0.24 + 1.5
filters = [("(i)", "none", ""), ("(ii)", "never re-ask", " (W = 1)"), ("(iii)", "exact ledger", ""),
           ("(iv)", "text similarity", " (cos > τ)"), ("(v)", "intent screen (LLM)", "")]
fh = 0.155
dtop = ym + 0.5
dbot = dtop - 0.27 - len(filters) * fh - 0.06
box(df0, dbot, df1, dtop, fc="white", ec=GREY_E)
txt(df0 + 0.09, dtop - 0.14, "Defense on dispatch", size=F2, color=INK, weight="bold")
for k, (lab, name, extra) in enumerate(filters):
    yk = dtop - 0.34 - k * fh
    txt(df0 + 0.09, yk, lab, size=F3, color=MUTED)
    x = runs(df0 + 0.36, yk, [(name, "")])
    if extra == " (W = 1)":
        runs(x, yk, [(" (", "m"), ("W", "im"), (" = 1)", "m")])
    elif extra:
        runs(x, yk, [(" (cos > ", "m"), ("τ", "im"), (")", "m")])
arrow((co1 + 0.02, ym), (df0 - 0.02, ym), color=BLUE, lw=1.3)

# worker
wk0, wk1 = df1 + 0.26, df1 + 0.26 + 0.78
box(wk0, ym - bh, wk1, ym + bh, fc=BLUE_F, ec=BLUE)
txt((wk0 + wk1) / 2, ym + 0.08, "Worker", size=F2, color=BLUE_D, weight="bold", ha="center")
txt((wk0 + wk1) / 2, ym - 0.12, "gpt-oss-20b", size=7.6, color=INK2, ha="center")
arrow((df1 + 0.02, ym), (wk0 - 0.02, ym), color=BLUE, lw=1.3)

# outcomes (right column)
oc0, oc1 = wk1 + 0.2, W - M
ex_y = ym + 0.36
rf_y = ym - 0.36
box(oc0, ex_y - 0.25, oc1, ex_y + 0.25)
txt(oc0 + 0.07, ex_y + 0.11, "Execute", size=F3, color=INK, weight="bold")
txt(oc0 + 0.07, ex_y - 0.05, "forbidden ⇒", size=7.2, color=WARM)
txt(oc0 + 0.07, ex_y - 0.17, "violation", size=7.2, color=WARM, weight="bold")
box(oc0, rf_y - 0.25, oc1, rf_y + 0.25)
txt(oc0 + 0.07, rf_y + 0.11, "Refuse", size=F3, color=INK, weight="bold")
txt(oc0 + 0.07, rf_y - 0.05, "with a", size=7.2, color=MUTED)
txt(oc0 + 0.07, rf_y - 0.17, "reason", size=7.2, color=MUTED)
arrow((wk1 + 0.02, ym + 0.06), (oc0 - 0.02, ex_y - 0.04), rad=0.0)
arrow((wk1 + 0.02, ym - 0.06), (oc0 - 0.02, rf_y + 0.04), rad=0.0)

# refusal -> ledger (record) ; ledger feeds (c), (d)
lg_x, lg_y = (df0 + df1) / 2 + 0.1, dbot - 0.28
lg_end = lg_x - 0.29 + width("refusal ledger (iii, iv)") + 0.07
db_glyph(lg_x - 0.42, lg_y, 0.17)
txt(lg_x - 0.29, lg_y, "refusal ledger (iii, iv)", size=F3, color=INK2)
ax.plot([oc0, oc0 - 0.12], [rf_y - 0.12, rf_y - 0.12], color=LINE, lw=0.8, zorder=3)
ax.plot([oc0 - 0.12, oc0 - 0.12], [rf_y - 0.12, lg_y], color=LINE, lw=0.8, zorder=3)
arrow((oc0 - 0.12, lg_y), (lg_end, lg_y), color=LINE, lw=0.8, hs=0.8)
txt((lg_end + oc0 - 0.12) / 2, lg_y + 0.09, "record text", size=7.2, color=MUTED, ha="center")
arrow((lg_x - 0.42, lg_y + 0.1), (lg_x - 0.42, dbot - 0.01), color=LINE, lw=0.8, hs=0.8)

# block -> back to the coordinator (above)
by = dtop + 0.14
ax.plot([df0 + 0.3, df0 + 0.3], [dtop, by], color=INK2, lw=0.9, zorder=3)
ax.plot([df0 + 0.3, (co0 + co1) / 2], [by, by], color=INK2, lw=0.9, zorder=3)
arrow(((co0 + co1) / 2, by), ((co0 + co1) / 2, ym + bh + 0.01), color=INK2, lw=0.9, hs=0.9)
txt((co0 + co1) / 2 + 0.08, by + 0.1, "block: scripted, the request ends; LLM, it counts as an attempt", size=7.4,
    color=INK2)

# re-ask loop (warm): refusal -> coordinator
ly = lg_y - 0.26
ax.plot([oc1 - 0.2, oc1 - 0.2], [rf_y - 0.25, ly], color=WARM, lw=1.4, zorder=3)
ax.plot([oc1 - 0.2, (co0 + co1) / 2], [ly, ly], color=WARM, lw=1.4, zorder=3)
arrow(((co0 + co1) / 2, ly), ((co0 + co1) / 2, ym - bh - 0.01), color=WARM, lw=1.4)
runs((co1 + oc1) / 2 - 0.1, ly - 0.14, [("refuse → re-ask, up to ", "w"), ("W", "iw"), (" = 3 attempts", "w")],
     size=F3, ha="center")

# ============================================================== (b) the two coordinators
yB = ly - 0.45
ax.plot([M, W - M], [yB + 0.22, yB + 0.22], color="#E3E3E0", lw=0.7)
runs(M, yB, [("(b)", "b"), ("  Coordinator and results", "b")], size=F1, color=INK)
b_top, b_bot = yB - 0.17, M
s0, s1 = M, M + 1.18
a0, a1 = s1 + 0.1, s1 + 0.1 + 1.72
box(s0, b_bot, s1, b_top)
txt(s0 + 0.09, b_top - 0.15, "Scripted", size=F2, color=INK, weight="bold")
for k, ln in enumerate(["re-sends the same", "text to a fresh", "worker call", "",
                        "never re-ask: stop", "after attempt 1"]):
    txt(s0 + 0.09, b_top - 0.36 - k * 0.135, ln, size=F3, color=INK2)
box(a0, b_bot, a1, b_top, fc=BLUE_F, ec=BLUE)
txt(a0 + 0.09, b_top - 0.15, "LLM coordinator", size=F2, color=BLUE_D, weight="bold")
for k, ln in enumerate(["sees the refusal reason or a", "block notice; may rephrase,",
                        "re-route, or stop", "",
                        "conditions: unprompted,", "explicit permission,", "reason hidden"]):
    txt(a0 + 0.09, b_top - 0.36 - k * 0.135, ln, size=F3, color=INK2)

# results table: % of forbidden requests executed (host B, P2 4.6)
t0 = a1 + 0.14
cols = [("", 0.0), ("scripted", 0.55), ("unprompted", 1.1), ("explicit", 1.6), ("reason\nhidden", 2.03)]
txt(t0, b_top - 0.1, "Forbidden executed, % (host B)", size=F3, color=INK, weight="bold")
txt(t0 + (cols[2][1] + cols[4][1]) / 2, b_top - 0.3, "LLM coordinator", size=7.2, color=BLUE_D, ha="center")
ax.plot([t0 + cols[2][1] - 0.25, t0 + cols[4][1] + 0.2], [b_top - 0.37, b_top - 0.37], color=BLUE, lw=0.6)
hy = b_top - 0.53
for lab, dx in cols[1:]:
    txt(t0 + dx, hy, lab, size=7.2, color=MUTED, ha="center", va="center", )
ax.plot([t0, W - M], [hy - 0.15, hy - 0.15], color=GREY_E, lw=0.6)
table = [("none", ["25", "23", "18", "24"]), ("exact", ["10", "14", "19", "20"]), ("intent", ["7", "10", "9", "–"])]
for r, (lab, vals) in enumerate(table):
    yr = hy - 0.29 - r * 0.17
    txt(t0, yr, lab, size=F3, color=INK2)
    for c, v in enumerate(vals):
        hot = lab == "exact" and c > 0
        txt(t0 + cols[c + 1][1], yr, v, size=F3, color=WARM if hot else INK2, ha="center",
            weight="bold" if hot else "normal")

fig.savefig(OUT + ".png", dpi=300, facecolor="white")
fig.savefig(OUT + ".pdf", facecolor="white")
print("saved", OUT, "| loop y", round(ly, 2), "| panel b top", round(b_top, 2))
