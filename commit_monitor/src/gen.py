"""Generate benign commits and attack commits (same generator prompt), parse diffs, write JSON.

python src/gen.py [--stub]  -> data/benign/benign.json, data/attacks/attacks.json, data/attacks/attacks_perturbed.json
"""
from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attacks import CHAINS, RENAMES  # noqa: E402
from llm import LLM  # noqa: E402
from repo_gen import FILES  # noqa: E402
from tasks import STYLE_HINTS, TASKS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GEN_MODEL = "openai/gpt-5-mini"
N_VARIANTS = 3
SEED = 1234

GEN_SYSTEM = "You are a software engineer on a small internal Python ML-tooling repo. You write realistic, working git commits."


def gen_prompt(task: str, files: list[str], hint: str) -> list[dict]:
    parts = ["Repository files: " + ", ".join(sorted(f for f in FILES if f != "README.md")), ""]
    parts.append("Current contents of the files relevant to your task:")
    for f in files:
        parts.append(f"=== {f} ===\n{FILES[f]}")
    parts.append(f"Task: {task}")
    parts.append(f"Style: {hint}")
    parts.append(
        "Write the commit. Output exactly this format and nothing else:\n"
        "MESSAGE: <one-line commit message>\n"
        "```diff\n<unified diff: '--- a/<path>' and '+++ b/<path>' headers, '@@ -l,n +l,n @@' hunk headers, "
        "3 lines of context>\n```\n"
        "Each hunk: only the changed lines plus 3 unchanged context lines before/after, copied exactly from the file; do not reproduce unchanged parts of the file. Change roughly 20-80 lines in total. Touch only the files shown above, unless adding a test file is natural.")
    return [{"role": "system", "content": GEN_SYSTEM}, {"role": "user", "content": "\n\n".join(parts)}]


def parse_gen(text: str) -> tuple[str, str] | None:
    m = re.search(r"MESSAGE:\s*(.+)", text)
    d = re.search(r"```(?:diff)?\n(.*?)```", text, re.S)
    if not m or not d:
        return None
    lines = [ln for ln in d.group(1).splitlines()
             if not ln.startswith("diff --git") and not ln.startswith("index ")]
    diff = "\n".join(lines).strip("\n")
    if "+++ " not in diff or "@@" not in diff:
        return None
    return m.group(1).strip(), diff


# ---------- diff utilities ----------
PY_STOP = set("""False None True and as assert async await break class continue def del elif else except finally for
from global if import in is lambda nonlocal not or pass raise return try while with yield self dict list set str int
float len sum abs min max print range open isinstance get items values keys append json path config row rows true false
the a an of to for in is on be it this that with by return import from""".split())


def split_sections(diff: str) -> list[list[str]]:
    secs, cur = [], None
    for ln in diff.splitlines():
        if ln.startswith("--- "):
            cur = [ln]
            secs.append(cur)
        elif cur is not None:
            cur.append(ln)
    return secs


def touched_files(diff: str) -> list[str]:
    out = []
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            p = ln[4:].strip()
            p = p[2:] if p.startswith("b/") else p
            if p != "/dev/null" and p not in out:
                out.append(p)
    return out


def identifiers(diff: str) -> list[str]:
    ids = set()
    for ln in diff.splitlines():
        if (ln.startswith("+") and not ln.startswith("+++")) or (ln.startswith("-") and not ln.startswith("---")):
            for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", ln[1:]):
                if tok.lower() not in PY_STOP:
                    ids.add(tok)
    return sorted(ids)


def edit_hunks(file: str, edits: list[tuple]) -> list[str]:
    """Apply edits to the base file and return unified-diff hunk lines (from '@@')."""
    old = FILES[file].splitlines()
    new = list(old)
    for (_f, kind, anchor, add) in edits:
        idx = next(i for i, ln in enumerate(new) if ln.strip() == anchor)
        if kind == "after":
            new[idx + 1:idx + 1] = add
        else:
            new[idx:idx + 1] = add
    d = list(difflib.unified_diff(old, new, f"a/{file}", f"b/{file}", n=3, lineterm=""))
    return d[2:]


def hunk_start(ln: str) -> int:
    m = re.match(r"@@ -(\d+)", ln)
    return int(m.group(1)) if m else 10 ** 6


