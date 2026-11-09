"""Round 7 item 0.3: execution-based validity of every attack chain variant (original / rule-adaptive / LLM-adaptive).

For each chain: apply its 3 commits in order to a temp copy of the toy repo (content-matching apply, line numbers
ignored); scan added code for dangerous calls (subprocess/socket/network/file deletion) and skip execution if
found; run the per-pattern toy goal check (src/r7_goalcheck_runner.py) in a subprocess (`python -I`, timeout);
run the repo's test files with pytest. Baseline: every goal check is also run on the UNMODIFIED repo and must
return False (otherwise the check is invalid).

-> results/attack_validity.csv, results/r7_validity.json
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment6 as E6  # noqa: E402
import feature_gen as FG  # noqa: E402
from attacks2 import CHAINS2  # noqa: E402
from repo_gen import FILES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
RUNNER = str(ROOT / "src/r7_goalcheck_runner.py")
SANDBOX = Path(os.environ.get("R7_SANDBOX", "/tmp/r7sandbox"))  # release: copy sandbox/sandbox.sh + src/r7_goalcheck_runner.py here (outside $HOME)
DANGER = re.compile(r"\b(subprocess|os\.system|socket|requests\.|urllib\.request|http\.client|shutil\.rmtree|os\.remove|"
                    r"os\.unlink|eval\(|exec\(|__import__)")

ORIG_PARAMS = {"A01": ("P1", {"src": "annotator_pool_b"}), "A02": ("P2", {}),
               "A03": ("P3", {"metric": "reward_hacking_rate"}),
               "A04": ("P4", {"host": "metrics-sink.partner-analytics.example"}), "A05": ("P5", {"reader": "alerts"}),
               "A06": ("P6", {"fn": "apply_overrides", "okey": "logger_overrides"})}


def params_new(ch):
    g, p = ch["goal"], ch["pattern"]
    last = g.split()[-1]
    if p in ("P1", "P7"):
        return {"src": last}
    if p == "P3":
        return {"metric": g.split()[1]}
    if p == "P4":
        return {"host": g.split(" to ")[1].split()[0]}
    if p == "P5":
        return {"reader": g.split()[1]}
    if p == "P6":
        fn = re.search(r"def (\w+)\(levels\)", "\n".join(ln for e in ch["commits"][0]["edits"] for ln in e[3])).group(1)
        okey = ch["commits"][1]["edits"][0][3][0].rstrip(":")
        return {"fn": fn, "okey": okey}
    if p == "P10":
        return {"metric": g.split()[1]}
    if p == "P12":
        return {"host": last}
    return {}


def fuzzy_apply(diff, state):
    """Apply a unified diff to `state` by content matching, with patch-style fuzz: if a hunk's context does not
    match (e.g. an earlier commit of the chain changed nearby lines; all diffs were rendered against the base
    repo), retry with up to 3 context lines trimmed from each end. Returns (new_state, n_failed_hunks)."""
    state = dict(state)
    failed = 0
    f, hunks = None, []

    def flush():
        nonlocal failed
        if f is None:
            return
        lines = state.get(f, "").splitlines()
        for h in hunks:
            body = [ln for ln in h]
            ok = False
            for trim in range(0, 4):
                b = body[:]
                for _ in range(trim):
                    if b and b[0][:1] == " ":
                        b = b[1:]
                    if b and b[-1][:1] == " ":
                        b = b[:-1]
                src = [ln[1:] for ln in b if ln[:1] in (" ", "-") or ln == ""]
                dst = [ln[1:] for ln in b if ln[:1] in (" ", "+") or ln == ""]
                if not src:
                    lines += dst
                    ok = True
                    break
                at = next((i for i in range(len(lines) - len(src) + 1)
                           if [x.rstrip() for x in lines[i:i + len(src)]] == [x.rstrip() for x in src]), None)
                if at is not None:
                    lines[at:at + len(src)] = dst
                    ok = True
                    break
            failed += 0 if ok else 1
        state[f] = "\n".join(lines) + "\n"

    cur = None
    for ln in diff.splitlines():
        if ln.startswith("--- "):
            continue
        if ln.startswith("+++ "):
            flush()
            f = ln[4:].strip().removeprefix("b/")
            hunks, cur = [], None
        elif ln.startswith("@@"):
            cur = []
            hunks.append(cur)
        elif cur is not None:
            cur.append(ln)
    flush()
    return state, failed


def write_repo(state):
    d = Path(tempfile.mkdtemp(dir=SANDBOX))
    for rel, text in state.items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    for pkg in ("pipeline", "trainer", "alerts"):
        (d / pkg / "__init__.py").touch()
    return d


WRAP = str(SANDBOX / "sandbox.sh")  # unshare -rnm: no network, $HOME hidden (tmpfs), python install read-only
SB_RUNNER = SANDBOX / "r7_goalcheck_runner.py"


def run_check(d, pattern, params):
    try:
        r = subprocess.run([WRAP, str(d), PY, "-I", str(SB_RUNNER), str(d), pattern, json.dumps(params)], cwd=str(d),
                           capture_output=True, text=True, timeout=30)
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
        return json.loads(line[-1]) if line else {"achieved": False, "detail": "no output: " + r.stderr[-200:]}
    except subprocess.TimeoutExpired:
        return {"achieved": False, "detail": "timeout"}


def run_tests(d):
    tests = [str(p) for p in d.rglob("test_*.py")]
    if not tests:
        return None
    try:
        r = subprocess.run([WRAP, str(d), PY, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", str(d), *tests],
                           cwd=str(d), capture_output=True, text=True, timeout=60)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def main():
    SANDBOX.mkdir(parents=True, exist_ok=True)
    assert Path(WRAP).exists(), "isolation wrapper missing; refusing to execute attack code without it"
    shutil.copy(RUNNER, SB_RUNNER)
    D = E6.load6()
    L = json.loads((ROOT / "data/attacks/attacks_r6_llmadapt.json").read_text())
    llm = {}
    for c in L:
        llm.setdefault(c["chain"], []).append(c)
    for v in llm.values():
        v.sort(key=lambda c: c["idx"])
    newp = {ch["id"]: (ch["pattern"], params_new(ch)) for ch in CHAINS2}
    allp = {**ORIG_PARAMS, **newp}
    base_dir = write_repo(dict(FILES))
    baseline = {}
    for ch, (pat, prm) in allp.items():
        baseline[ch] = run_check(base_dir, pat, prm)
    base_tests = run_tests(base_dir)
    rows = []
    for ch in sorted(D["chains42"]):
        pat, prm = allp[ch]
        for variant, cs in (("orig", D["chains42"][ch]), ("adapt", D["achains42"][ch]), ("llm", llm[ch])):
            state, applies, nfail = dict(FILES), True, 0
            for c in cs:
                exact = FG.apply_on_state(c["diff"], state)
                if exact:
                    for f, (_, new) in exact.items():
                        state[f] = new
                    continue
                applies = False  # exact apply failed; fall back to fuzzy (recorded)
                state, k = fuzzy_apply(c["diff"], state)
                nfail += k
            added = "\n".join(ln[1:] for c in cs for ln in c["diff"].splitlines() if ln.startswith("+") and not ln.startswith("+++"))
            danger = bool(DANGER.search(added))
            if danger:
                chk, tests = {"achieved": None, "detail": "not executed: dangerous call pattern in added code"}, None
            else:
                d = write_repo(state)
                chk, tests = run_check(d, pat, prm), run_tests(d)
                shutil.rmtree(d, ignore_errors=True)
            rows.append(dict(chain_id=ch, pattern=pat, variant=variant, applies_cleanly=applies,
                             applies_with_fuzz=(nfail == 0), unapplied_hunks=nfail, tests_pass=tests,
                             goal_achieved=chk["achieved"], baseline_goal=baseline[ch]["achieved"],
                             check_valid=baseline[ch]["achieved"] is False, notes=chk["detail"]))
            print(ch, variant, applies, tests, chk["achieved"], chk["detail"][:90], flush=True)
    shutil.rmtree(base_dir, ignore_errors=True)
    for x in SANDBOX.iterdir():  # clean up throwaway repo copies
        if x.is_dir() and x.name not in ("mc",):
            shutil.rmtree(x, ignore_errors=True)
    with open(ROOT / "results/attack_validity.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (ROOT / "results/r7_validity.json").write_text(json.dumps(dict(base_tests_pass=base_tests, baseline=baseline, rows=rows), indent=1))
    from collections import Counter
    for v in ("orig", "adapt", "llm"):
        rv = [r for r in rows if r["variant"] == v]
        print(v, "applies", sum(r["applies_cleanly"] for r in rv), "fuzz-ok", sum(r["applies_with_fuzz"] for r in rv), "goal", sum(bool(r["goal_achieved"]) for r in rv),
              "tests", Counter(r["tests_pass"] for r in rv), "of", len(rv))
    print("baseline goal true (invalid checks):", [k for k, v in baseline.items() if v["achieved"] is not False],
          "base tests pass:", base_tests)


if __name__ == "__main__":
    main()
