"""Round 6: 42 attack chains (6 original + 36 new), fresh TEST split (new benign single commits v3, new seeds),
calibration = the round-5 calibration sequences (never used as test). Methods: per-commit, boundary joint,
dependency joint, oracle joint, and the label-free zmax combinations fixed in round 5.

python src/experiment6.py --stage score [--estimate-only]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
import experiment4 as E4  # noqa: E402
import experiment5 as E5  # noqa: E402
from experiment import rng_for  # noqa: E402
from linker import linking_recall  # noqa: E402
from llm import LLM  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SEED = 61
N = 10
PATTERN_OF_ORIG = {"A01": "P1", "A02": "P2", "A03": "P3", "A04": "P4", "A05": "P5", "A06": "P6"}


def load6():
    D = E5.load5()
    new = json.loads((ROOT / "data/attacks/attacks_r6.json").read_text())
    chains = {}
    for ch, cs in D["chains"].items():
        chains[ch] = [dict(c, pattern=PATTERN_OF_ORIG[ch]) for c in cs]
    for c in new:
        chains.setdefault(c["chain"], []).append(c)
    for v in chains.values():
        v.sort(key=lambda c: c["idx"])
    D["chains42"] = chains
    D["achains42"] = {ch: [dict(a, pattern=cs[0]["pattern"]) for a in E4.adaptive(cs)] for ch, cs in chains.items()}
    D["v3"] = json.loads((ROOT / "data/benign/benign_v3.json").read_text())
    return D


def cal_seqs(D, n_cal):
    """Exactly the round-5 calibration sequences (same builder, seed, authors), plus a fixed fake oracle group."""
    seqs = [s for s in E5.build_fresh(D, n_cal, 0) if s["role"] == "cal"]
    for s in seqs:
        s["attack_pos"] = sorted(rng_for("r6fake", s["sid"]).sample(range(len(s["commits"])), 3))
    return seqs


def test_seqs(D, n_eval):
    calF = {k for k in D["allf"] if k in E5.FRESH_CAL_F}
    calX = {k for k in D["x"] if k in E5.FRESH_CAL_X}
    evF = [f for k, f in sorted(D["allf"].items()) if k not in calF]
    evX = [f for k, f in sorted(D["x"].items()) if k not in calX]
    A = E5.AGENTS
    seqs = []

    def make(r, attack):
        f, x = r.choice(evF), r.choice(evX)
        fa = r.choice(A)
        xa = r.sample(A, len(x))
        aa = r.sample(A, len(attack)) if attack else []
        L = N + 3
        sing = [E5.with_author(c, r.choice(A)) for c in r.sample(D["v3"], L - len(attack) - len(f) - len(x))]
        slots, seq, pos = list(range(L)), [None] * L, {}
        for name, items in (("a", [E5.with_author(c, a) for c, a in zip(attack, aa)]), ("f", [E5.with_author(c, fa) for c in f]),
                            ("x", [E5.with_author(c, a) for c, a in zip(x, xa)])):
            if items:
                p = sorted(r.sample(slots, len(items)))
                slots = [s for s in slots if s not in p]
                pos[name] = p
                for i, c in zip(p, items):
                    seq[i] = c
        it = iter(sing)
        seq = [c if c is not None else next(it) for c in seq]
        return seq, pos.get("a", []), pos["f"], pos["x"]

    for ch, cs in sorted(D["chains42"].items()):
        r = rng_for("r6att", ch, SEED)
        seq, ap, fp, xp = make(r, cs)
        for v in ("orig", "adapt"):
            src = cs if v == "orig" else D["achains42"][ch]
            s2 = [dict(src[ap.index(p)], author=c["author"]) if p in ap else c for p, c in enumerate(seq)]
            seqs.append(dict(sid=f"r6{v}_{ch}", role="attack", N=N, chain=ch, pattern=cs[0]["pattern"],
                             category=cs[0]["category"], variant=v, commits=s2, attack_pos=ap, feat_pos=fp, x_pos=xp))
    for s in range(n_eval):
        r = rng_for("r6eval", s, SEED)
        seq, _, fp, xp = make(r, [])
        seqs.append(dict(sid=f"r6eval_{s}", role="benign_eval", N=N, chain=None, pattern=None, category=None,
                         variant="benign", commits=seq, attack_pos=sorted(rng_for("r6fake", s).sample(range(N + 3), 3)),
                         feat_pos=fp, x_pos=xp))
    return seqs


def main(args):
    llm = LLM()
    D = load6()
    calF = [c for k, f in D["allf"].items() if k in E5.FRESH_CAL_F for c in f]
    calX = [c for k, f in D["x"].items() if k in E5.FRESH_CAL_X for c in f]
    fit = D["cal1"] + calF + calX  # same fit pool as round 5
    Ls = E5.make_linkers5(D, ["boundary_union", "dep"], fit)
    seqs = cal_seqs(D, args.n_cal) + test_seqs(D, args.n_eval)
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
        s["k"], s["rec"], s["groups"] = {}, {}, {}
        for n, L in Ls.items():
            g = L.groups(cs)
            s["groups"][n] = g
            s["k"][f"linked_{n}"] = [s["k_single"][x[-1]] if len(x) == 1 else add([cs[i] for i in x]) for x in g]
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
        scores = {"per_commit": max(single),
                  "oracle_joint": max([orc] + [v for i, v in enumerate(single) if i not in s["attack_pos"]])}
        toks, ok = {"per_commit": sum(tok(k) for k in s["k_single"])}, True
        for m, ks in s["k"].items():
            v = [sc(k) for k in ks]
            if None in v:
                ok = False
                break
            scores[m] = max(v)
            toks[m] = sum(tok(k) for k in ks)
        if ok:
            rows.append(dict(sid=s["sid"], role=s["role"], N=N, chain=s["chain"], pattern=s.get("pattern"),
                             category=s["category"], variant=s["variant"], perturbed=False, scores=scores, tokens=toks,
                             rec={n: list(v) for n, v in s["rec"].items()},
                             nonsingleton={n: sum(len(g) > 1 for g in G) / len(G) for n, G in s["groups"].items()},
                             xfeat_recall={n: linking_recall(G, s["x_pos"])[0] for n, G in s["groups"].items()}))
    (ROOT / "results/r6_scores.json").write_text(json.dumps(dict(monitor=E2.MON, rows=rows, n_cal=args.n_cal,
                                                                 n_eval=args.n_eval), indent=1))
    print(f"rows={len(rows)}/{len(seqs)} -> r6_scores.json; ledger=${llm.spent:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="score")
    ap.add_argument("--n-cal", type=int, default=200)
    ap.add_argument("--n-eval", type=int, default=100)
    ap.add_argument("--estimate-only", action="store_true")
    main(ap.parse_args())
