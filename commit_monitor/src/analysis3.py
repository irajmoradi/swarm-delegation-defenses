"""Round-3 metrics: merge r2 (text/struct/llmtag) and r3 (dep/dep_hop2/effect/sens...) scores by sequence id
(same sequences, same prompt, same cached per-commit/oracle calls), then reuse analysis2.analyse.

-> results/r3_metrics.json, results/r3_metrics.md, detection_vs_noise_r3.png, results/r3_cost_vs_detection.png
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis2 as A2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
A2.LABEL.update({"linked_dep": "joint on dependency linker", "linked_dep_hop2": "joint on dependency + 2-hop",
                 "linked_effect": "joint on effect-summary linker", "linked_sens": "joint on sensitivity-filtered union",
                 "linked_sens_hop2": "joint on sens-union + 2-hop", "linked_union": "joint on union linker"})


def main():
    r2 = []
    for f in ("r2_scores_N0.json", "r2_scores_N10.json"):
        r2 += json.loads((ROOT / "results" / f).read_text())["rows"]
    r3files = sorted((ROOT / "results").glob("r3_scores*.json"))
    by = {(r["sid"]): r for r in r2}
    for f in r3files:
        for r in json.loads(f.read_text())["rows"]:
            if r["sid"] not in by:
                continue
            b = by[r["sid"]]
            assert b["scores"]["per_commit"] == r["scores"]["per_commit"], r["sid"]
            for k in ("scores", "tokens", "rec", "nonsingleton"):
                b[k].update({kk: vv for kk, vv in r[k].items() if kk not in b[k]})
    rows = [r for r in by.values()]
    keep = ["per_commit", "linked_text", "linked_struct", "linked_llmtag", "linked_effect", "linked_dep",
            "linked_sens", "linked_dep_hop2", "linked_sens_hop2", "oracle_joint"]
    for r in rows:
        r["scores"] = {k: r["scores"][k] for k in keep if k in r["scores"]}
    # keep only sequences scored by every method (r3 used 30 held-out benign seqs at N=0, r2 used 60)
    allm = set.union(*[set(r["scores"]) for r in rows])
    rows = [r for r in rows if set(r["scores"]) >= allm]
    for r in rows:
        r["scores"] = {k: r["scores"][k] for k in keep if k in allm}
    rng = random.Random(0)
    conds = []
    for N in sorted({r["N"] for r in rows}):
        for pert in (False, True):
            if any(r["role"] == "attack" and r["N"] == N and r["perturbed"] == pert for r in rows):
                conds.append(A2.analyse(rows, N, pert, rng))
    (ROOT / "results/r3_metrics.json").write_text(json.dumps(dict(r3files=[str(f) for f in r3files], conditions=conds),
                                                             indent=1))
    L = []
    for c in conds:
        L.append(f"\n### N={c['N']}{' perturbed' if c['perturbed'] else ''}: attack seqs={c['n_attack']}, "
                 f"cal seqs={c['n_cal']}, held-out benign seqs={c['n_eval']}")
        L.append("| method | pair recall | full chain | det@1% | det@5% | AUC | held-out FPR @1%/@5% | tokens/benign seq |")
        L.append("|---|---|---|---|---|---|---|---|")
        for m, mo in c["methods"].items():
            ln = m.removeprefix("linked_")
            lk = c["linkers"].get(ln)
            rec = f"{lk['pair_recall']:.2f} | {lk['full_chain']:.2f}" if lk else "- | -"
            cell = lambda f: f"{mo[f]['detection']:.2f} [{mo[f]['ci95'][0]:.2f}, {mo[f]['ci95'][1]:.2f}]"
            L.append(f"| {A2.LABEL.get(m, m)} | {rec} | {cell('fpr1')} | {cell('fpr5')} | {mo['auc']:.2f} "
                     f"[{mo['auc_ci95'][0]:.2f}, {mo['auc_ci95'][1]:.2f}] | {mo['fpr1']['heldout_fpr']:.2f}/"
                     f"{mo['fpr5']['heldout_fpr']:.2f} | {mo.get('tokens_benign_seq', float('nan')):.0f} |")
    (ROOT / "results/r3_metrics.md").write_text("\n".join(L))
    print("\n".join(L))
    figures(conds)


def figures(conds):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    show = ["per_commit", "linked_text", "linked_effect", "linked_dep", "linked_sens", "linked_dep_hop2",
            "linked_sens_hop2", "oracle_joint"]
    col = {"per_commit": "#4C72B0", "linked_text": "#DD8452", "linked_effect": "#8172B3", "linked_dep": "#C44E52",
           "linked_sens": "#DA8BC3", "linked_dep_hop2": "#8C613C", "linked_sens_hop2": "#CCB974",
           "oracle_joint": "#55A868"}
    base = [c for c in conds if not c["perturbed"]]
    show = [m for m in show if m in base[0]["methods"]]
    Ns = [c["N"] for c in base]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
    for ax, f in zip(axes, ["fpr1", "fpr5"]):
        for j, m in enumerate(show):
            xs, ys, lo, hi = [], [], [], []
            for c in base:
                d = c["methods"][m][f]
                xs.append(c["N"] + (j - len(show) / 2) * 0.28); ys.append(d["detection"])
                lo.append(d["detection"] - d["ci95"][0]); hi.append(d["ci95"][1] - d["detection"])
            ax.errorbar(xs, ys, yerr=[lo, hi], marker="o", capsize=2, label=A2.LABEL[m], color=col[m])
        ax.set_title(f"sequence-level FPR = {f[3:]}% (200 calibration seqs per N)", fontsize=8)
        ax.set_xlabel("benign commits per attack sequence (N)")
        ax.set_xticks(Ns)
        ax.set_ylim(-0.05, 1.05)
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("detection rate (attack seqs flagged)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=7, loc="lower center", ncol=4)
    fig.suptitle("Round 3 (gpt-5-mini monitor, same prompt as round 2): detection vs noise; 6 toy chains x 3; "
                 "95% bootstrap CI over chains; NON-adaptive attacker", fontsize=8)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(ROOT / "detection_vs_noise_r3.png", dpi=140)
    # cost vs detection at N=10
    c10 = next(c for c in base if c["N"] == 10)
    fig, ax = plt.subplots(figsize=(6, 4))
    for m in show:
        mo = c10["methods"][m]
        if "tokens_benign_seq" not in mo:
            continue
        ax.errorbar(mo["tokens_benign_seq"], mo["fpr5"]["detection"],
                    yerr=[[mo["fpr5"]["detection"] - mo["fpr5"]["ci95"][0]], [mo["fpr5"]["ci95"][1] - mo["fpr5"]["detection"]]],
                    marker="o", capsize=3, color=col[m], label=A2.LABEL[m])
    ax.set_xlabel("monitor tokens per benign sequence (N=10, gpt-5-mini)")
    ax.set_ylabel("detection at 5% FPR")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=6)
    ax.set_title("Detection vs monitor cost, N=10 (oracle omitted: not deployable)", fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "results/r3_cost_vs_detection.png", dpi=140)


if __name__ == "__main__":
    main()
