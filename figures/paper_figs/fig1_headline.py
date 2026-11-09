# Headline figure for P2. Every number is read from a results file at run time.
# Run: python3 -I fig1_headline.py <verify_baselines.jsonl> <mario r7_stats.json> <out.png>
#   verify_baselines.jsonl = output of figs/verify_baselines.py over the episodes of
#     host A  planD/runs/20261108T192100834630Z-v2-ledger (none, exact; audited run, recount matches A2-O B)
#     host B  planD/runs/20261108T203321606463Z-v2-ledger3-primeintellect-fp4 (none, exact, semantic, intent; NOT audited)
#     wording-change run planD/runs/20261107T083446934699Z-v2-memory (none, exact, lexical, scope; audited round 1)
#     host A four-arm run planD/runs/20261108T215135942724Z-v2-ledger3 (DeepInfra bf16; none, exact, semantic, intent; NOT audited)
#   "no-retry rule" = the none arm truncated to its first attempt (counterfactual, not a separate run).
#   r7_stats.json = commit_monitor/results/r7_stats.json (round 7, exploratory; point values verified by AUDIT_mario_r67)
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

VB, STATS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRAY, INK, INK2, SURF, GRID = "#8a8984", "#0b0b0b", "#52514e", "#fcfcfb", "#e6e5e1"
plt.rcParams.update({"font.size": 9.6, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "font.family": "DejaVu Sans"})

runs = {}
for line in open(VB):
    d = json.loads(line)
    r = d["run"]
    key = ("A" if r.endswith("-v2-ledger") else "B" if "primeintellect" in r else
           "A2" if r.endswith("-v2-ledger3") else "W")
    runs[key] = d["arms"]


def arm(run, m):
    a = runs[run][m]
    n, na = a["n_forb"], a["n_allowed"]
    return dict(total=100 * a["viol"] / n, first=100 * a["first_try_viol"] / n,
                blocked=100 * a["allowed_ledger_block"] / na,
                noretry_lost=100 * (a["allowed_success"] - a["allowed_first_attempt_success"]) / na)


def noretry(run):
    a = arm(run, "none")
    return dict(total=a["first"], first=a["first"], blocked=a["noretry_lost"])


fig = plt.figure(figsize=(10.0, 7.6))
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], width_ratios=[1, 1.05])
a = fig.add_subplot(gs[0, :]); b = fig.add_subplot(gs[1, 0]); c = fig.add_subplot(gs[1, 1])
fig.patch.set_facecolor(SURF)
for ax in (a, b, c):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)

# (a) first try vs re-ask, with the no-retry rule as its own (hatched) bar.
bars = [("A", "none"), ("A", "noretry"), ("A", "exact"),
        ("A2", "none"), ("A2", "noretry"), ("A2", "exact"), ("A2", "semantic"), ("A2", "intent"),
        ("B", "none"), ("B", "noretry"), ("B", "exact"), ("B", "semantic"), ("B", "intent")]
labels = {"none": "none\n(re-ask)", "noretry": "no-\nretry", "exact": "exact", "semantic": "text-\nsim.",
          "intent": "intent\nscreen"}
xs = [0, 1, 2, 3.4, 4.4, 5.4, 6.4, 7.4, 8.8, 9.8, 10.8, 11.8, 12.8]
W = 0.74
for x, (run, m) in zip(xs, bars):
    v = noretry(run) if m == "noretry" else arm(run, m)
    if m == "noretry":
        a.bar(x, v["first"], W, color=SURF, edgecolor=BLUE, lw=1.2, hatch="////")
    else:
        a.bar(x, v["first"], W, color=BLUE, edgecolor=SURF, lw=2)
    if v["total"] - v["first"] > 0.05:
        a.bar(x, v["total"] - v["first"], W, bottom=v["first"], color=ORANGE, edgecolor=SURF, lw=2)
    a.text(x, v["total"] + 0.8, f"{v['total']:.1f}", ha="center", va="bottom", fontsize=8.2, color=INK)
    a.text(x, -1.6, f"{v['blocked']:.1f}", ha="center", va="top", fontsize=8.0,
           color=INK if v["blocked"] >= 10 else INK2, fontweight="bold" if v["blocked"] >= 10 else "normal")
a.set_xticks(xs)
a.set_xticklabels([labels[m] for _, m in bars], fontsize=7.8)
a.text(-0.68, -1.6, "allowed\nlost (%):", ha="right", va="top", fontsize=8.0, color=INK2)
a.set_ylim(-5.5, 37)
a.set_yticks(range(0, 31, 10))
a.spines["bottom"].set_visible(False)
a.axhline(0, color=INK2, lw=0.8)
a.set_xlim(-0.6, 13.3)
a.set_ylabel("forbidden requests executed (%)")
a.text(1.0, 36.5, "host A, ledger run\n(audited)", ha="center", va="top", fontsize=8.4, color=INK2)
a.text(5.4, 36.5, "host A, four-arm run\u2020\n(same host, later run)", ha="center", va="top", fontsize=8.4, color=INK2)
a.text(10.8, 36.5, "host B\u2020 (fp4; compare\nwithin host only)", ha="center", va="top", fontsize=8.4, color=INK2)
a.axvline(2.7, color=GRID, lw=1)
a.axvline(8.1, color=GRID, lw=1)
a.legend(handles=[Patch(facecolor=BLUE, label="first try"), Patch(facecolor=ORANGE, label="after a re-ask")],
         loc="upper right", bbox_to_anchor=(1.0, 0.74), frameon=False, fontsize=8.4)
