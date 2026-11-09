"""Row filters applied before pair construction."""
import hashlib


def text_length_ok(row, config):
    n = len(row["prompt"]) + len(row["response_a"]) + len(row["response_b"])
    return config["min_text_len"] <= n <= config["max_text_len"]


def toxicity_ok(row, config):
    score = row.get("toxicity", 0.0)
    return score <= config["max_toxicity"]


def row_fingerprint(row):
    text = row["prompt"] + "\x1f" + row["response_a"] + "\x1f" + row["response_b"]
    return hashlib.sha256(text.encode()).hexdigest()


def dedupe_rows(rows):
    seen = set()
    out = []
    for row in rows:
        fp = row_fingerprint(row)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(row)
    return out


def apply_filters(rows, config):
    rows = [r for r in rows if text_length_ok(r, config) and toxicity_ok(r, config)]
    if config.get("dedupe", True):
        rows = dedupe_rows(rows)
    return rows
