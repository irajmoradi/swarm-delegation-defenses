# Frozen-embedding counterfactual replay

**These are replay estimates conditional on recorded no-memory trajectories, not new live model/guard observations. No OpenRouter requests occur.**

Task text is embedded using the pinned generic [all-MiniLM-L6-v2 encoder](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), CPU only, attention-mask mean pooling and L2 normalization. It is not IntentAlign or an intent-trained access-control matcher. A fixed threshold grid is reported in full; no test-selected operating point is recommended.

| Cosine threshold | Replayed violation | Replayed allowed safe completion | Replayed allowed block | Recorded attempts retained |
|---:|---:|---:|---:|---:|
| 0.50 | 3.1% | 13.9% | 86.1% | 100 |
| 0.60 | 3.1% | 25.3% | 74.7% | 146 |
| 0.70 | 5.6% | 48.3% | 51.7% | 242 |
| 0.80 | 9.0% | 68.1% | 31.9% | 340 |
| 0.90 | 10.8% | 80.2% | 19.8% | 434 |
| 0.95 | 13.9% | 84.0% | 16.0% | 504 |

## Replay assumptions

- Each trial starts from the actual no-memory request order and recorded fresh-worker attempts. A matching negative entry skips an action; a recorded refusal adds the request to memory. Calls after the first match/refusal may be removed.
- This is possible because workers receive fresh per-task contexts and databases reset. It assumes omitted calls would not change later per-task draws. Provider load, timing and new random samples could violate that counterfactual assumption.
- The replay can only remove recorded actions; it cannot generate new model outcomes or reveal how a live embedding guard changes behavior. It is a secondary sensitivity analysis, not another set of independent experimental samples.
- “Attempts retained” is a replay count, not new API spending or a realized refund. The live exact/lexical/scope arms use independent stochastic draws and should not be directly pooled with this table.
- Thresholds were fixed before this replay. Values are descriptive on the same fixed task suite, with no held-out calibration or generalization claim.

Source run: `planD/runs/20261107T083446934699Z-v2-memory/`. Encoder revision and embedding hash are in `EMBEDDING_MODEL.json`.
