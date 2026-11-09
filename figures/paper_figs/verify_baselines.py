"""Independent recount (P2 writer) of the no-retry baseline, paired tests and intent-screen pass-through.
Usage: python3 -I verify_baselines.py <episodes.jsonl> [...]   -> JSON lines on stdout. Reads episodes only; no API calls.
no-retry rule = the 'none' arm truncated to its first attempt (attempt 0 is identical across arms within a run)."""
import json, sys, random, itertools
from collections import defaultdict

def pct(xs, q):
    xs = sorted(xs); k = (len(xs) - 1) * q; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

for path in sys.argv[1:]:
    run = path.rstrip("/").split("/")[-2]
    E = [json.loads(l) for l in open(path)]
    kind_forb = lambda r: r["kind"] == "forbidden"
    out = {"run": run, "arms": {}}
    modes = sorted({r["mode"] for r in E})
    for m in modes:
        F = [r for r in E if r["mode"] == m and kind_forb(r)]
        A = [r for r in E if r["mode"] == m and not kind_forb(r)]
        a = {"n_forb": len(F), "viol": sum(r["violation"] for r in F),
             "first_try_viol": sum(1 for r in F if r["attempts"] and r["attempts"][0]["violation"]),
             "n_allowed": len(A), "allowed_success": sum(r["success"] for r in A),
             "allowed_first_attempt_success": sum(1 for r in A if r["attempts"] and r["attempts"][0]["success"]),
             "allowed_ledger_block": sum(1 for r in A if r.get("ledger_block"))}
        if m == "intent":
            passed = [r for r in F if not r.get("ledger_block")]
            a["intent_passed_forbidden"] = len(passed)
            a["intent_passed_and_violated"] = sum(r["violation"] for r in passed)
            a["intent_screen_errors"] = sum(1 for r in F + A if r.get("screen_error"))
        out["arms"][m] = a
    # paired contrasts vs none, and exact vs the no-retry rule
    F = [r for r in E if kind_forb(r)]
    trials = sorted({r["trial"] for r in F}); intents = sorted({r["intent_id"] for r in F})
    def cell(m, key, val, metric):
        rs = [r for r in F if r["mode"] == m and r[key] == val]
        if metric == "viol": return sum(r["violation"] for r in rs) / len(rs)
        return sum(1 for r in rs if r["attempts"] and r["attempts"][0]["violation"]) / len(rs)
    contrasts = [(m, "none", "viol") for m in modes if m != "none"] + [("exact", "none", "first")]
    out["contrasts"] = {}
    for m, base, bm in contrasts:
        if m not in modes: continue
        name = f"{m}-{'none' if bm == 'viol' else 'noretry'}"
        d = [cell(m, "trial", t, "viol") - cell(base, "trial", t, bm) for t in trials]
        obs = sum(d) / len(d)
        hits = sum(1 for s in itertools.product((1, -1), repeat=len(d))
                   if abs(sum(x * y for x, y in zip(s, d))) >= abs(sum(d)) - 1e-12)
        di = {i: cell(m, "intent_id", i, "viol") - cell(base, "intent_id", i, bm) for i in intents}
        rng = random.Random(20261108); bs = []
        for _ in range(10000):
            smp = [rng.choice(intents) for _ in intents]; bs.append(sum(di[i] for i in smp) / len(smp))
        out["contrasts"][name] = {"diff_pts": round(100 * obs, 2), "per_trial": [round(100 * x, 1) for x in d],
                                  "n_neg_trials": sum(x < 0 for x in d), "signflip_p": f"{hits}/{2**len(d)}",
                                  "intent_cluster_ci95": [round(100 * pct(bs, .025), 1), round(100 * pct(bs, .975), 1)],
                                  "n_intents": len(intents)}
    print(json.dumps(out))
