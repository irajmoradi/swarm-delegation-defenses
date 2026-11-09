"""Round 6 one-shot test analysis. Calibration = round-5 calibration seqs; test = fresh held-out benign (new v3
singles) + 42 attack chains (1 arrangement each) as original / rule-adaptive / LLM-adaptive variants.
Bootstrap CIs resample whole chains (n=42) and, separately, whole patterns (clustered, n=12).
-> results/r6_stats.json, results/r6.md, detection_vs_noise_r6.png"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stats5 as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LAB = {"per_commit": "per-commit", "linked_boundary_union": "joint, boundary linker", "linked_dep": "joint, dependency linker",
       "oracle_joint": "oracle joint (true groups; not deployable)",
       "zmax_linked_boundary_union": "zmax(per-commit, boundary joint)", "zmax_linked_dep": "zmax(per-commit, dependency joint)"}
METHODS = ["per_commit", "linked_boundary_union", "linked_dep", "oracle_joint", "zmax_linked_boundary_union", "zmax_linked_dep"]
PAIRS = [("zmax_linked_boundary_union", "per_commit"), ("zmax_linked_dep", "per_commit"),
         ("linked_dep", "per_commit"), ("linked_boundary_union", "per_commit"), ("oracle_joint", "per_commit")]
VARIANTS = [("orig", "original attacks"), ("adapt", "rule-based adaptive (dependency hiding)"),
            ("llm", "LLM-adaptive (sees per-commit policy text)")]


def main():
    rows_all = json.loads((ROOT / "results/r6_scores.json").read_text())["rows"]
    p = ROOT / "results/r6_llm_scores.json"
    if p.exists():
        rows_all += [r for r in json.loads(p.read_text())["rows"] if r["role"] == "attack"]
    out, L = {}, []
    for v, desc in VARIANTS:
        rows = [dict(r, scores=dict(r["scores"])) for r in rows_all if r["role"] != "attack" or r["variant"] == v]
        if not any(r["role"] == "attack" for r in rows):
            continue
        S.add_combos(rows, joints=("linked_boundary_union", "linked_dep"))
        rep = S.full_report(rows, METHODS, PAIRS)
        prow = [dict(r, chain=r["pattern"]) if r["role"] == "attack" else r for r in rows]
        rep_p = S.full_report(prow, METHODS, PAIRS[:2])
        att = [r for r in rows if r["role"] == "attack"]
        cal = [r for r in rows if r["role"] == "cal"]
        rep["pattern_clustered"] = {m: {k: rep_p["methods"][m][k] for k in ("auc_ci95", "matched5")} for m in METHODS}
        rep["pattern_clustered_paired"] = rep_p["paired"]
        rep["linking"] = {n: dict(pair_recall=float(np.mean([r["rec"][n][0] for r in att])),
                                  full_chain=float(np.mean([r["rec"][n][1] for r in att])),
                                  benign_linked=float(np.mean([r["nonsingleton"][n] for r in cal])))
                          for n in ("boundary_union", "dep")}
        out[v] = rep
        L.append(f"\n### TEST, {desc}: attack seqs={rep['n_attack']} (42 chains, 12 patterns), cal={rep['n_cal']}, held-out={rep['n_eval']}")
        L.append("| method | AUC [chain CI] | det@1% (realized FPR) | det@5% (realized FPR) | matched det @5% [chain CI] / [pattern CI] | matched @12% |")
        L.append("|---|---|---|---|---|---|")
        for m in METHODS:
            mo = rep["methods"][m]
            pc = rep["pattern_clustered"][m]["matched5"]["ci95"]
            L.append(f"| {LAB[m]} | {mo['auc']:.2f} [{mo['auc_ci95'][0]:.2f}, {mo['auc_ci95'][1]:.2f}] | "
                     f"{mo['np_fpr1']['detection']:.2f} ({mo['np_fpr1']['realized_fpr']:.2f}) | "
                     f"{mo['np_fpr5']['detection']:.2f} ({mo['np_fpr5']['realized_fpr']:.2f}) | "
                     f"{mo['matched5']['detection']:.2f} [{mo['matched5']['ci95'][0]:.2f}, {mo['matched5']['ci95'][1]:.2f}] / "
                     f"[{pc[0]:.2f}, {pc[1]:.2f}] | {mo['matched12']['detection']:.2f} |")
        L.append("\n| paired (A - B), calibrated thresholds | FPR | diff | chain CI | pattern CI | McNemar A-only/B-only, p |")
        L.append("|---|---|---|---|---|---|")
        for k, dd in rep["paired"].items():
            a, b = k.split(" - ")
            for f, x in dd.items():
                pci = rep["pattern_clustered_paired"].get(k, {}).get(f, {}).get("ci95")
                L.append(f"| {LAB[a]} - {LAB[b]} | {f[3:]}% | {x['diff']:+.2f} | [{x['ci95'][0]:+.2f}, {x['ci95'][1]:+.2f}] | "
                         + (f"[{pci[0]:+.2f}, {pci[1]:+.2f}]" if pci else "-") +
                         f" | {x['mcnemar_a_only']}/{x['mcnemar_b_only']}, {x['mcnemar_p']:.3f} |")
        L.append("\nlinking: " + json.dumps({k: {kk: round(vv, 2) for kk, vv in x.items()} for k, x in rep["linking"].items()}))
    for v in out.values():
        for mo in v["methods"].values():
            mo["roc"] = [list(q) for q in mo["roc"]]
    (ROOT / "results/r6_stats.json").write_text(json.dumps(out, indent=1))
    (ROOT / "results/r6.md").write_text("\n".join(L))
    print("\n".join(L))
    figure(out)


def figure(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    col = {"per_commit": "#4C72B0", "linked_boundary_union": "#DD8452", "linked_dep": "#C44E52", "oracle_joint": "#55A868",
           "zmax_linked_boundary_union": "#8172B3", "zmax_linked_dep": "#937860"}
    vs = [v for v, _ in VARIANTS if v in out]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
    w = 0.8 / len(METHODS)
    for ax, f in zip(axes, ("matched5", "matched12")):
        for j, m in enumerate(METHODS):
            for i, v in enumerate(vs):
                d = out[v]["methods"][m][f]
                ax.bar(i + (j - (len(METHODS) - 1) / 2) * w, d["detection"], w, color=col[m],
                       yerr=[[d["detection"] - d["ci95"][0]], [d["ci95"][1] - d["detection"]]], capsize=2,
                       label=LAB[m] if i == 0 else None)
        ax.set_xticks(range(len(vs)))
        ax.set_xticklabels([dict(VARIANTS)[v] for v in vs], fontsize=7)
        ax.set_title(f"detection at matched realized held-out FPR = {f[7:]}% (95% CI over 42 chains)", fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.grid(alpha=0.3, axis="y")
    axes[0].set_ylabel("detection (attack seqs flagged)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=7, loc="lower center", ncol=3)
    fig.suptitle("Round 6 one-shot test: 42 toy chains, N=10, fresh benign; gpt-5-mini, prompt ca06a3b9", fontsize=9)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(ROOT / "detection_vs_noise_r6.png", dpi=140)


if __name__ == "__main__":
    main()
