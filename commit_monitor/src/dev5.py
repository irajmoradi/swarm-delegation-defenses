"""Round 5 items 1-4 on the round-4 scores (now the DEV split; its held-out set has been looked at)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stats5 as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
rows_all = json.loads((ROOT / "results/r4_scores_main.json").read_text())["rows"]
out = {}
for v in ("orig", "adapt"):
    rows = [dict(r, scores=dict(r["scores"])) for r in rows_all if r["role"] != "attack" or r["variant"] == v]
    S.add_combos(rows, joints=("linked_dep", "linked_effect"))
    methods = ["per_commit", "linked_dep", "linked_dep_hop2sens", "linked_effect", "max_linked_dep", "zmax_linked_dep",
               "max_linked_effect", "zmax_linked_effect"]
    rep = S.full_report(rows, methods, [("linked_dep", "per_commit"), ("linked_effect", "per_commit"),
                                        ("zmax_linked_dep", "per_commit")])
    rep["loco_lr"] = {j: S.loco_lr(rows, "per_commit", j) for j in ("linked_dep", "linked_effect")}
    out[v] = rep
    print(f"\n=== DEV (round-4 seqs), attacks={v}: n_att={rep['n_attack']} n_cal={rep['n_cal']} n_eval={rep['n_eval']}")
    print("method | AUC | NP det@1/5 (realized FPR) | conformal det@1/5 (realized) | matched-FPR det @5% / @12%")
    for m, mo in rep["methods"].items():
        print(f"{m:22s} {mo['auc']:.2f} [{mo['auc_ci95'][0]:.2f},{mo['auc_ci95'][1]:.2f}] | "
              f"{mo['np_fpr1']['detection']:.2f}({mo['np_fpr1']['realized_fpr']:.2f}) {mo['np_fpr5']['detection']:.2f}({mo['np_fpr5']['realized_fpr']:.2f}) | "
              f"{mo['conf_fpr1']['detection']:.2f}({mo['conf_fpr1']['realized_fpr']:.2f}) {mo['conf_fpr5']['detection']:.2f}({mo['conf_fpr5']['realized_fpr']:.2f}) | "
              f"{mo['matched5']['detection']:.2f} [{mo['matched5']['ci95'][0]:.2f},{mo['matched5']['ci95'][1]:.2f}] / "
              f"{mo['matched12']['detection']:.2f} [{mo['matched12']['ci95'][0]:.2f},{mo['matched12']['ci95'][1]:.2f}]")
    for k, d in rep["paired"].items():
        print("paired", k, {f: (round(x["diff"], 2), [round(y, 2) for y in x["ci95"]], round(x["p_boot_le0"], 3),
                                 f"McN {x['mcnemar_a_only']}/{x['mcnemar_b_only']} p={x['mcnemar_p']:.3f}") for f, x in d.items()})
    print("LOCO-LR", rep["loco_lr"])
for v in out.values():
    for mo in v["methods"].values():
        mo.pop("roc", None) if False else None
(ROOT / "results/r5_dev_stats.json").write_text(json.dumps(out, indent=1))
