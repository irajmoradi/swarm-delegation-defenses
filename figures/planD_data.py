"""Single source of truth for the Plan D figures (planD_method.py, planD_method_lw.py).

Every plotted or captioned number is READ at runtime from the run's analysis outputs (read-only) and ASSERTED
against the number printed in the P2 draft; any mismatch stops the render. Caption files are rendered from the
same loaded values via `caption_neurips()` / `caption_lw()`, so figures and captions cannot drift.

Sources (read-only):
  ADAPTIVE  paper_p2/figs/adaptive_primeintellect.csv  (= planD runs/...-v2-adaptive-primeintellect-fp4/analysis_
            adaptive/adaptive.csv, same md5): `violation`, `allowed_blocked`, `n_forbidden`, `n_allowed`
  SPLIT     planD runs/20261108T203321606463Z-v2-ledger3-primeintellect-fp4/analysis_split/split.csv:
            semantic `violation` (7.64%), semantic `false_block` (40.97%), none `first_try` (= never re-ask, 16.9%)
  P2        paper_p2/P2_DRAFT.md: the section 4.6 table, "host B 7.6% vs 10.0%" (4.3),
            "41.0% vs 2.1%" (4.3), "on host B, 16.9% (1.4%)" (4.2), "99-100% in every arm" (4.6)
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # release repo root
ADAPTIVE = ROOT / "figures/paper_figs/adaptive_primeintellect.csv"
SPLIT = ROOT / "planD/runs/20261108T203321606463Z-v2-ledger3-primeintellect-fp4/analysis_split/split.csv"
P2 = ROOT / "paper/P2_DRAFT.md"
TOL = 0.05                                   # percentage points

DEFENSES = ["none", "exact", "semantic", "intent"]           # bar groups, left to right
COORDS = ["scripted", "unprompted", "explicit", "bare"]       # series; bare = reason hidden


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _pct(x: str) -> float:
    return 100.0 * float(x)


def load() -> dict:
    """All numbers the figures use, in percent, plus n per bar. Raises AssertionError on any P2 mismatch."""
    rows = _read_csv(ADAPTIVE)
    viol, blocked, n_forb, n_allow = {}, {}, {}, {}
    for r in rows:
        if r["coordinator"] in COORDS and r["violation"]:
            key = (r["defense"], r["coordinator"])
            viol[key] = _pct(r["violation"])
            blocked[key] = _pct(r["allowed_blocked"])
            n_forb[key] = int(r["n_forbidden"])
            n_allow[key] = int(r["n_allowed"])
    split = {(r["arm"], r["group"]): r for r in _read_csv(SPLIT)}
    sem = split[("semantic", "all forbidden")]
    sem_allowed = split[("semantic", "allowed requests")]
    none_all = split[("none", "all forbidden")]
    d = {
        "viol": viol, "blocked": blocked, "n_forb": n_forb, "n_allow": n_allow,
        "sem_viol": _pct(sem["violation"]), "sem_n": int(sem["n"]),
        "sem_false_block": _pct(sem_allowed["false_block"]), "sem_allow_n": int(sem_allowed["n"]),
        "never_reask": _pct(none_all["first_try"]), "never_reask_n": int(none_all["n"]),
    }
    _check_against_p2(d)
    return d


def _check_against_p2(d: dict) -> None:
    if not P2.exists():  # the paper text is not part of this release; skip the cross-check
        return
    text = P2.read_text()
    # section 4.6 table: | defense | scripted | unprompted | explicit | reason hidden |  (integers as printed)
    names = {"no defense": "none", "exact ledger": "exact", "intent screen": "intent"}
    found = 0
    for line in text.splitlines():
        m = re.match(r"\|\s*(no defense|exact ledger|intent screen)\s*\|(.*)\|\s*$", line)
        if not m or line.count("|") != 6:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if not re.match(r"^\d+$", cells[0]):
            continue                                            # another table with the same row names
        found += 1
        for coord, cell in zip(COORDS, cells):
            key = (names[m.group(1)], coord)
            if cell.startswith("—"):
                assert key not in d["viol"], f"P2 says {key} not run, but the CSV has it"
                continue
            printed = int(re.match(r"(\d+)", cell).group(1))
            got = d["viol"][key]
            assert round(got) == printed, f"P2 4.6 {key}: printed {printed}, CSV {got:.2f}"
    assert found == 3, f"P2 4.6 table: found {found} of 3 rows"
    # section 4.3 (host B four-arm run, all 6 trials)
    m = re.search(r"host B (\d+\.\d)% vs (\d+\.\d)%", text)
    assert m and abs(float(m.group(1)) - d["sem_viol"]) <= TOL, f"P2 4.3 text similarity {m and m.group(1)}"
    m = re.search(r"\(42\.1% vs 1\.6%; (\d+\.\d)% vs (\d+\.\d)%\)", text)
    assert m and abs(float(m.group(1)) - d["sem_false_block"]) <= TOL, f"P2 4.3 false block {m and m.group(1)}"
    # section 4.2 (never re-ask on host B, all 6 trials)
    m = re.search(r"on host B, (\d+\.\d)% \(", text)
    assert m and abs(float(m.group(1)) - d["never_reask"]) <= TOL, f"P2 4.2 never re-ask {m and m.group(1)}"
    # section 4.6: allowed work completed 99-100% in every arm -> blocked at most 1.5%
    assert re.search(r"Allowed work completed stayed at 99–100% in every arm", text)
    assert max(d["blocked"].values()) <= 1.5, "adaptive allowed_blocked exceeds P2's 99-100% completed"
    # host-A headline numbers used in the NeurIPS caption (P2 4.1 / 4.2 / 4.3, quoted, not plotted)
    for s in ("**25.5%**", "**14.8%**", "**9.3%**"):
        assert s in text, f"P2 headline {s} missing"
    assert re.search(r"\(38\.2% vs 0\.7%\)", text) and "42.1%" in text, "P2 4.3 38-42% range"
    ns = set(d["n_forb"].values())
    assert ns == {216} and d["sem_n"] == 432 and d["never_reask_n"] == 432, f"n per bar {ns}"


# ---------------------------------------------------------------- plot tables
def tables(d: dict) -> dict:
    """Per series k (0 scripted, 1 unprompted, 2 explicit, 3 reason hidden) and group g (none, exact, text
    similarity, intent): violation %, allowed-blocked %, n (None = not run). Scripted text similarity comes from
    the six-trial four-arm run (SPLIT); everything else from ADAPTIVE."""
    pct, blk, n = {}, {}, {}
    for k, c in enumerate(COORDS):
        pct[k], blk[k], n[k] = [], [], []
        for g in DEFENSES:
            if g == "semantic":
                ok = c == "scripted"
                pct[k].append(d["sem_viol"] if ok else None)
                blk[k].append(d["sem_false_block"] if ok else None)
                n[k].append(d["sem_n"] if ok else None)
            else:
                key = (g, c)
                pct[k].append(d["viol"].get(key))
                blk[k].append(d["blocked"].get(key))
                n[k].append(d["n_forb"].get(key))
    return {"pct": pct, "blocked": blk, "n": n}


# ---------------------------------------------------------------- derived strings
def r0(x: float) -> str:
    return f"{x:.0f}"


def exact_jump(d: dict) -> tuple[str, str]:
    """('10', '14-20'): scripted exact-ledger rate and the LLM-coordinator range, as printed in P2."""
    s = r0(d["viol"][("exact", "scripted")])
    llm = [d["viol"][("exact", c)] for c in COORDS[1:]]
    return s, f"{r0(min(llm))}–{r0(max(llm))}"


def max_other_blocked(d: dict) -> float:
    return max(d["blocked"].values())


def caption_neurips(d: dict) -> str:
    s, rng = exact_jump(d)
    return (
        "(a) A coordinator passes each request (24 allowed and 24 forbidden types, 12 families) to an "
        "openai/gpt-oss-20b worker on a synthetic database; a rule-based checker flags violations. Each run uses one "
        "defense; (ii) and (iii) read the ledger of refused text (τ = 0.85, MiniLM). On the main host, forbidden "
        "requests executed fell from 25.5% (no defense) to 14.8% (never re-ask) and 9.3% (exact ledger); text "
        "similarity also blocked 38–42% of allowed work. (b) Second host (primeintellect, fp4 quantization): 3 "
        f"trials, n = {d['n_forb'][('none', 'scripted')]} forbidden requests per bar, Wilson 95% intervals; "
        f"† scripted text similarity uses all 6 trials of the same host's run (n = {d['sem_n']}). The LLM "
        f"coordinator rephrases past the exact ledger ({s}% to {rng}%) but not the intent screen. Lower strip: allowed "
        f"requests blocked; text similarity blocked {d['sem_false_block']:.0f}%, every other bar at most "
        f"{max_other_blocked(d):.1f}%. The adaptive run tested three defenses, without text similarity, and ran "
        "reason hidden only with no defense and the exact ledger (×). Not audited.\n")


def caption_lw(d: dict) -> str:
    return (
        "Bars: forbidden requests executed on the adaptive-coordinator host (primeintellect, fp4), 3 trials, "
        f"n = {d['n_forb'][('none', 'scripted')]} per bar, Wilson 95% intervals; values as in P2 §4.6. Scripted "
        f"text similarity ({d['sem_viol']:.1f}%, and {d['sem_false_block']:.0f}% of allowed requests blocked) uses all "
        f"6 trials of the same host's four-arm run (n = {d['sem_n']}; P2 §4.3). Text similarity was not run with "
        "the LLM coordinator, and the reason-hidden condition only with no defense and the exact ledger. Dashed line: "
        f"never re-ask on this host ({d['never_reask']:.1f}%, P2 §4.2). The exchange is verbatim from the run log "
        "(synthetic data).\n")


if __name__ == "__main__":
    d = load()
    print("all P2 checks passed;", len(d["viol"]), "adaptive bars;", f"sem {d['sem_viol']:.2f} / "
          f"{d['sem_false_block']:.2f}; never re-ask {d['never_reask']:.2f}")
