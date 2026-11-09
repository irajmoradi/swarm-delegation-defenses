"""Save/load toy checkpoints to a local directory."""
import json
from pathlib import Path


def checkpoint_path(directory, step):
    return Path(directory) / f"ckpt_{step:06d}.json"


def save_checkpoint(directory, step, weights, meta=None):
    path = checkpoint_path(directory, step)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"step": step, "weights": weights, "meta": meta or {}}, f)
    return path


def can_read(reader, config):
    return reader in config.get("checkpoint_readers", [])


def load_checkpoint(path, reader, config):
    if not can_read(reader, config):
        raise PermissionError(f"{reader} may not read checkpoints")
    with open(path) as f:
        return json.load(f)


def prune_checkpoints(directory, keep_last):
    paths = sorted(Path(directory).glob("ckpt_*.json"))
    for p in paths[:-keep_last]:
        p.unlink()
