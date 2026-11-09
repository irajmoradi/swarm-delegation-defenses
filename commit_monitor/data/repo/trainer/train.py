"""Toy training loop over preference pairs."""
import random

import yaml

from trainer.checkpoint import prune_checkpoints, save_checkpoint
from trainer.eval_gate import gate
from trainer.loss import batch_loss


def load_config(path="trainer/config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def score(weights, text):
    return sum(weights.get(tok, 0.0) for tok in text.split())


def train(pairs, eval_set, config, seed=0):
    rng = random.Random(seed)
    weights = {}
    step = 0
    for epoch in range(config["epochs"]):
        rng.shuffle(pairs)
        for i in range(0, len(pairs), config["batch_size"]):
            batch = [{"score_chosen": score(weights, p["chosen"]),
                      "score_rejected": score(weights, p["rejected"])} for p in pairs[i:i + config["batch_size"]]]
            loss = batch_loss(batch, config["beta"])
            for p in pairs[i:i + config["batch_size"]]:
                for tok in p["chosen"].split():
                    weights[tok] = weights.get(tok, 0.0) + config["learning_rate"] * loss
                for tok in p["rejected"].split():
                    weights[tok] = weights.get(tok, 0.0) - config["learning_rate"] * loss
            step += 1
        save_checkpoint(config["checkpoint_dir"], step, weights, {"epoch": epoch})
        prune_checkpoints(config["checkpoint_dir"], config["keep_last"])
    promoted = gate(weights, eval_set, config)
    return weights, promoted
