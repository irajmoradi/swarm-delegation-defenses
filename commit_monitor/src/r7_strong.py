"""Round 7: stronger per-commit monitor control (openai/gpt-5.4-mini, same prompt) on the round-6 calibration
and test sequences (untuned; evaluated once). Includes an automatic score-direction probe for each model.

python src/r7_strong.py [--estimate-only] -> results/r7_strong_scores.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
import experiment6 as E6  # noqa: E402
from analysis import auc  # noqa: E402
from llm import LLM  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STRONG = "openai/gpt-5.4-mini"
EFFORT = sys.argv[sys.argv.index("--effort") + 1] if "--effort" in sys.argv else "minimal"


def sequences():
    D = E6.load6()
    seqs = E6.cal_seqs(D, 200) + E6.test_seqs(D, 100)
    L = json.loads((ROOT / "data/attacks/attacks_r6_llmadapt.json").read_text())
    lch = {}
    for c in L:
        lch.setdefault(c["chain"], []).append(c)
    for v in lch.values():
        v.sort(key=lambda c: c["idx"])
    D["achains42"] = lch
    seqs += [dict(s, variant="llm", sid=s["sid"].replace("r6adapt", "r6llm")) for s in E6.test_seqs(D, 0)
             if s["role"] == "attack" and s["variant"] == "adapt"]
    return D, seqs


def probe(llm, model, effort, D):
    att = [c for ch in ("A01", "A02", "A03", "A04", "A05", "A06") for c in D["chains42"][ch]][:12]
    ben = D["cal1"][:12]
    sc = lambda c: E2.parse_score(llm.chat(model, E2.single_msgs(c), max_tokens=E2.MAXTOK, effort=effort, tag="r7probe")) or 50
    a, b = [sc(c) for c in att], [sc(c) for c in ben]
    ok = float(np.mean(a)) > float(np.mean(b)) and auc(a, b) > 0.6
    print(f"PROBE {model}: attack mean {np.mean(a):.1f} benign mean {np.mean(b):.1f} AUC {auc(a, b):.2f} -> {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    llm = LLM()
    D, seqs = sequences()
    uniq = {}
    for s in seqs:
        for c in s["commits"]:
            uniq[LLM.key_of(STRONG, E2.single_msgs(c), E2.MAXTOK, EFFORT)] = c
    unc = [c for k, c in uniq.items() if k not in llm.cache]
    est = sum(sum(len(m["content"]) for m in E2.single_msgs(c)) / 3.6 * 0.75e-6 + 250 * 4.5e-6 for c in unc)
    print(f"unique commits={len(uniq)} uncached={len(unc)} est=${est:.3f} ledger=${llm.spent:.4f} cap=${llm.cap:.2f}")
    if "--estimate-only" in sys.argv:
        return
    assert probe(llm, "openai/gpt-5-mini", "minimal", D), "gpt-5-mini failed direction probe"
    assert probe(llm, STRONG, EFFORT, D), f"{STRONG} failed direction probe"
    jobs = {k: (STRONG, E2.single_msgs(c), "r7strong:1", E2.MAXTOK) for k, c in uniq.items()}
    jobs = {k: v for k, v in jobs.items()}
    # run_jobs uses effort=minimal; call directly for EFFORT
    from concurrent.futures import ThreadPoolExecutor
    out = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        def run(item):
            k, (m, msgs, tag, mt) = item
            try:
                return k, llm.chat(m, msgs, max_tokens=mt, effort=EFFORT, tag=tag)
            except Exception as e:  # noqa: BLE001
                print("call error:", type(e).__name__, str(e)[:150], flush=True)
                return k, None
        for i, (k, t) in enumerate(ex.map(run, jobs.items())):
            out[k] = t
            if (i + 1) % 100 == 0:
                print(f"  {i + 1}/{len(jobs)} ledger=${llm.spent:.4f}", flush=True)
    rows = []
    for s in seqs:
        v = [E2.parse_score(out.get(LLM.key_of(STRONG, E2.single_msgs(c), E2.MAXTOK, EFFORT)) or "") for c in s["commits"]]
        if any(x is None for x in v):
            v = [50 if x is None else x for x in v]
        toks = sum((llm.cache.get(LLM.key_of(STRONG, E2.single_msgs(c), E2.MAXTOK, EFFORT)) or {}).get("in_tok", 0) +
                   (llm.cache.get(LLM.key_of(STRONG, E2.single_msgs(c), E2.MAXTOK, EFFORT)) or {}).get("out_tok", 0)
                   for c in s["commits"])
        rows.append(dict(sid=s["sid"], role=s["role"], variant=s.get("variant"), chain=s.get("chain"),
                         pattern=s.get("pattern"), per_commit_strong=max(v), tokens_strong=toks,
                         attack_commit_scores=[v[i] for i in s["attack_pos"]] if s["role"] == "attack" else []))
    (ROOT / "results/r7_strong_scores.json").write_text(json.dumps(dict(model=STRONG, effort=EFFORT, rows=rows), indent=1))
    print(f"rows={len(rows)} unparsed={sum(1 for t in out.values() if t is None or E2.parse_score(t) is None)}; ledger=${llm.spent:.4f}")


if __name__ == "__main__":
    main()
