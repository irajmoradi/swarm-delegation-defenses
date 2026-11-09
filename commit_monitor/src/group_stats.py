"""Group-size / benign-linkage stats per linker at N=10 (free). -> results/r3_group_stats.json"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
from experiment3 import make_linkers  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
_, _, _, cal, test, chains, pchains = E2.load()
names = ["text", "struct", "dep", "effect", "sens", "dep_hop2", "sens_hop2"]
Ls = make_linkers(cal, names)
seqs = E2.build_sequences(chains, pchains, test, cal, [10], 200, 30, set())
res = {}
for n, L in Ls.items():
    gs_cal, gs_att, pulled, nb, bb_links, joint_calls = [], [], 0, 0, [], []
    for s in seqs:
        G = L.groups(s["commits"])
        if s["role"] == "cal":
            gs_cal += [len(g) for g in G]
            bb_links.append(sum(len(g) - 1 for g in G))
            joint_calls.append(sum(len(g) > 1 for g in G))
        elif s["role"] == "attack":
            gs_att += [len(g) for g in G]
            ap = set(s["attack_pos"])
            in_att = set()
            for g in G:
                if set(g) & ap:
                    in_att |= set(g) - ap
            pulled += len(in_att)
            nb += len(s["commits"]) - len(ap)
            # groups containing an attack commit: size
    res[n] = dict(tau=L.tau,
                  cal_group_mean=sum(gs_cal) / len(gs_cal), cal_group_max=max(gs_cal),
                  attack_seq_group_mean=sum(gs_att) / len(gs_att), attack_seq_group_max=max(gs_att),
                  benign_commits_pulled_into_attack_groups=pulled / nb,
                  benign_benign_links_per_cal_seq=sum(bb_links) / len(bb_links),
                  joint_calls_per_cal_seq=sum(joint_calls) / len(joint_calls))
    print(f"{n:10s}", {k: round(v, 3) for k, v in res[n].items()})
(ROOT / "results/r3_group_stats.json").write_text(json.dumps(res, indent=1))
