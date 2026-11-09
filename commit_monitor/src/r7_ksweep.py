"""Round 7 item 0.4 (partial): K=1 vs K=3. Each chain's 3 commits are merged into ONE commit (end state of the
chain applied in order to the base repo, rendered as one diff; stated task = the 3 tasks joined). In each round-6
original-attack test sequence the 3 attack commits are replaced by the merged commit (at the first attack position).
Scored per-commit with gpt-5-mini (and gpt-5.4-mini). K=6/9 need new hunks and are not built.
-> results/r7_k1_scores.json"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment2 as E2  # noqa: E402
import experiment6 as E6  # noqa: E402
import feature_gen as FG  # noqa: E402
import gen as G  # noqa: E402
from llm import LLM  # noqa: E402
from r7_validity import fuzzy_apply  # noqa: E402
from repo_gen import FILES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"per_commit": "openai/gpt-5-mini", "per_commit_strong": "openai/gpt-5.4-mini"}
llm = LLM()
D = E6.load6()
merged = {}
for ch, cs in D["chains42"].items():
    state = dict(FILES)
    for c in cs:
        ex = FG.apply_on_state(c["diff"], state)
        if ex:
            for f, (_, new) in ex.items():
                state[f] = new
        else:
            state, _ = fuzzy_apply(c["diff"], state)
    st = {f: (FILES.get(f, ""), state[f]) for f in state if state[f] != FILES.get(f, "")}
    merged[ch] = G.make_commit(f"{ch}K1", "attack", "; ".join(c["main_task"] for c in cs),
                               "; ".join(c["message"] for c in cs), G.render(st), chain=ch, pattern=cs[0]["pattern"])
seqs = [s for s in E6.test_seqs(D, 0) if s["role"] == "attack" and s["variant"] == "orig"]
jobs = {}
for s in seqs:
    for c in [c for i, c in enumerate(s["commits"]) if i not in s["attack_pos"]] + [merged[s["chain"]]]:
        for m, model in MODELS.items():
            msgs = E2.single_msgs(c)
            jobs[LLM.key_of(model, msgs, E2.MAXTOK, "minimal")] = (model, msgs)
unc = {k: v for k, v in jobs.items() if k not in llm.cache}
print(f"calls={len(jobs)} uncached={len(unc)} ledger=${llm.spent:.4f}")
if "--estimate-only" in sys.argv:
    sys.exit()
from concurrent.futures import ThreadPoolExecutor  # noqa: E402
with ThreadPoolExecutor(max_workers=6) as ex:
    out = dict(ex.map(lambda kv: (kv[0], llm.chat(kv[1][0], kv[1][1], max_tokens=E2.MAXTOK, effort="minimal",
                                                    tag="r7k1")), jobs.items()))
rows = []
for s in seqs:
    noise = [c for i, c in enumerate(s["commits"]) if i not in s["attack_pos"]]
    sc = {}
    for m, model in MODELS.items():
        f = lambda c: E2.parse_score(out[LLM.key_of(model, E2.single_msgs(c), E2.MAXTOK, "minimal")]) or 50
        sc[m] = max([f(c) for c in noise] + [f(merged[s["chain"]])])
        sc[m + "_merged_commit"] = f(merged[s["chain"]])
    rows.append(dict(sid=s["sid"].replace("r6orig", "r7k1"), chain=s["chain"], pattern=s["pattern"], role="attack",
                     variant="k1", scores=sc))
(ROOT / "results/r7_k1_scores.json").write_text(json.dumps(dict(rows=rows), indent=1))
print(f"K=1 rows={len(rows)}; ledger=${llm.spent:.4f}")
