"""Round 3: Mario's linking ideas. Same sequences, calibration, monitor prompt (hash ca06a3b93e837173) as round 2.

python src/experiment3.py --stage effects [--estimate-only]     # 1 gpt-5-mini effect summary per commit
python src/experiment3.py --stage recall                        # recall for all linkers, k sweep (free)
python src/experiment3.py --stage diagnose                      # missed-pair taxonomy table + figure (free)
python src/experiment3.py --stage score --noise 10 --linkers dep effect sens [--k 3] [--estimate-only]
python src/experiment3.py --stage judge ...                      # LLM pairwise judge (only if budget)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
from linker import linking_recall  # noqa: E402
from linkers2 import StructLinker, TextLinker  # noqa: E402
from linkers3 import DepLinker, EffectLinker, Hop2, SensLinker, TopK, UnionLinker  # noqa: E402
from llm import LLM  # noqa: E402
from repo_gen import FILES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EFF_PATH = ROOT / "results/r3_effects.json"


def stage_effects(args, llm):
    benign, attacks, pert, *_ = E2.load()
    jobs, ids = {}, {}
    for c in benign + attacks + pert:
        m = EffectLinker.msgs(c)
        k = LLM.key_of(EffectLinker.model, m, 600, "minimal")
        jobs[k] = (EffectLinker.model, m, "effect", 600)
        ids[c["id"]] = k
    out = E2.run_jobs(llm, jobs, args.estimate_only, out_tokens=60)
    if out is None:
        return
    eff = {i: out.get(k, "").strip().splitlines()[0] if out.get(k, "").strip() else "" for i, k in ids.items()}
    EFF_PATH.write_text(json.dumps(eff, indent=1))
    print(f"effects: {len(eff)}, empty {sum(1 for v in eff.values() if not v)}; ledger=${llm.spent:.4f}")


def make_linkers(cal, names, k=3):
    eff = json.loads(EFF_PATH.read_text()) if EFF_PATH.exists() else {}
    base = {}
    base["text"] = TextLinker(cal)
    base["struct"] = StructLinker(cal, "\n".join(FILES.values()))
    base["dep"] = DepLinker(cal, FILES)
    if eff:
        base["effect"] = EffectLinker(cal, eff)
        parts = [base["text"], base["dep"], base["effect"]]
        base["union"] = UnionLinker(cal, parts)
        base["sens"] = SensLinker(cal, parts)
    out = {}
    for n in names:
        hop = n.endswith("_hop2")
        b, _, kk = n.removesuffix("_hop2").partition("_k")
        L = base[b]
        kk = int(kk) if kk else k
        L = L if kk == 3 else TopK(L, kk)
        out[n] = Hop2(L) if hop else L
    return out


def stage_recall(args, llm):
    _, _, _, cal, test, chains, pchains = E2.load()
    names = ["text", "struct", "dep", "effect", "union", "sens"]
    names += [f"{n}_k{k}" for n in ("dep", "union", "sens") for k in (5, 10)]
    names += ["text_hop2", "dep_hop2", "sens_hop2"]
    Ls = make_linkers(cal, names)
    seqs = E2.build_sequences(chains, pchains, test, cal, [0, 10], 200, 30, {10})
    res = {}
    for n, L in Ls.items():
        for N in (0, 10):
            for pert in (False, True):
                att = [s for s in seqs if s["role"] == "attack" and s["N"] == N and s["perturbed"] == pert]
                if not att:
                    continue
                rec = [linking_recall(L.groups(s["commits"]), s["attack_pos"]) for s in att]
                cal_s = [s for s in seqs if s["role"] == "cal" and s["N"] == N]
                gs = [L.groups(s["commits"]) for s in cal_s]
                ns = sum(sum(len(g) > 1 for g in G) / len(G) for G in gs) / len(gs)
                extra = sum(sum(len(g) - 1 for g in G) for G in gs) / len(gs)  # extra commits read per seq
                key = f"{n}|N{N}{'|pert' if pert else ''}"
                res[key] = dict(pair_recall=sum(r for r, _ in rec) / len(rec), full=sum(f for _, f in rec) / len(rec),
                                benign_linked=ns, extra_commits_per_benign_seq=extra, tau=L.tau)
                print(f"{key:22s}", {k: round(v, 3) for k, v in res[key].items()})
    (ROOT / "results/r3_recall.json").write_text(json.dumps(res, indent=1))


# ---------------- diagnosis ----------------
def pair_reason(a, b, dep: DepLinker):
    files = bool(set(a["touched_files"]) & set(b["touched_files"]))
    ids = bool(set(a["identifiers"]) & set(b["identifiers"]) - {"config", "row", "rows"})
    e = dep.edges(a, b)
    strong = [t for t in ("defuse", "key", "literal", "into") if e[t]]
    if files:
        return "same file", strong
    if strong:
        return "deeper dependency (" + "/".join(strong) + ")", strong
    if ids:
        return "shared identifiers only", strong
    return "same effect target only", strong


def stage_diagnose(args, llm):
    _, _, _, cal, test, chains, pchains = E2.load()
    names = ["text", "struct", "dep", "effect", "sens", "dep_hop2"]
    Ls = make_linkers(cal, names)
    dep = Ls["dep"]
    seqs = E2.build_sequences(chains, pchains, test, cal, [0, 10], 0, 0, set())
    rows = []
    for ch, cs in chains.items():
        for i in range(3):
            for j in range(i + 1, 3):
                reason, strong = pair_reason(cs[i], cs[j], dep)
                row = dict(chain=ch, category=cs[0]["category"], pair=f"c{i}-c{j}", reason=reason,
                           shared_files=sorted(set(cs[i]["touched_files"]) & set(cs[j]["touched_files"])),
                           dep_edges={t: sorted(v) for t, v in dep.edges(cs[i], cs[j]).items() if v})
                for n, L in Ls.items():
                    for N in (0, 10):
                        att = [s for s in seqs if s["role"] == "attack" and s["N"] == N and s["chain"] == ch]
                        hit = 0
                        for s in att:
                            G = [set(g) for g in L.groups(s["commits"])]
                            a, b = s["attack_pos"][i], s["attack_pos"][j]
                            hit += any(a in g and b in g for g in G)
                        row[f"{n}_N{N}"] = hit / len(att)
                rows.append(row)
    (ROOT / "results/r3_diagnosis.json").write_text(json.dumps(rows, indent=1))
    L = ["| chain | pair | why linkable (first match) | dependency edges | " +
         " | ".join(f"{n} N0/N10" for n in names) + " |", "|---|---|---|---|" + "---|" * len(names)]
    for r in rows:
        edges = "; ".join(f"{t}: {', '.join(v[:3])}" for t, v in r["dep_edges"].items() if t != "coset") or "-"
        L.append(f"| {r['chain']} | {r['pair']} | {r['reason']} | {edges} | " +
                 " | ".join(f"{r[f'{n}_N0']:.2f}/{r[f'{n}_N10']:.2f}" for n in names) + " |")
    (ROOT / "results/r3_diagnosis.md").write_text("\n".join(L))
    print("\n".join(L))
    # figure: per linker at N=10, fraction of the 18 pairs linked vs missed, by reason
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    reasons = ["same file", "deeper dependency", "shared identifiers only", "same effect target only"]
    col = {"same file": "#4C72B0", "deeper dependency": "#DD8452", "shared identifiers only": "#8172B3",
           "same effect target only": "#937860"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, N in zip(axes, (0, 10)):
        x = range(len(names))
        bottom = [0.0] * len(names)
        for rs in reasons:
            linked = [sum(r[f"{n}_N{N}"] for r in rows if r["reason"].startswith(rs)) for n in names]
            missed = [sum(1 - r[f"{n}_N{N}"] for r in rows if r["reason"].startswith(rs)) for n in names]
            ax.bar(x, linked, bottom=bottom, color=col[rs], label=f"{rs}: linked")
            bottom = [b + v for b, v in zip(bottom, linked)]
            ax.bar(x, missed, bottom=bottom, color=col[rs], alpha=0.3, hatch="//", label=f"{rs}: missed")
            bottom = [b + v for b, v in zip(bottom, missed)]
        ax.set_xticks(list(x))
        ax.set_xticklabels(names, rotation=20)
        ax.set_title(f"18 true attack pairs, N={N} (solid = linked, hatched = missed)", fontsize=8)
    axes[0].set_ylabel("attack-commit pairs (avg over 3 arrangements)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=7, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Why attack pairs are missed: pair type (first match) x linker", fontsize=9)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    fig.savefig(ROOT / "results/r3_diagnosis.png", dpi=140)


def stage_score(args, llm):
    """Joint scoring with round-3 linkers, writing rows compatible with analysis2 (r3_scores_N*.json)."""
    _, _, _, cal, test, chains, pchains = E2.load()
    Ls = make_linkers(cal, args.linkers)
    seqs = E2.build_sequences(chains, pchains, test, cal, args.noise, args.n_cal, args.n_eval, set(args.perturb_noise))
    jobs = {}

    def add(cs):
        m = E2.single_msgs(cs[0]) if len(cs) == 1 else E2.joint_msgs(cs)
        k = LLM.key_of(E2.MON, m, E2.MAXTOK, "minimal")
        jobs.setdefault(k, (E2.MON, m, f"r2mon:{len(cs)}", E2.MAXTOK))
        return k

    for s in seqs:
        cs = s["commits"]
        s["k_single"] = [add([c]) for c in cs]
        s["k_oracle"] = add([cs[i] for i in s["attack_pos"]])
        s["groups"], s["k_linked"], s["rec"] = {}, {}, {}
        for n, L in Ls.items():
            g = L.groups(cs)
            s["groups"][n] = g
            s["k_linked"][n] = [s["k_single"][x[-1]] if len(x) == 1 else add([cs[i] for i in x]) for x in g]
            if s["role"] == "attack":
                s["rec"][n] = linking_recall(g, s["attack_pos"])
    out = E2.run_jobs(llm, jobs, args.estimate_only)
    if out is None:
        return

    def sc(k):
        if k not in out:
            return None
        v = E2.parse_score(out[k])
        return 50 if v is None else v

    def tok(k):
        r = llm.cache.get(k)
        return (r["in_tok"] + r["out_tok"]) if r else 0

    rows = []
    for s in seqs:
        single = [sc(k) for k in s["k_single"]]
        orc = sc(s["k_oracle"])
        if None in single or orc is None:
            continue
        others = [v for i, v in enumerate(single) if i not in s["attack_pos"]]
        scores = {"per_commit": max(single), "oracle_joint": max([orc] + others)}
        toks = {"per_commit": sum(tok(k) for k in s["k_single"])}
        ok = True
        for n in Ls:
            lv = [sc(k) for k in s["k_linked"][n]]
            if None in lv:
                ok = False
                break
            scores[f"linked_{n}"] = max(lv)
            toks[f"linked_{n}"] = sum(tok(k) for k in s["k_linked"][n])
        if ok:
            rows.append(dict(sid=s["sid"], role=s["role"], N=s["N"], chain=s["chain"], category=s["category"],
                             perturbed=s["perturbed"], scores=scores, tokens=toks,
                             attack_commit_scores=[single[i] for i in s["attack_pos"]], oracle_group_score=orc,
                             rec={n: list(v) for n, v in s["rec"].items()},
                             nonsingleton={n: sum(len(g) > 1 for g in s["groups"][n]) / len(s["groups"][n]) for n in Ls}))
    path = ROOT / f"results/r3_scores{args.tag}.json"
    path.write_text(json.dumps(dict(monitor=E2.MON, linkers=list(Ls), taus={n: L.tau for n, L in Ls.items()},
                                    noise=args.noise, n_cal=args.n_cal, n_eval=args.n_eval, window=0,
                                    n_parse_fail=sum(1 for t in out.values() if E2.parse_score(t) is None),
                                    rows=rows), indent=1))
    print(f"rows={len(rows)}/{len(seqs)} -> {path.name}; ledger=${llm.spent:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["effects", "recall", "diagnose", "score"], required=True)
    ap.add_argument("--noise", type=int, nargs="+", default=[0, 10])
    ap.add_argument("--perturb-noise", type=int, nargs="*", default=[10])
    ap.add_argument("--n-cal", type=int, default=200)
    ap.add_argument("--n-eval", type=int, default=30)
    ap.add_argument("--linkers", nargs="+", default=["dep", "effect", "sens"])
    ap.add_argument("--tag", default="")
    ap.add_argument("--estimate-only", action="store_true")
    a = ap.parse_args()
    llm = LLM()
    {"effects": stage_effects, "recall": stage_recall, "diagnose": stage_diagnose, "score": stage_score}[a.stage](a, llm)
