from alerts.rules import should_fire

CFG = {"thresholds": {"loss_spike": 3.0}, "cooldown_seconds": 300}


def test_fires_above_threshold():
    assert should_fire("loss_spike", 4.0, CFG, now=1000)


def test_no_fire_below_threshold():
    assert not should_fire("loss_spike", 1.0, CFG, now=5000)
