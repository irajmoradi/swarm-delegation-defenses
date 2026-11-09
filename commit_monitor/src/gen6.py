"""Round 6 data: (a) 36 new attack chains (attacks2.CHAINS2): legit part by the same generator prompt, toy hunk
applied on top (retries ask to keep anchor lines; fallback applies the hunk to the base file and is recorded);
(b) one NEW benign variant (v3) of each of the 65 tasks, for a fresh test split.

python src/gen6.py [--stub] -> data/attacks/attacks_r6.json, data/benign/benign_v3.json
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen as G  # noqa: E402
from attacks2 import CHAINS2  # noqa: E402
from llm import LLM  # noqa: E402
from repo_gen import FILES  # noqa: E402
from tasks import TASKS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
V3_HINT = "Keep it production-ready: validate inputs and handle edge cases."


def gen_attack_commit(llm, ch, ci, stub):
    spec = ch["commits"][ci]
    fe = {}
    for e in spec["edits"]:
        fe.setdefault(e[0], []).append(e)
    anchors = sorted({e[2] for e in spec["edits"]})
    base = G.gen_prompt(spec["main_task"], spec["gen_files"], G.STYLE_HINTS[ci % 3])
    mode, st, msg = "anchor_fallback", None, spec["main_task"]
    for k in range(4):
        m = base if k == 0 else base + [{"role": "user", "content": "Keep these existing lines unchanged: " +
                                         " | ".join(anchors) + ". Context and removed lines must match the file exactly."
                                         + (f" (attempt {k})" if k > 1 else "")}]
        text = llm.chat(G.GEN_MODEL, m, max_tokens=4000, effort="minimal", tag=f"gen:r6attack:{ch['id']}:{ci}:{k}")
        p = G.parse_gen(text)
        s = G.apply_llm_diff(p[1]) if (p and not stub) else None
        if not s:
            continue
        ok = True
        for f, eds in fe.items():
            old, cur = s.get(f, (FILES[f], FILES[f]))
            new = G.apply_edits_text(cur, eds)
            if new is None:
                ok = False
                break
            s[f] = (old, new)
        if ok:
            st, msg, mode = s, p[0], "applied"
            break
    if st is None:
        st = {f: (FILES[f], G.apply_edits_text(FILES[f], eds)) for f, eds in fe.items()}
    diff = G.render(st)
    return G.make_commit(f"{ch['id']}c{ci}", "attack", spec["main_task"], msg, diff, chain=ch["id"], pattern=ch["pattern"],
                         category=ch["category"], idx=ci, n_malicious_lines=sum(len(e[3]) for e in spec["edits"]),
                         splice_mode=mode)


def gen_benign_v3(llm, ti, stub):
    files, task = TASKS[ti]
    msgs = G.gen_prompt(task, files.split(","), V3_HINT)
    for attempt in range(3):
        m = msgs if attempt == 0 else msgs + [{"role": "user", "content": G.RETRY_NOTES[attempt]}]
        text = llm.chat(G.GEN_MODEL, m, max_tokens=4000, effort="minimal", tag=f"gen:benignv3:{ti}:{attempt}")
        p = G.parse_gen(text)
        s = G.apply_llm_diff(p[1]) if (p and not stub) else None
        if s:
            return G.make_commit(f"B{ti:02d}v3", "benign", task, p[0], G.render(s), task_idx=ti)
    return None


def main(stub):
    llm = LLM(stub=stub, stub_fn=G.stub_gen, stub_out_tokens=1100)
    with ThreadPoolExecutor(max_workers=6) as ex:
        att = list(ex.map(lambda a: gen_attack_commit(llm, a[0], a[1], stub),
                          [(ch, ci) for ch in CHAINS2 for ci in range(3)]))
        ben = list(ex.map(lambda t: gen_benign_v3(llm, t, stub), range(len(TASKS))))
    ben = [b for b in ben if b]
    if not stub:
        (ROOT / "data/attacks/attacks_r6.json").write_text(json.dumps(att, indent=1))
        (ROOT / "data/benign/benign_v3.json").write_text(json.dumps(ben, indent=1))
    from collections import Counter
    print(f"attack commits={len(att)} modes={Counter(c['splice_mode'] for c in att)} benign_v3={len(ben)}; "
          f"ledger=${llm.spent:.4f}" + (f" DRY est ${llm.dry_cost:.3f}" if stub else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stub", action="store_true")
    main(ap.parse_args().stub)
