"""Round 5 statistics (items 1-4), usable on any scores file with roles attack/cal/benign_eval.

1 matched realized FPR: threshold read off the HELD-OUT benign ROC so every method sits at the same actual FPR
2 paired bootstrap of detection differences (same attack sequences; resample chains + calibration seqs) and
  exact McNemar on deterministic flags
3 score combination: (a) label-free max of calibration-standardized scores; (b) logistic regression,
  leave-one-chain-out (benign side = calibration seqs only)
4 calibration: randomized Neyman-Pearson (rounds 2-4) vs split-conformal strict threshold; realized vs target
"""
from __future__ import annotations

import math
import random
from math import comb

import numpy as np

from analysis import auc, ci, flag_rate, threshold

B = 2000


def conformal_t(cal, alpha):
    """Split-conformal: q = ceil((n+1)(1-alpha))-th smallest; flag iff score > q  =>  P(FP) <= alpha."""
    s = sorted(cal)
    k = math.ceil((len(s) + 1) * (1 - alpha))
    return math.inf if k > len(s) else s[k - 1]


def det_conformal(scores, q):
    return float(np.mean(np.array(scores) > q)) if len(scores) else float("nan")


def matched(att, ev, fpr):
    """Detection at realized held-out FPR = fpr (randomized threshold on the held-out benign scores)."""
    return flag_rate(att, threshold(ev, fpr))


def roc(att, ev):
    pts = [(0.0, 0.0)]
    for t in sorted(set(att) | set(ev), reverse=True):
        pts.append((float(np.mean(np.array(ev) >= t)), float(np.mean(np.array(att) >= t))))
    pts.append((1.0, 1.0))
    return pts


def mcnemar_exact(a_flags, b_flags):
    b = sum(1 for x, y in zip(a_flags, b_flags) if x and not y)
    c = sum(1 for x, y in zip(a_flags, b_flags) if y and not x)
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    return b, c, p


def paired(att_rows, cal_rows, ma, mb, fpr, seed=0):
    rng = random.Random(seed)
    chains = sorted({r["chain"] for r in att_rows})
    diffs = []
    for _ in range(B):
        cs = [rng.choice(chains) for _ in chains]
        a = [r for c in cs for r in att_rows if r["chain"] == c]
        cb = [rng.choice(cal_rows) for _ in cal_rows]
        ta = threshold([r["scores"][ma] for r in cb], fpr)
        tb = threshold([r["scores"][mb] for r in cb], fpr)
        diffs.append(flag_rate([r["scores"][ma] for r in a], ta) - flag_rate([r["scores"][mb] for r in a], tb))
    point = (flag_rate([r["scores"][ma] for r in att_rows], threshold([r["scores"][ma] for r in cal_rows], fpr)) -
             flag_rate([r["scores"][mb] for r in att_rows], threshold([r["scores"][mb] for r in cal_rows], fpr)))
    qa = conformal_t([r["scores"][ma] for r in cal_rows], fpr)
    qb = conformal_t([r["scores"][mb] for r in cal_rows], fpr)
    fa = [r["scores"][ma] > qa for r in att_rows]
    fb = [r["scores"][mb] > qb for r in att_rows]
    b, c, p = mcnemar_exact(fa, fb)
    return dict(diff=point, ci95=ci(diffs), p_boot_le0=float(np.mean(np.array(diffs) <= 0)),
                mcnemar_a_only=b, mcnemar_b_only=c, mcnemar_p=p)


def add_combos(rows, per="per_commit", joints=()):
    """Adds label-free combo scores: max of z-scores standardized on calibration rows."""
    cal = [r for r in rows if r["role"] == "cal"]
    for j in joints:
        stats = {}
        for m in (per, j):
            v = np.array([r["scores"][m] for r in cal], float)
            stats[m] = (v.mean(), v.std() + 1e-9)
        for r in rows:
            r["scores"][f"zmax_{j}"] = round(max((r["scores"][m] - stats[m][0]) / stats[m][1] for m in (per, j)), 4)
            r["scores"][f"max_{j}"] = max(r["scores"][per], r["scores"][j])


