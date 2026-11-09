"""Build (chosen, rejected) preference pairs from rated rows."""


def make_pair(row):
    if row["rating_a"] == row["rating_b"]:
        return None
    if row["rating_a"] > row["rating_b"]:
        chosen, rejected = row["response_a"], row["response_b"]
    else:
        chosen, rejected = row["response_b"], row["response_a"]
    return {"prompt": row["prompt"], "chosen": chosen, "rejected": rejected,
            "margin": abs(row["rating_a"] - row["rating_b"]), "source": row["source"]}


def build_pairs(rows, min_margin=0.5):
    pairs = []
    for row in rows:
        pair = make_pair(row)
        if pair is None or pair["margin"] < min_margin:
            continue
        pairs.append(pair)
    return pairs


def pair_stats(pairs):
    if not pairs:
        return {"n": 0, "mean_margin": 0.0}
    return {"n": len(pairs), "mean_margin": sum(p["margin"] for p in pairs) / len(pairs)}
