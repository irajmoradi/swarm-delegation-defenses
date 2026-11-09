"""Round 4: realistic benign baseline (multi-commit features), hybrid linker, 2-hop dilution fixes,
>=100 held-out benign sequences at N=10, light rule-based adaptive attacker. Same monitor prompt as rounds 2-3.

python src/experiment4.py --stage effects                 # effect summaries for feature + adaptive commits
python src/experiment4.py --stage metrics                 # free: dependency gap, linkage, recall, hop-fix choice
python src/experiment4.py --stage score --linkers ... [--estimate-only]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
from experiment import rng_for  # noqa: E402
from linker import linking_recall  # noqa: E402
from linkers2 import TextLinker, _Base  # noqa: E402
from linkers3 import DepLinker, DepFeatures, EffectLinker, Hop2, sensitive  # noqa: E402
from llm import LLM  # noqa: E402
from repo_gen import FILES  # noqa: E402
import gen as G  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EFF4 = ROOT / "results/r4_effects.json"
SEED = 41
N = 10
CAL_FEATS = {"F02", "F05", "F08", "F11", "F14", "F17"}


# ---------------- adaptive attacker: WITHHELD in the public release (dual-use) ----------------
# The original rule-based dependency-hiding rewrite (rounds 4-6) is described at a high level in
# PILOT_RESULTS.md ("Light rule-based adaptive attacker"). Its implementation is not released.
def adaptive(chain_commits: list[dict]) -> list[dict]:
    """WITHHELD (dual-use): rule-based rewrite of attack commits. Not included in this release."""
    raise NotImplementedError("adaptive attacker withheld from the public release; see README 'Withheld material'")


def load4():
    benign, attacks, pert, cal1, test1, chains, pchains = E2.load()
    feats = json.loads((ROOT / "data/benign/features.json").read_text())
    by_f = {}
    for c in feats:
        by_f.setdefault(c["feature"], []).append(c)
    for v in by_f.values():
        v.sort(key=lambda c: c["step"])
    multi = {k: v for k, v in by_f.items() if len(v) >= 2}
    cal_f = [v for k, v in sorted(multi.items()) if k in CAL_FEATS]
    test_f = [v for k, v in sorted(multi.items()) if k not in CAL_FEATS]
    achains = {ch: adaptive(cs) for ch, cs in chains.items()}
    return dict(benign=benign, feats=feats, cal1=cal1, test1=test1, cal_f=cal_f, test_f=test_f,
                chains=chains, pchains=pchains, achains=achains)


def build_seqs(D, n_cal, n_eval, variants=("orig", "pert", "adapt")):
    """N=10: every sequence contains one benign multi-commit feature (in order) + singles (+ K attack commits)."""
    seqs = []

    def fill(r, singles, feats, n_noise, extra):
        f = r.choice(feats)
        n_single = n_noise - len(f)
        sing = r.sample(singles, n_single)
        L = n_noise + len(extra)
        pos_extra = sorted(r.sample(range(L), len(extra)))
        rest = [p for p in range(L) if p not in pos_extra]
        pos_f = sorted(r.sample(rest, len(f)))
        seq, ie, iff, iss = [None] * L, iter(extra), iter(f), iter(sing)
        for p in range(L):
            seq[p] = next(ie) if p in pos_extra else next(iff) if p in pos_f else next(iss)
        return seq, pos_extra, pos_f

    for ch, cs in D["chains"].items():
        for a in range(3):
            r = rng_for("r4att", ch, a, SEED)
            seq, pos, pos_f = fill(r, D["test1"], D["test_f"], N, cs)
            for v in variants:
                src = {"orig": D["chains"], "pert": D["pchains"], "adapt": D["achains"]}[v][ch]
                s2 = [src[pos.index(p)] if p in pos else c for p, c in enumerate(seq)]
                seqs.append(dict(sid=f"r4{v}_{ch}_a{a}", role="attack", N=N, chain=ch, category=cs[0]["category"],
                                 perturbed=(v != "orig"), variant=v, commits=s2, attack_pos=pos, feat_pos=pos_f))
    for role, singles, feats, n in (("cal", D["cal1"], D["cal_f"], n_cal), ("benign_eval", D["test1"], D["test_f"], n_eval)):
        for s in range(n):
            r = rng_for("r4" + role, s, SEED)
            seq, _, pos_f = fill(r, singles, feats, N + 3, [])
            fake = sorted(rng_for("r4fake", role, s).sample(range(N + 3), 3))
            seqs.append(dict(sid=f"r4{role}_{s}", role=role, N=N, chain=None, category=None, perturbed=False,
                             variant="benign", commits=seq, attack_pos=fake, feat_pos=pos_f))
    return seqs


# ---------------- linkers ----------------
class HybridLinker(_Base):
    """dependency + effect-summary: score = dep/tau_dep + w * effect/tau_eff (w=1), tau at q90."""
    name = "hybrid"

    def __init__(self, fit, dep, eff, w=1.0):
        self.dep, self.eff, self.w = dep, eff, w
        self._set_tau(fit)

    def pair_score(self, a, b):
        return self.dep.pair_score(a, b) / self.dep.tau + self.w * self.eff.pair_score(a, b) / self.eff.tau


class Hop2Cap:
    """2-hop with dilution control. mode 'top1': each direct link contributes only its single strongest
    own link; cap total group size. mode 'sens': expand only through sensitivity-tagged commits."""

    def __init__(self, inner, mode="top1", cap=4):
        self.inner, self.mode, self.cap, self.tau = inner, mode, cap, inner.tau
        self.name = f"{inner.name}_hop2{mode}"
        self._s = {}

    def _sens(self, c):
        if c["id"] not in self._s:
            self._s[c["id"]] = sensitive(c)
        return self._s[c["id"]]

    def groups(self, seq):
        base = self.inner.groups(seq)
        out = []
        for j, g in enumerate(base):
            s = set(g)
            for i in g:
                if i == j:
                    continue
                if self.mode == "sens" and not (self._sens(seq[i]) and self._sens(seq[j])):
                    continue
                cand = [x for x in base[i] if x != i and x not in s]
                if self.mode == "top1" and cand:
                    cand = [max(cand, key=lambda x: self.inner.pair_score(seq[i], seq[x]))]
                if self.mode == "sens":
                    cand = [x for x in cand if self._sens(seq[x])]
                s |= set(cand)
            s = sorted(s)
            if len(s) > self.cap:
                s = sorted([x for x in s if x != j][-(self.cap - 1):] + [j])
            out.append(s)
        return out


def make_linkers(D, names):
    effects = json.loads(EFF4.read_text()) if EFF4.exists() else {}
    fit = D["cal1"] + [c for f in D["cal_f"] for c in f]
    base = {"text": TextLinker(fit), "dep": DepLinker(fit, FILES)}
    if effects:
        base["effect"] = EffectLinker(fit, effects)
        base["hybrid"] = HybridLinker(fit, base["dep"], base["effect"])
    out = {}
    for n in names:
        if n in base:
            out[n] = base[n]
        elif n.endswith("_hop2"):
            out[n] = Hop2(base[n[:-5]])
        elif n.endswith("_hop2top1"):
            out[n] = Hop2Cap(base[n[:-9]], "top1", 4)
        elif n.endswith("_hop2sens"):
            out[n] = Hop2Cap(base[n[:-9]], "sens", 6)
    return out


def stage_effects(args, llm):
    D = load4()
    cs = D["feats"] + [c for v in D["achains"].values() for c in v]
    old = json.loads((ROOT / "results/r3_effects.json").read_text())
    jobs, ids = {}, {}
    for c in cs:
        m = EffectLinker.msgs(c)
        k = LLM.key_of(EffectLinker.model, m, 600, "minimal")
        jobs[k] = (EffectLinker.model, m, "effect", 600)
        ids[c["id"]] = k
    out = E2.run_jobs(llm, jobs, args.estimate_only, out_tokens=60)
    if out is None:
        return
    for i, k in ids.items():
        t = out.get(k, "").strip()
        old[i] = t.splitlines()[0] if t else ""
    EFF4.write_text(json.dumps(old, indent=1))
    print(f"effects total {len(old)}; ledger=${llm.spent:.4f}")


def stage_metrics(args, llm):
    D = load4()
    dep = DepLinker(D["cal1"] + [c for f in D["cal_f"] for c in f], FILES)
    # dependency gap: attack pairs vs benign feature intra pairs vs benign cross-task pairs
    strong = lambda a, b: any(dep.edges(a, b)[t] for t in ("defuse", "key"))
    anye = lambda a, b: any(dep.edges(a, b)[t] for t in ("defuse", "key", "literal", "into"))
    gap = {}
    for name, pairs in (
            ("attack (orig)", [(cs[i], cs[j]) for cs in D["chains"].values() for i in range(3) for j in range(i + 1, 3)]),
            ("attack (adaptive)", [(cs[i], cs[j]) for cs in D["achains"].values() for i in range(3) for j in range(i + 1, 3)]),
            ("benign feature, same feature", [(f[i], f[j]) for f in D["cal_f"] + D["test_f"] for i in range(len(f)) for j in range(i + 1, len(f))]),
            ("benign singles, cross-task", [(a, b) for x, a in enumerate(D["test1"]) for b in D["test1"][x + 1:] if a["id"][:3] != b["id"][:3]])):
        gap[name] = dict(n=len(pairs), strong=sum(strong(a, b) for a, b in pairs) / len(pairs),
                         any=sum(anye(a, b) for a, b in pairs) / len(pairs))
        print(f"dep-edge rate {name:32s} n={len(pairs):5d} strong={gap[name]['strong']:.3f} any={gap[name]['any']:.3f}")
    names = ["text", "dep", "effect", "hybrid", "dep_hop2", "hybrid_hop2", "dep_hop2top1", "hybrid_hop2top1",
             "dep_hop2sens", "hybrid_hop2sens"]
    Ls = make_linkers(D, names)
    seqs = build_seqs(D, 200, 100)
    res = {}
    for n, L in Ls.items():
        r = dict(tau=L.tau)
        for v in ("orig", "pert", "adapt"):
            att = [s for s in seqs if s["role"] == "attack" and s["variant"] == v]
            rec = [linking_recall(L.groups(s["commits"]), s["attack_pos"]) for s in att]
            r[f"pair_{v}"] = sum(x for x, _ in rec) / len(rec)
            r[f"full_{v}"] = sum(y for _, y in rec) / len(rec)
        att = [s for s in seqs if s["role"] == "attack" and s["variant"] == "orig"]
        pulled = nb = 0
        for s in att:
            Gs = L.groups(s["commits"]); ap = set(s["attack_pos"]); inn = set()
            for g in Gs:
                if set(g) & ap:
                    inn |= set(g) - ap
            pulled += len(inn); nb += len(s["commits"]) - 3
        cal = [s for s in seqs if s["role"] == "cal"]
        gs = [L.groups(s["commits"]) for s in cal]
        r["benign_linked"] = sum(sum(len(g) > 1 for g in Gq) / len(Gq) for Gq in gs) / len(gs)
        r["benign_group_mean"] = sum(sum(len(g) for g in Gq) / len(Gq) for Gq in gs) / len(gs)
        r["benign_group_max"] = max(len(g) for Gq in gs for g in Gq)
        r["pulled_into_attack_groups"] = pulled / nb
        # benign feature recall (how often a benign feature's own commits are grouped together)
        fr = [linking_recall(L.groups(s["commits"]), s["feat_pos"])[0] for s in cal]
        r["benign_feature_pair_recall"] = sum(fr) / len(fr)
        res[n] = r
        print(f"{n:16s}", {k: round(v, 3) for k, v in r.items()})
    (ROOT / "results/r4_metrics_free.json").write_text(json.dumps(dict(dep_gap=gap, linkers=res), indent=1))


def stage_score(args, llm):
    D = load4()
    Ls = make_linkers(D, args.linkers)
    seqs = build_seqs(D, args.n_cal, args.n_eval)
    jobs = {}

    def add(cs):
        m = E2.single_msgs(cs[0]) if len(cs) == 1 else E2.joint_msgs(cs)
        k = LLM.key_of(E2.MON, m, E2.MAXTOK, "minimal")
        jobs.setdefault(k, (E2.MON, m, f"r2mon:{len(cs)}", E2.MAXTOK))
        return k

    for s in seqs:
        cs = s["commits"]
        s["k_single"] = [add([c]) for c in cs]
        s["k_oracle"] = add([cs[i] for i in s["attack_pos"]]) if args.oracle else None
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
        if None in single:
            continue
        scores = {"per_commit": max(single)}
        toks = {"per_commit": sum(tok(k) for k in s["k_single"])}
        if args.oracle:
            orc = sc(s["k_oracle"])
            if orc is None:
                continue
            scores["oracle_joint"] = max([orc] + [v for i, v in enumerate(single) if i not in s["attack_pos"]])
        ok = True
        for n in Ls:
            lv = [sc(k) for k in s["k_linked"][n]]
            if None in lv:
                ok = False
                break
            scores[f"linked_{n}"] = max(lv)
            toks[f"linked_{n}"] = sum(tok(k) for k in s["k_linked"][n])
        if ok:
            rows.append(dict(sid=s["sid"], role=s["role"], N=N, chain=s["chain"], category=s["category"],
                             perturbed=s["perturbed"], variant=s["variant"], scores=scores, tokens=toks,
                             rec={n: list(v) for n, v in s["rec"].items()},
                             nonsingleton={n: sum(len(g) > 1 for g in s["groups"][n]) / len(s["groups"][n]) for n in Ls}))
    path = ROOT / f"results/r4_scores{args.tag}.json"
    path.write_text(json.dumps(dict(monitor=E2.MON, linkers=list(Ls), taus={n: L.tau for n, L in Ls.items()},
                                    n_cal=args.n_cal, n_eval=args.n_eval, rows=rows,
                                    n_parse_fail=sum(1 for t in out.values() if E2.parse_score(t) is None)), indent=1))
    print(f"rows={len(rows)}/{len(seqs)} -> {path.name}; ledger=${llm.spent:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["effects", "metrics", "score"], required=True)
    ap.add_argument("--n-cal", type=int, default=200)
    ap.add_argument("--n-eval", type=int, default=100)
    ap.add_argument("--linkers", nargs="+", default=["dep", "hybrid_hop2top1"])
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--tag", default="")
    ap.add_argument("--estimate-only", action="store_true")
    a = ap.parse_args()
    llm = LLM()
    {"effects": stage_effects, "metrics": stage_metrics, "score": stage_score}[a.stage](a, llm)