a.set_title("(a) Re-asking: what each defense removes", loc="left", fontsize=10.5, color=INK)

# (b) trade-off plane: violations vs allowed work lost, every arm of all four runs.
# Colour = defense; marker = run.
runs_b = [("A", "host A ledger run", "o", ["none", "noretry", "exact"]),
          ("A2", "host A four-arm run\u2020", "v", ["none", "noretry", "exact", "semantic", "intent"]),
          ("B", "host B four-arm run\u2020", "s", ["none", "noretry", "exact", "semantic", "intent"]),
          ("W", "host A, wording changes", "D", ["none", "noretry", "exact", "lexical", "scope"])]
arm_col = {"none": GRAY, "noretry": BLUE, "exact": BLUE, "semantic": ORANGE, "lexical": ORANGE,
           "intent": "#6250d6", "scope": AQUA}
for run, lab, mk, ms in runs_b:
    for m in ms:
        v = noretry(run) if m == "noretry" else arm(run, m)
        col = arm_col[m]
        hollow = m == "noretry"
        b.plot(v["blocked"], v["total"], mk, ms=7, color=col, mfc=SURF if hollow else col,
               mec=col if hollow else SURF, mew=1.6 if hollow else 0.8, alpha=0.95)
b.set_xscale("symlog", linthresh=1)
b.set_xticks([0, 1, 2, 5, 10, 20, 40])
b.set_xticklabels(["0", "1", "2", "5", "10", "20", "40"])
b.set_xlim(-0.1, 70)
b.set_ylim(0, 31)
b.grid(axis="x", color=GRID, lw=0.6)
b.set_xlabel("allowed requests lost (%; log scale above 1)")
b.set_ylabel("forbidden requests executed (%)")
arm_h = [Line2D([], [], color=c_, marker="o", lw=0, ms=7, label=l_) for l_, c_ in
         [("none", GRAY), ("exact", BLUE), ("text similarity", ORANGE), ("intent screen", "#6250d6"), ("scope", AQUA)]]
arm_h.insert(1, Line2D([], [], color=BLUE, marker="o", mfc=SURF, mew=1.6, lw=0, ms=7, label="no-retry rule"))
leg1 = b.legend(handles=arm_h, loc="upper right", frameon=False, fontsize=7.8, title="defense", title_fontsize=7.8)
b.add_artist(leg1)
b.legend(handles=[Line2D([], [], color=INK2, marker=m_, lw=0, ms=7, label=l_) for _, l_, m_, _ in runs_b],
         loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, fontsize=7.6, title="run", title_fontsize=7.6)
b.set_title("(b) The trade-off: protection vs allowed work lost", loc="left", fontsize=10.5, color=INK)

# (c) Mario round 7: AUC with pattern-clustered CIs (the robust comparison per AUDIT_mario_r67: low-FPR
# detection sits on score ties and on thresholds set on the test benign set).
st = json.load(open(STATS))
main, k1 = st["main"], st["k_per_commit"]["k1"]
methods = [("per_commit", "per-commit"), ("linked_dep", "joint,\ndependency\nlink"),
           ("oracle_joint", "joint,\noracle\n(true groups)"), ("zmax_linked_dep", "zmax(per,\ndep)")]
variants = [("orig|all", "original, all (42)", AQUA, "s"), ("orig|valid-only", "original, valid (21)", BLUE, "o"),
            ("llm|valid-only", "LLM-rewritten, valid (13)", ORANGE, "D")]
for i, (mk, _) in enumerate(methods):
    for j, (vk, _, col, mrk) in enumerate(variants):
        m = main[vk][mk]
        lo, hi = m["auc_ci"]
        x = i + (j - 1) * 0.22
        c.plot([x, x], [lo, hi], color=col, lw=2, solid_capstyle="round")
        c.plot(x, m["auc"], mrk, ms=6, color=col, mec=SURF, mew=1)
lo, hi = k1["auc_ci"]
c.plot([-0.44, -0.44], [lo, hi], color=GRAY, lw=2, solid_capstyle="round")
c.plot(-0.44, k1["auc"], "s", ms=5.5, color=SURF, mec=GRAY, mew=2)
c.axvspan(1.6, 2.4, color=GRID, alpha=0.45, lw=0)
c.text(2.0, 0.455, "not deployable", ha="center", va="bottom", fontsize=7.8, color=INK2)
c.set_xticks(range(len(methods)))
c.set_xticklabels([m[1] for m in methods], fontsize=8.2)
c.set_ylim(0.45, 1.12)
c.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
c.set_xlim(-0.65, len(methods) - 0.5)
c.set_ylabel("AUC (attack vs benign sequences)")
h = [Line2D([], [], color=col, marker=m, lw=2, label=l) for _, l, col, m in variants]
h.append(Line2D([], [], color=GRAY, marker="s", mfc=SURF, mew=2, lw=2, label="original, merged into 1 commit (42)"))
c.legend(handles=h, loc="upper left", frameon=False, fontsize=7.6, ncol=2)
c.set_title("(c) Splitting: per-commit vs linked review\u2020", loc="left", fontsize=10.5, color=INK)

fig.tight_layout()
fig.savefig(OUT, dpi=200, facecolor=SURF)
print("wrote", OUT)
