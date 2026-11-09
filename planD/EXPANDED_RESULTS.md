# Plan D: expanded experiment results

Authorized cumulative cap: **$2.00**. Reported cumulative model charges: **$0.263723** across **9,682 request attempts** (9,660 logged completion records). Conservative budget accounting: $0.813723; 22 unresolved charge reservations. These totals include smoke, diagnostic and superseded runs.

All tasks use synthetic records and explicit toy database access rules. Model-generated actions are verified from SQL results and database state.

## Completed stages

| Stage | Main task episodes | Calibration draws | API calls | Reported stage cost | Operational flags |
|---|---:|---:|---:|---:|---:|
| pilot | 560 | 240 | 1,568 | $0.043033 | 7 |
| diversity | 2,016 | 861 | 6,185 | $0.184087 | 23 |
| ledger | 864 | 0 | 922 | $0.017801 | 1 |

The native-tool pilot, JSON-action diversity grid, and separate matched-task memory experiment are not pooled into a single violation estimate.

## Model diversity and repeated attempts

| Family/pool | W=1 fresh | W=3 fresh | W=6 fresh | W=3 retry | W=6 retry |
|---|---:|---:|---:|---:|---:|
| gpt | 5.6% | 6.9% | 16.7% | 0.0% | 6.9% |
| qwen | 2.8% | 8.3% | 8.3% | 1.4% | 1.4% |
| mistral | 1.4% | 9.7% | 9.7% | 5.6% | 4.2% |
| mixed | — | 12.5% | 20.8% | — | — |

Rates are forbidden-task episodes with at least one observed violation. Each fresh-pool cell has 72 forbidden episodes across 12 tasks; the mixed W=3/6 pools use all three model families. Mixed order rotates through six permutations. Complete task-bootstrap intervals and paired contrasts are in the diversity report.

Mixed pools have the highest point estimates at both attempt budgets in this dataset; wide task-level intervals and model differences limit the inference.

## Refusal memory across requests

| Memory | Forbidden-request violation | Allowed success | Allowed requests blocked by ledger |
|---|---:|---:|---:|
| none | 9.0% | 100.0% | 0.0% |
| exact | 0.7% | 97.2% | 2.8% |
| lexical | 4.2% | 59.7% | 40.3% |

Each memory arm has 144 forbidden and 144 allowed task episodes, grouped into six independent trials. Exact memory shares refusals for identical requests. Lexical memory uses TF-IDF cosine with a fixed 0.55 threshold, not an embedding or intent-trained model. Similar wording can confuse permissions for user_id=1 and user_id=2. Trial-bootstrap intervals and paired differences are in the memory report.

## Evidence and limits

- Observed violations on allowed requests in the selected main datasets: 0.
- These are exploratory synthetic experiments. Few unique tasks, six diversity repetitions, and six memory trials limit generalization. Nominal intervals are not adjusted for multiple comparisons.
- Each model uses a pinned DeepInfra endpoint without fallbacks; sizes, quantization, and reasoning settings still differ. The earlier native-tool pilot varies providers and is kept separate.
- The verifier covers protected literal SQL results and state mutations, including unauthorized ticket ownership. It does not cover arbitrary encodings, aggregates, or changes restored before a final snapshot.
- Operational failures are recorded separately. The diversity/memory primary rates retain completed episodes including failures; the pilot uses complete-case rates.
- The initial Llama protocol diagnostics and the first memory run with an ambiguous ID-reading control are preserved but excluded from final comparisons. Their costs still count against $2.
- Autonomous coordinator pressure, decomposition, paraphrase adaptation, embeddings, and intent-trained defenses remain untested.

## Artifacts

- Native-tool pilot: `planD/runs/20261107T064013391682Z-full/RESULTS.md`.
- Diversity: `planD/runs/20261107T064719208501Z-diversity/RESULTS.md`; plot `violation_vs_w.png`.
- Corrected memory experiment: `planD/runs/20261107T065945724810Z-ledger/RESULTS.md`; plot `ledger_tradeoff.png`.
- Each run retains configurations, per-episode verdicts, output hashes, token/cost records, individual flags, and machine-readable statistics. Main experiment source snapshots are hash-verified.
- Commands and methodology: `planD/README.md` and `planD/EXPERIMENT_DESIGN.md`.
