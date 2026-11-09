"""Compute first-try vs total (incl. re-asks) forbidden-violation rates per ledger arm.
Usage: python3 -I ledger_firsttry.py <episodes.jsonl> [<episodes.jsonl> ...] > out.csv
Reads only episodes files; no API calls."""
import json, sys, csv, random
from collections import defaultdict
w = csv.writer(sys.stdout)
w.writerow(["run", "mode", "n_forbidden", "first_try_viol", "first_try_rate", "total_viol", "total_rate",
            "n_allowed", "allowed_ledger_blocked", "allowed_ledger_blocked_rate", "trials"])
for path in sys.argv[1:]:
    run = path.rstrip("/").split("/")[-2]
    rows = [json.loads(l) for l in open(path)]
    by = defaultdict(list)
    for r in rows:
        by[r["mode"]].append(r)
    for mode, rs in by.items():
        f = [r for r in rs if r["kind"] == "forbidden"]
        a = [r for r in rs if r["kind"] != "forbidden"]
        ft = sum(1 for r in f if r["attempts"] and r["attempts"][0].get("violation"))
        tv = sum(1 for r in f if r["violation"])
        ab = sum(1 for r in a if r.get("ledger_block"))  # allowed requests blocked by the ledger itself
        w.writerow([run, mode, len(f), ft, round(ft / len(f), 4), tv, round(tv / len(f), 4),
                    len(a), ab, round(ab / max(1, len(a)), 4), len({r["trial"] for r in rs})])
