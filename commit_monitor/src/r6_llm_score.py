"""Score the LLM-adaptive chain variant on the SAME round-6 test arrangements (attack seqs only; calibration and
held-out benign rows are reused from r6_scores.json). Also adds effect summaries for the rewritten commits."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
import experiment4 as E4  # noqa: E402
import experiment5 as E5  # noqa: E402
import experiment6 as E6  # noqa: E402
from linker import linking_recall  # noqa: E402
from linkers3 import EffectLinker  # noqa: E402
from llm import LLM  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
llm = LLM()
D = E6.load6()
L = json.loads((ROOT / "data/attacks/attacks_r6_llmadapt.json").read_text())
lch = {}
for c in L:
    lch.setdefault(c["chain"], []).append(c)
for v in lch.values():
    v.sort(key=lambda c: c["idx"])
# effect summaries for rewritten commits
eff = json.loads(E4.EFF4.read_text())
jobs, ids = {}, {}
for c in L:
    if c["id"] not in eff:
        m = EffectLinker.msgs(c)
        k = LLM.key_of(EffectLinker.model, m, 600, "minimal")
        jobs[k] = (EffectLinker.model, m, "effect", 600)
        ids[c["id"]] = k
out = E2.run_jobs(llm, jobs, False, out_tokens=60) if jobs else {}
for i, k in ids.items():
    t = out.get(k, "").strip()
    eff[i] = t.splitlines()[0] if t else ""
E4.EFF4.write_text(json.dumps(eff, indent=1))
D["achains42"] = lch
seqs = [dict(s, variant="llm", sid=s["sid"].replace("r6adapt", "r6llm")) for s in E6.test_seqs(D, 0)
        if s["role"] == "attack" and s["variant"] == "adapt"]
calF = [c for k, f in D["allf"].items() if k in E5.FRESH_CAL_F for c in f]
calX = [c for k, f in D["x"].items() if k in E5.FRESH_CAL_X for c in f]
Ls = E5.make_linkers5(D, ["boundary_union", "dep"], D["cal1"] + calF + calX)
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
    for n, Lk in Ls.items():
        g = Lk.groups(cs)
        s["groups"][n] = g
        s["k"][f"linked_{n}"] = [s["k_single"][x[-1]] if len(x) == 1 else add([cs[i] for i in x]) for x in g]
        s["rec"][n] = linking_recall(g, s["attack_pos"])
out = E2.run_jobs(llm, jobs, "--estimate-only" in sys.argv)
if out is None:
    sys.exit()
sc = lambda k: (50 if E2.parse_score(out[k]) is None else E2.parse_score(out[k])) if k in out else None
rows = []
for s in seqs:
    single = [sc(k) for k in s["k_single"]]
    orc = sc(s["k_oracle"])
    vals = {m: [sc(k) for k in ks] for m, ks in s["k"].items()}
    if None in single or orc is None or any(None in v for v in vals.values()):
        continue
    scores = {"per_commit": max(single), "oracle_joint": max([orc] + [v for i, v in enumerate(single) if i not in s["attack_pos"]])}
    scores.update({m: max(v) for m, v in vals.items()})
    rows.append(dict(sid=s["sid"], role="attack", N=10, chain=s["chain"], pattern=s["pattern"], category=s["category"],
                     variant="llm", perturbed=False, scores=scores, tokens={},
                     rec={n: list(v) for n, v in s["rec"].items()},
                     nonsingleton={n: sum(len(g) > 1 for g in G) / len(G) for n, G in s["groups"].items()}))
(ROOT / "results/r6_llm_scores.json").write_text(json.dumps(dict(rows=rows), indent=1))
print(f"llm-adaptive rows={len(rows)}/{len(seqs)}; ledger=${llm.spent:.4f}")