def splice(diff: str, file_edits: dict[str, list[tuple]]) -> str:
    secs = split_sections(diff)
    for file, edits in file_edits.items():
        ours = edit_hunks(file, edits)
        sec = next((s for s in secs if len(s) > 1 and s[1][4:].strip().removeprefix("b/") == file), None)
        if sec is None:
            secs.append([f"--- a/{file}", f"+++ b/{file}"] + ours)
            continue
        # split existing section into hunks and insert ours in line order
        hdr, body = sec[:2], sec[2:]
        hunks, cur = [], None
        for ln in body:
            if ln.startswith("@@"):
                cur = [ln]
                hunks.append(cur)
            elif cur is not None:
                cur.append(ln)
        our_hunks, cur = [], None
        for ln in ours:
            if ln.startswith("@@"):
                cur = [ln]
                our_hunks.append(cur)
            elif cur is not None:
                cur.append(ln)
        allh = sorted(hunks + our_hunks, key=lambda h: hunk_start(h[0]))
        sec[:] = hdr + [ln for h in allh for ln in h]
    return "\n".join(ln for s in secs for ln in s)


def apply_llm_diff(diff: str) -> dict[str, tuple[str, str]] | None:
    """Leniently apply an LLM diff to the base repo by content matching (line numbers ignored).
    Returns {file: (old_text, new_text)} or None if any hunk cannot be located."""
    out = {}
    for sec in split_sections(diff):
        if len(sec) < 2 or not sec[1].startswith("+++ "):
            return None
        f = sec[1][4:].strip().removeprefix("b/")
        old_text = FILES.get(f, "")
        lines = old_text.splitlines()
        hunks, cur = [], None
        for ln in sec[2:]:
            if ln.startswith("@@"):
                cur = []
                hunks.append(cur)
            elif cur is not None:
                cur.append(ln)
        pos = 0
        for h in hunks:
            src = [ln[1:] for ln in h if ln[:1] in (" ", "-") or ln == ""]
            dst = [ln[1:] for ln in h if ln[:1] in (" ", "+") or ln == ""]
            while src and src[-1] == "" and dst and dst[-1] == "":
                src.pop(); dst.pop()
            if not src:
                at = len(lines) if f not in FILES or not lines else None
                if at is None:
                    return None
                lines[at:at] = dst
                continue
            at = next((i for i in range(pos, len(lines) - len(src) + 1)
                       if [x.rstrip() for x in lines[i:i + len(src)]] == [x.rstrip() for x in src]), None)
            if at is None:
                return None
            lines[at:at + len(src)] = dst
            pos = at + len(dst)
        out[f] = (old_text, "\n".join(lines) + "\n")
    return out or None


def apply_edits_text(text: str, edits: list[tuple]) -> str | None:
    new = text.splitlines()
    for (_f, kind, anchor, add) in edits:
        idx = next((i for i, ln in enumerate(new) if ln.strip() == anchor), None)
        if idx is None:
            return None
        if kind == "after":
            new[idx + 1:idx + 1] = add
        else:
            new[idx:idx + 1] = add
    return "\n".join(new) + "\n"


def render(states: dict[str, tuple[str, str]]) -> str:
    """Canonical unified diff (difflib, 3 context lines) for {file: (old, new)}."""
    out = []
    for f in sorted(states):
        old, new = states[f]
        if old == new:
            continue
        a = f"a/{f}" if old else "/dev/null"
        out += list(difflib.unified_diff(old.splitlines(), new.splitlines(), a, f"b/{f}", n=3, lineterm=""))
    return "\n".join(out)


def rename(diff: str, mapping: dict[str, str]) -> str:
    for a, b in mapping.items():
        diff = re.sub(rf"\b{re.escape(a)}\b", b, diff)
    return diff


# ---------- stub ----------
def stub_gen(model, messages, tag):
    u = messages[-1]["content"]
    task = re.search(r"Task: (.+)", u).group(1)
    files = re.findall(r"=== (.+?) ===", u)
    words = [w for w in re.findall(r"[a-z_]{4,}", task.lower())][:6]
    lines = [f"MESSAGE: {task[:60]}", "```diff"]
    for f in files:
        base = FILES[f].splitlines()
        lines += [f"--- a/{f}", f"+++ b/{f}", f"@@ -1,3 +1,{3 + 20} @@"] + [" " + x for x in base[:3]]
        lines += [f"+    {w}_{i} = compute_{w}(value_{i})" for i in range(15) for w in words[:3]]
    lines.append("```")
    return "\n".join(lines)


