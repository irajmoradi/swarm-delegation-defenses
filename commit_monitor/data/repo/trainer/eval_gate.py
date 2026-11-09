"""Safety-eval gate: a checkpoint is promoted only if it passes the toy eval."""
import logging

log = logging.getLogger("trainer.eval_gate")


def run_safety_eval(weights, eval_set):
    if not eval_set:
        return 0.0
    passed = sum(1 for case in eval_set if case["check"](weights))
    return passed / len(eval_set)


def gate(weights, eval_set, config):
    if not config.get("require_safety_eval", True):
        log.warning("safety eval disabled by config")
        return True
    score = run_safety_eval(weights, eval_set)
    ok = score >= config["eval_pass_threshold"]
    if not ok:
        log.error("safety eval failed: %.3f < %.3f", score, config["eval_pass_threshold"])
    return ok