def loco_lr(rows, per, joint, fprs=(0.01, 0.05)):
    """Logistic regression on [per, joint], leave-one-chain-out; benign training rows = calibration only;
    threshold from calibration predictions of the same fold model; evaluated on the left-out chain's attack
    seqs (detection) and on the held-out benign seqs (realized FPR, averaged over folds)."""
    cal = [r for r in rows if r["role"] == "cal"]
    ev = [r for r in rows if r["role"] == "benign_eval"]
    att = [r for r in rows if r["role"] == "attack"]
    chains = sorted({r["chain"] for r in att})
    X = lambda rs: np.array([[r["scores"][per], r["scores"][joint]] for r in rs], float)
    mu, sd = X(cal).mean(0), X(cal).std(0) + 1e-9
    res = {f: dict(det=[], fpr=[]) for f in fprs}
    for ch in chains:
        tr_att = [r for r in att if r["chain"] != ch]
        Xt = (np.vstack([X(cal), X(tr_att)]) - mu) / sd
        y = np.array([0] * len(cal) + [1] * len(tr_att))
        sw = np.where(y == 1, len(cal) / max(1, len(tr_att)), 1.0)
        w, b = np.zeros(2), 0.0
        for _ in range(3000):
            p = 1 / (1 + np.exp(-(Xt @ w + b)))
            g = sw * (p - y)
            w -= 0.05 * (Xt.T @ g / len(y) + 0.01 * w)
            b -= 0.05 * g.mean()
        f = lambda rs: list(((X(rs) - mu) / sd) @ w + b)
        for fp in fprs:
            th = threshold(f(cal), fp)
            res[fp]["det"] += [flag_rate([v], th) for v in f([r for r in att if r["chain"] == ch])]
            res[fp]["fpr"].append(flag_rate(f(ev), th))
    return {f"fpr{int(fp * 100)}": dict(detection=float(np.mean(v["det"])), heldout_fpr=float(np.mean(v["fpr"])))
            for fp, v in res.items()}


def full_report(rows, methods, pairs, fprs=(0.01, 0.05), matched_fprs=(0.05, 0.12)):
    att = [r for r in rows if r["role"] == "attack"]
    cal = [r for r in rows if r["role"] == "cal"]
    ev = [r for r in rows if r["role"] == "benign_eval"]
    rng = random.Random(1)
    chains = sorted({r["chain"] for r in att})
    out = {"n_attack": len(att), "n_cal": len(cal), "n_eval": len(ev), "methods": {}, "paired": {}}
    for m in methods:
        A = [r["scores"][m] for r in att]
        E = [r["scores"][m] for r in ev]
        C = [r["scores"][m] for r in cal]
        mo = {"auc": auc(A, E)}
        boots = []
        for _ in range(B):
            a = [r["scores"][m] for c in [rng.choice(chains) for _ in chains] for r in att if r["chain"] == c]
            boots.append(auc(a, [rng.choice(E) for _ in E]))
        mo["auc_ci95"] = ci(boots)
        for f in fprs:
            th = threshold(C, f)
            q = conformal_t(C, f)
            mo[f"np_fpr{int(f * 100)}"] = dict(detection=flag_rate(A, th), realized_fpr=flag_rate(E, th))
            mo[f"conf_fpr{int(f * 100)}"] = dict(detection=det_conformal(A, q), realized_fpr=det_conformal(E, q))
        for f in matched_fprs:
            boots = []
            for _ in range(B):
                a = [r["scores"][m] for c in [rng.choice(chains) for _ in chains] for r in att if r["chain"] == c]
                boots.append(matched(a, [rng.choice(E) for _ in E], f))
            mo[f"matched{int(f * 100)}"] = dict(detection=matched(A, E, f), ci95=ci(boots))
        mo["roc"] = roc(A, E)
        out["methods"][m] = mo
    for a, b in pairs:
        out["paired"][f"{a} - {b}"] = {f"fpr{int(f * 100)}": paired(att, cal, a, b, f) for f in fprs}
    return out
