from pipeline.pairs import build_pairs, make_pair


def test_make_pair_orders_by_rating():
    row = {"prompt": "p", "response_a": "a", "response_b": "b", "rating_a": 1, "rating_b": 3, "source": "s"}
    pair = make_pair(row)
    assert pair["chosen"] == "b" and pair["rejected"] == "a"


def test_build_pairs_drops_ties():
    row = {"prompt": "p", "response_a": "a", "response_b": "b", "rating_a": 2, "rating_b": 2, "source": "s"}
    assert build_pairs([row]) == []