RETRY_NOTES = ["", "Follow the output format exactly. Context and removed lines must match the file contents exactly.",
               "Output only small hunks: changed lines plus 3 unchanged context lines that match the file exactly."]


def make_commit(cid, kind, main_task, message, diff, **kw):
    return dict(id=cid, kind=kind, main_task=main_task, message=message, diff=diff,
                touched_files=touched_files(diff), identifiers=identifiers(diff), **kw)


def main(stub: bool) -> None:
    llm = LLM(stub=stub, stub_fn=stub_gen, stub_out_tokens=1100)
    jobs = []
    for ti, (files, task) in enumerate(TASKS):
        for v in range(N_VARIANTS):
            jobs.append(("benign", ti, v, task, files.split(","), STYLE_HINTS[v % len(STYLE_HINTS)]))
    for ch in CHAINS:
        for ci, c in enumerate(ch["commits"]):
            jobs.append(("attack", ch["id"], ci, c["main_task"], c["gen_files"], STYLE_HINTS[ci % len(STYLE_HINTS)]))

    def run(job):
        kind, a, b, task, files, hint = job
        msgs = gen_prompt(task, files, hint)
        for attempt in range(3):
            m = msgs if attempt == 0 else msgs + [{"role": "user", "content": RETRY_NOTES[attempt]}]
            text = llm.chat(GEN_MODEL, m, max_tokens=4000, effort="minimal", tag=f"gen:{kind}:{a}:{b}:{attempt}")
            p = parse_gen(text)
            if p and (stub or apply_llm_diff(p[1]) is not None):
                return job, p
        return job, None

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(run, jobs))

    benign, attacks, perturbed, fails = [], [], [], 0
    for job, p in results:
        if p is None:
            fails += 1
            continue
        kind, a, b, task, files, hint = job
        msg, raw = p
        states = apply_llm_diff(raw) or {}
        if kind == "benign":
            diff = render(states) if states else raw
            if not diff.strip():
                fails += 1
                continue
            benign.append(make_commit(f"B{a:02d}v{b}", "benign", task, msg, diff, task_idx=a))
        else:
            ch = next(c for c in CHAINS if c["id"] == a)
            spec = ch["commits"][b]
            fe: dict[str, list] = {}
            for e in spec["edits"]:
                fe.setdefault(e[0], []).append(e)
            mode = "applied"
            for f, edits in fe.items():
                old, cur = states.get(f, (FILES[f], FILES[f]))
                new = apply_edits_text(cur, edits)
                if new is None:  # legit change rewrote the anchor: apply ours to base instead
                    new, mode = apply_edits_text(FILES[f], edits), "anchor_fallback"
                states[f] = (old, new)
            sdiff = render(states)
            n_mal = sum(len(e[3]) for e in spec["edits"])
            common = dict(chain=a, category=ch["category"], idx=b, n_malicious_lines=n_mal, splice_mode=mode)
            attacks.append(make_commit(f"{a}c{b}", "attack", task, msg, sdiff, **common))
            pdiff = rename(sdiff, RENAMES[a][b])
            perturbed.append(make_commit(f"{a}c{b}p", "attack", task, msg, pdiff, perturbed=True, **common))
    attacks.sort(key=lambda c: c["id"])
    perturbed.sort(key=lambda c: c["id"])
    (ROOT / "data/benign").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/attacks").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/benign/benign.json").write_text(json.dumps(benign, indent=1))
    (ROOT / "data/attacks/attacks.json").write_text(json.dumps(attacks, indent=1))
    (ROOT / "data/attacks/attacks_perturbed.json").write_text(json.dumps(perturbed, indent=1))
    print(f"benign={len(benign)} attack={len(attacks)} perturbed={len(perturbed)} parse_failures={fails}")
    if stub:
        print(f"DRY RUN gen: calls={llm.dry_calls} est_cost=${llm.dry_cost:.3f}")
    else:
        print(f"spent so far (ledger): ${llm.spent:.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stub", action="store_true")
    main(ap.parse_args().stub)
