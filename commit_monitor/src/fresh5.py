"""Round 5: ONE-SHOT evaluation on the fresh split (results/r5_scores_fresh.json). Methods and combos were
fixed on the dev split before this was run. -> results/r5_fresh_stats.json, results/r5_fresh.md, figures."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stats5 as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LAB = {"per_commit": "per-commit", "linked_boundary_union": "joint, boundary linker",
       "linkedQ6_boundary_union": "joint, boundary linker, NEW combined-effect question",
       "linked_struct7_S2": "joint, structured-effect linker (S2)",
       "zmax_linked_boundary_union": "zmax(per-commit, boundary joint)",
       "zmax_linkedQ6_boundary_union": "zmax(per-commit, boundary joint NEW question)",
       "zmax_linked_struct7_S2": "zmax(per-commit, structured joint)"}


def main():
    d = json.loads((ROOT / "results/r5_scores_fresh.json").read_text())
    out, L = {}, []
    joints = ["linked_boundary_union", "linkedQ6_boundary_union", "linked_struct7_S2"]
    for v in ("orig", "adapt"):
        rows = [dict(r, scores=dict(r["scores"])) for r in d["rows"] if r["role"] != "attack" or r["variant"] == v]
        S.add_combos(rows, joints=joints)
        methods = ["per_commit"] + joints + [f"zmax_{j}" for j in joints]
        pairs = [(j, "per_commit") for j in joints] + [("linkedQ6_boundary_union", "linked_boundary_union"),
                                                        ("zmax_linked_boundary_union", "per_commit"),
                                                        ("zmax_linkedQ6_boundary_union", "per_commit")]
        rep = S.full_report(rows, methods, pairs)
        att = [r for r in rows if r["role"] == "attack"]
        cal = [r for r in rows if r["role"] == "cal"]
        ev = [r for r in rows if r["role"] == "benign_eval"]
        rep["linking"] = {n: dict(pair_recall=float(np.mean([r["rec"][n][0] for r in att])),
                                  full_chain=float(np.mean([r["rec"][n][1] for r in att])),
                                  benign_linked=float(np.mean([r["nonsingleton"][n] for r in cal])),
                                  xfeature_pair_recall=float(np.mean([r["xfeat_recall"][n] for r in cal])))
                          for n in d["linkers"]}
        rep["tokens_benign_seq"] = {m: float(np.mean([r["tokens"][m] for r in ev])) for m in ev[0]["tokens"]}
        out[v] = rep
        L.append(f"\n### FRESH split, attacks={v}: attack seqs={rep['n_attack']}, cal={rep['n_cal']}, held-out={rep['n_eval']}")
        L.append("| method | AUC | det@1% (realized FPR) | det@5% (realized FPR) | conformal det@5% (realized) | matched det @5% FPR | matched det @12% FPR |")
        L.append("|---|---|---|---|---|---|---|")
        for m, mo in rep["methods"].items():
            L.append(f"| {LAB.get(m, m)} | {mo['auc']:.2f} [{mo['auc_ci95'][0]:.2f}, {mo['auc_ci95'][1]:.2f}] | "
                     f"{mo['np_fpr1']['detection']:.2f} ({mo['np_fpr1']['realized_fpr']:.2f}) | "
                     f"{mo['np_fpr5']['detection']:.2f} ({mo['np_fpr5']['realized_fpr']:.2f}) | "
                     f"{mo['conf_fpr5']['detection']:.2f} ({mo['conf_fpr5']['realized_fpr']:.2f}) | "
                     f"{mo['matched5']['detection']:.2f} [{mo['matched5']['ci95'][0]:.2f}, {mo['matched5']['ci95'][1]:.2f}] | "
                     f"{mo['matched12']['detection']:.2f} [{mo['matched12']['ci95'][0]:.2f}, {mo['matched12']['ci95'][1]:.2f}] |")
        L.append("\n| paired comparison (A - B) | FPR | diff | 95% CI | P(boot diff<=0) | McNemar A-only/B-only, p |")
        L.append("|---|---|---|---|---|---|")
        for k, dd in rep["paired"].items():
            a, b = k.split(" - ")
            for f, x in dd.items():
                L.append(f"| {LAB.get(a, a)} - {LAB.get(b, b)} | {f[3:]}% | {x['diff']:+.2f} | [{x['ci95'][0]:+.2f}, "
                         f"{x['ci95'][1]:+.2f}] | {x['p_boot_le0']:.2f} | {x['mcnemar_a_only']}/{x['mcnemar_b_only']}, "
                         f"{x['mcnemar_p']:.2f} |")
        L.append("\nlinking: " + json.dumps({k: {kk: round(vv, 2) for kk, vv in x.items()} for k, x in rep["linking"].items()}))
        L.append("tokens per held-out benign seq: " + json.dumps({k: round(x) for k, x in rep["tokens_benign_seq"].items()}))
    for v in out.values():
        for mo in v["methods"].values():
            mo["roc"] = [list(p) for p in mo["roc"]]
    (ROOT / "results/r5_fresh_stats.json").write_text(json.dumps(out, indent=1))
    (ROOT / "results/r5_fresh.md").write_text("\n".join(L))
    print("\n".join(L))
    figure(out)


def figure(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    show = ["per_commit", "linked_boundary_union", "linkedQ6_boundary_union", "linked_struct7_S2",
            "zmax_linkedQ6_boundary_union"]
    col = {"per_commit": "#4C72B0", "linked_boundary_union": "#DD8452", "linkedQ6_boundary_union": "#C44E52",
           "linked_struct7_S2": "#8172B3", "zmax_linkedQ6_boundary_union": "#55A868"}
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    for ax, v in zip(axes[:2], ("orig", "adapt")):
        for m in show:
            mo = out[v]["methods"][m]
            xs, ys = zip(*mo["roc"])
            ax.step(xs, ys, where="post", color=col[m], label=f"{LAB[m]} (AUC {mo['auc']:.2f})")
        ax.plot([0, 1], [0, 1], ":", color="#999")
        ax.axvline(0.05, color="#bbb", lw=0.8); ax.axvline(0.12, color="#bbb", lw=0.8)
        ax.set_xlim(0, 0.4); ax.set_xlabel("held-out benign FPR (sequence level)")
        ax.set_ylabel("detection"); ax.set_title(f"FRESH split ROC, {'original' if v == 'orig' else 'adaptive'} attacks", fontsize=8)
        ax.legend(fontsize=6, loc="lower right"); ax.grid(alpha=0.3)
    ax = axes[2]
    w = 0.8 / len(show)
    for j, m in enumerate(show):
        for i, (v, f) in enumerate([("orig", "matched5"), ("orig", "matched12"), ("adapt", "matched5"), ("adapt", "matched12")]):
            d = out[v]["methods"][m][f]
            ax.bar(i + (j - (len(show) - 1) / 2) * w, d["detection"], w, color=col[m],
                   yerr=[[d["detection"] - d["ci95"][0]], [d["ci95"][1] - d["detection"]]], capsize=2,
                   label=LAB[m] if i == 0 else None)
    ax.set_xticks(range(4)); ax.set_xticklabels(["orig @5%", "orig @12%", "adapt @5%", "adapt @12%"], fontsize=8)
    ax.set_ylim(0, 1.05); ax.set_title("detection at MATCHED realized held-out FPR (95% CI over chains)", fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    fig.suptitle("Round 5, one-shot FRESH split (N=10, every seq has a same-agent and a cross-agent benign feature); "
                 "gpt-5-mini", fontsize=9)
    fig.tight_layout()
    fig.savefig(ROOT / "detection_vs_noise_r5.png", dpi=140)


if __name__ == "__main__":
    main()
