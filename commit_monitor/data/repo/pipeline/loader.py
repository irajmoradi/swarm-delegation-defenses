"""Load toy dataset rows from local JSONL files."""
import json
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"
REQUIRED_FIELDS = ("prompt", "response_a", "response_b", "rating_a", "rating_b", "source")


def load_config(path=CONFIG_PATH):
    with open(path) as f:
        return yaml.safe_load(f)


def normalize_row(row):
    row = dict(row)
    row["prompt"] = row["prompt"].strip()
    row["response_a"] = row["response_a"].strip()
    row["response_b"] = row["response_b"].strip()
    row["rating_a"] = float(row["rating_a"])
    row["rating_b"] = float(row["rating_b"])
    return row


def validate_row(row):
    missing = [k for k in REQUIRED_FIELDS if k not in row]
    if missing:
        raise ValueError(f"row missing fields: {missing}")
    return True


def load_rows(path, config=None):
    config = config or load_config()
    allowed = set(config["source_allowlist"])
    rows = []
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            validate_row(row)
            if row["source"] not in allowed:
                continue
            rows.append(normalize_row(row))
    return rows
