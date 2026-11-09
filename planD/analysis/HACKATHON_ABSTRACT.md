# Abstract draft (Apart style) and paper skeleton

**Title (working):** Refusal Shopping: How Routing Refused Requests Across Workers Erodes Per-Worker Safety, and What a Shared Refusal Memory Costs

## Abstract (about 230 words)

Delegation systems let a coordinator LLM send a request to worker LLMs. If a worker refuses, the coordinator can retry the request or reroute it to another worker, so per-worker refusal may not bound system-level risk. We study this "refusal shopping" in a synthetic access-control setting: an in-memory fake database with explicit rules, where a violation is a forbidden action that was actually executed, checked against database state rather than model claims.

We use three open-weight model families (GPT-OSS 20B, Qwen3 32B, Mistral Small 3.2 24B), 96 balanced requests in 12 scenario families, and W = 1, 3 and 6 workers. Violation rates rise with W: pooled same-model W=6 minus W=1 is +11.1 pp (95% CI 6.2 to 16.7). Mixed-family pools violate more than same-family pools (+13.2 pp [7.3, 19.1] at W=3), but this is consistent with heterogeneous per-request propensities, not evidence of lower refusal correlation. Observed rates stay within 5 pp of an independence plug-in.

A shared refusal ledger with exact matching cut violations from 9.0% to 0.7% on repeated requests, with 2.8% false blocks, while TF-IDF matching blocked about 40% of allowed requests. Model-parsed tool-scope memory reached 12.5% violations (28.1% without memory) with 2.4% blocks under wording shift. A coordinator probe found unprompted rerouting of forbidden requests at 4.9%, rising only with an explicit instruction (+9.7 pp).

Results are exploratory: a few request-model pairs carry the risk, n is small, and the setting is a toy. Total cost: $0.68.

## Paper skeleton (5 bullets)

1. **Problem and threat model.** Refusal shopping in coordinator-worker systems. Link to "Adversaries Can Misuse Combinations of Safe Models" and the decomposition literature. Define a violation as an executed forbidden action. Derive 1-r^W and 1-(1-p)^W, and say what they do and don't prove (heterogeneity counterexample).
2. **Setup.** Synthetic DB, typed-action executor and policy oracle, a 96-request balanced bank (48 intents, 12 families, 2 wordings), three pinned model endpoints, W in {1, 3, 6}, retry vs reroute, family-cluster bootstrap, calibration draws kept separate. Report the v1 SQL study as a separate pilot.
3. **Results on routing.** Violation grows with W (modest, concentrated between W=3 and W=6). Mixed pools are worse than same-family. Retry is less risky than reroute at W=6. Curves stay near the independence plug-in. Risk is concentrated in 37 of 144 intermediate request-model cells; include the drop-ticket_read sensitivity check.
4. **Defense.** The refusal-ledger trade-off (exact, lexical, scope), with false-block cost as the main axis, and propagated spurious refusals. Caveat: exact matching's gain includes within-request stopping. Coordinator probe: shopping is rare unprompted and rises with an explicit instruction; deadline and reward are null.
5. **Limitations and next steps.** Toy policy, small n, single-task dominance, multiple comparisons. Untested: split/decomposition, an adaptive paraphrasing coordinator, live embedding and intent-trained ledgers, end-to-end autonomous shopping, and comparison with code-enforced authorization as the stronger reference.
