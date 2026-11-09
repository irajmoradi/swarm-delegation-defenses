"""Round-4 metrics: results/r4_scores_main.json -> results/r4_metrics.json/.md, detection_vs_noise_r4.png
(bars: detection at 1%/5% FPR per method, for original / renamed / adaptive attacks at N=10)."""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis2 as A2  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
A2.LABEL.update({"linked_dep": "joint, dependency linker", "linked_dep_hop2sens": "joint, dependency + sens-only 2-hop",
                 "linked_effect": "joint, effect-summary linker", "linked_text": "joint, text linker",
                 "linked_hybrid": "joint, hybrid dep+effect"})
VARIANTS = [("orig", "original attacks"), ("pert", "identifier renaming (round 1-3 perturbation)"),
            ("adapt", "adaptive: dependency hiding")]


def main():
    d = json.loads((ROOT / "results/r4_scores_main.json").read_text())
    rows = d["rows"]
    rng = random.Random(0)
    conds = []
    for v, _ in VARIANTS:
        rs = []
        for r in rows:
            if r["role"] == "attack" and r["variant"] != v:
                continue
            r2 = copy.deepcopy(r)
            r2["perturbed"] = False
            rs.append(r2)
        c = A2.analyse(rs, 10, False, rng)
        c["variant"] = v
        conds.append(c)
    (ROOT / "results/r4_metrics.json").write_text(json.dumps(dict(taus=d["taus"], conditions=conds), indent=1))
    L = []
    for c, (v, desc) in zip(conds, VARIANTS):
        L.append(f"\n### N=10, {desc}: attack seqs={c['n_attack']}, cal seqs={c['n_cal']}, held-out benign seqs={c['n_eval']}")
        L.append("| method | pair recall | full chain | det@1% | det@5% | AUC | held-out FPR @1%/@5% | tokens/benign seq |")
        L.append("|---|---|---|---|---|---|---|---|")
        for m, mo in c["methods"].items():
            lk = c["linkers"].get(m.removeprefix("linked_"))
            rec = f"{lk['pair_recall']:.2f} | {lk['full_chain']:.2f}" if lk else "- | -"
            cell = lambda f: f"{mo[f]['detection']:.2f} [{mo[f]['ci95'][0]:.2f}, {mo[f]['ci95'][1]:.2f}]"
            L.append(f"| {A2.LABEL.get(m, m)} | {rec} | {cell('fpr1')} | {cell('fpr5')} | {mo['auc']:.2f} "
                     f"[{mo['auc_ci95'][0]:.2f}, {mo['auc_ci95'][1]:.2f}] | {mo['fpr1']['heldout_fpr']:.2f}/"
                     f"{mo['fpr5']['heldout_fpr']:.2f} | {mo.get('tokens_benign_seq', float('nan')):.0f} |")
    (ROOT / "results/r4_metrics.md").write_text("\n".join(L))
    print("\n".join(L))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    methods = list(conds[0]["methods"])
    col = {"per_commit": "#4C72B0", "linked_dep": "#C44E52", "linked_dep_hop2sens": "#8C613C",
           "linked_effect": "#8172B3", "linked_text": "#DD8452", "oracle_joint": "#55A868"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    w = 0.8 / len(methods)
    for ax, f in zip(axes, ["fpr1", "fpr5"]):
        for j, m in enumerate(methods):
            xs = [i + (j - (len(methods) - 1) / 2) * w for i in range(len(conds))]
            ys = [c["methods"][m][f]["detection"] for c in conds]
            lo = [y - c["methods"][m][f]["ci95"][0] for y, c in zip(ys, conds)]
            hi = [c["methods"][m][f]["ci95"][1] - y for y, c in zip(ys, conds)]
            ax.bar(xs, ys, w, yerr=[lo, hi], capsize=2, color=col.get(m, "#999"), label=A2.LABEL.get(m, m))
        ax.set_xticks(range(len(conds)))
        ax.set_xticklabels(["original", "renamed ids", "adaptive\n(dependency hiding)"], fontsize=8)
        ax.set_title(f"N=10, sequence-level FPR = {f[3:]}% (200 cal / 100 held-out benign seqs)", fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.3, axis="y")
    axes[0].set_ylabel("detection rate (attack seqs flagged)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=7, loc="lower center", ncol=4)
    fig.suptitle("Round 4: realistic benign baseline (every sequence contains a benign multi-commit feature); "
                 "gpt-5-mini, prompt ca06a3b9; 95% CI over chains", fontsize=8)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(ROOT / "detection_vs_noise_r4.png", dpi=140)


if __name__ == "__main__":
    main()
