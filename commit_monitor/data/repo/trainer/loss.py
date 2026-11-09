"""Toy preference loss (logistic on score differences)."""
import math


def preference_loss(score_chosen, score_rejected, beta=0.1):
    diff = beta * (score_chosen - score_rejected)
    return math.log1p(math.exp(-diff))


def batch_loss(batch, beta=0.1):
    if not batch:
        return 0.0
    total = sum(preference_loss(b["score_chosen"], b["score_rejected"], beta) for b in batch)
    return total / len(batch)
