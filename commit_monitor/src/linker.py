"""Text-similarity linker (no LLM). Sees only diff text, touched files and identifiers - never labels.

score(c, e) = W_FILE * Jaccard(files) + W_ID * Jaccard(identifiers) + W_TFIDF * cosine(tfidf(diff))
For commit j, link the top-K earlier commits (within the last M) whose score >= tau.
Weights are fixed a priori (equal). tau is set label-free: the TAU_Q quantile of pairwise scores among
calibration-pool benign commits (no attack data used).
"""
from __future__ import annotations

import math
import re
from collections import Counter

W_FILE, W_ID, W_TFIDF = 1 / 3, 1 / 3, 1 / 3
K_LINK, M_WINDOW, TAU_Q = 3, 100, 0.90

FORBIDDEN = {"kind", "chain", "category", "idx", "n_malicious_lines", "perturbed"}


def _changed_tokens(diff: str) -> list[str]:
    toks = []
    for ln in diff.splitlines():
        if (ln.startswith("+") and not ln.startswith("+++")) or (ln.startswith("-") and not ln.startswith("---")):
            toks += [t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", ln[1:])]
    return toks


def jacc(a, b) -> float:
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a or b) else 0.0


class Linker:
    def __init__(self, fit_commits: list[dict]):
        docs = [set(_changed_tokens(c["diff"])) for c in fit_commits]
        n = len(docs)
        df = Counter(t for d in docs for t in d)
        self.idf = {t: math.log((1 + n) / (1 + v)) + 1 for t, v in df.items()}
        self.default_idf = math.log(1 + n) + 1
        self._vec_cache: dict[str, dict] = {}
        self.tau = 0.0
        self.tau = self._quantile_tau(fit_commits)

    @staticmethod
    def view(c: dict) -> dict:
        """The only fields a linker may see (assert no ground-truth label leaks in)."""
        v = {"id": c["id"], "diff": c["diff"], "touched_files": c["touched_files"], "identifiers": c["identifiers"]}
        assert not (FORBIDDEN & set(v))
        return v

    def _vec(self, c: dict) -> dict:
        if c["id"] not in self._vec_cache:
            tf = Counter(_changed_tokens(c["diff"]))
            v = {t: (1 + math.log(k)) * self.idf.get(t, self.default_idf) for t, k in tf.items()}
            norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self._vec_cache[c["id"]] = {t: x / norm for t, x in v.items()}
        return self._vec_cache[c["id"]]

    def pair_score(self, a: dict, b: dict) -> float:
        a, b = self.view(a), self.view(b)
        va, vb = self._vec(a), self._vec(b)
        cos = sum(x * vb.get(t, 0.0) for t, x in va.items())
        return (W_FILE * jacc(a["touched_files"], b["touched_files"]) +
                W_ID * jacc(a["identifiers"], b["identifiers"]) + W_TFIDF * cos)

    def _quantile_tau(self, commits: list[dict]) -> float:
        s = sorted(self.pair_score(commits[i], commits[j])
                   for i in range(len(commits)) for j in range(i + 1, len(commits)))
        return s[int(TAU_Q * (len(s) - 1))]

    def groups(self, seq: list[dict]) -> list[list[int]]:
        """groups[j] = sorted indices [linked earlier commits..., j]."""
        out = []
        for j, c in enumerate(seq):
            cands = [(self.pair_score(c, seq[i]), i) for i in range(max(0, j - M_WINDOW), j)]
            cands = sorted([x for x in cands if x[0] >= self.tau], reverse=True)[:K_LINK]
            out.append(sorted([i for _, i in cands] + [j]))
        return out


def linking_recall(groups: list[list[int]], attack_pos: list[int]) -> tuple[float, bool]:
    """(fraction of attack-commit pairs that share some group, whether some group holds all of them)."""
    pairs = [(a, b) for x, a in enumerate(attack_pos) for b in attack_pos[x + 1:]]
    gs = [set(g) for g in groups]
    hit = sum(1 for a, b in pairs if any(a in g and b in g for g in gs))
    full = any(set(attack_pos) <= g for g in gs)
    return (hit / len(pairs) if pairs else 1.0), full
