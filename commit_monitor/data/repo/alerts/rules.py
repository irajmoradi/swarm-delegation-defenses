"""Threshold-based alert rules for training metrics."""
import time

import yaml

_last_fired = {}


def load_config(path="alerts/config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def should_fire(metric, value, config, now=None):
    now = now or time.time()
    threshold = config["thresholds"].get(metric)
    if threshold is None:
        return False
    if value <= threshold:
        return False
    last = _last_fired.get(metric, 0)
    if now - last < config["cooldown_seconds"]:
        return False
    _last_fired[metric] = now
    return True


def evaluate(metrics, config):
    return [{"metric": m, "value": v} for m, v in metrics.items() if should_fire(m, v, config)]
