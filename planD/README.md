# Plan D research packet

The completed morning handoff starts at [Lance: start here](LANCE_START_HERE.md).
A [PDF brief](LANCE_MORNING_BRIEF.pdf) and [portable ZIP](LANCE_HANDOFF.zip) are ready.
See [overnight reproduction instructions](overnight/README.md) for the new studies and offline analysis.
The earlier MVP and batch instructions follow below.

The user subsequently authorized a $2 cumulative local cap and larger experiments.
The native-tool pilot and the controlled diversity experiment are separate datasets.
The completed batch overview is `planD/EXPANDED_RESULTS.md`; machine-readable
batch counts and budget reconciliation are in `planD/batch_summary.json`.

```bash
python -m planD.run full --k 5 --eps 5
python -m planD.diversity --k 6 --eps 6 --workers 8
python -m planD.ledger_experiment --trials 6 --cycles 3 --workers 6
```

Regenerate the overview for this completed batch without making model calls:

```bash
python -m planD.summarize_batch --pilot 20261107T064013391682Z-full --diversity 20261107T064719208501Z-diversity --ledger 20261107T065945724810Z-ledger
```

The diversity grid uses GPT-OSS 20B, Qwen3 32B, and Mistral Small 3.2 24B,
each pinned to a specific DeepInfra endpoint without provider fallback. All use
the same strict JSON-schema action protocol, converted into local run_sql/refuse
actions. This avoids native-tool parser differences found during the initial
Llama compatibility check. Diagnostic runs are retained and never pooled with
the main experiment. Model sizes, quantization, and reasoning differ; the report
records these limits on causal interpretation.

The default diversity experiment has 2,304 jobs: three independent calibration
draws per panel, six panels per task/family, six main episode replicates per
condition, all sixteen tasks, W=1,3,6, same-family reroute/retry, mixed-family
reroute, and exact-match ledgers at W=3. The six mixed-family permutations rotate
across replicates. Results go to `planD/DIVERSITY_RESULTS.md` and each run's directory.

The cross-request memory experiment uses a separate balanced suite of eight
allowed/eight forbidden requests. Each trial sends three shuffled passes of the
suite with W=3, sharing a refusal ledger across requests. It compares no memory,
exact matching, and a TF-IDF lexical matcher at a fixed 0.55 cosine threshold.
Closely worded requests for user_id=1 versus user_id=2 test false blocking when
wording overlaps but permissions differ. All arms share a trial's request order.
Intervals resample whole trials to preserve memory dependence. This lexical
baseline is not an embedding model or intent-trained matcher. The default has
six trials per arm, 864 task episodes, and reports to `planD/LEDGER_RESULTS.md`.

Lance's scoped experiment: plain synthetic database requests, same-model workers,
retry versus reroute, and a shared exact-match refusal ledger. There are no real
secrets in the database. Model-generated SQL runs only in disposable in-memory
SQLite databases. The actual OpenRouter credential is never sent in a prompt.

From the workspace root:

```bash
python -m pip install -r planD/requirements.txt
python -m unittest planD.test_planD -v
python -m planD.run dry --k 1 --eps 1
python -m planD.run smoke
# Larger experiment, only when wanted (still subject to the cumulative cap):
python -m planD.run full
```

The default smoke test uses two forbidden and two allowed tasks, three independent
calibration panels of three workers per task, and two episode replicates per cell.
W is 1 or 3. The full command uses all 16 tasks and W=1,3,6. `--tasks` accepts
comma-separated task IDs; `--k`, `--eps`, and `--workers` control sampling and
concurrency. Each sample is a real independent call; no response cache collapses
trials. The retry strategy retains conversation history, while reroute starts a
new conversation. The common W=1 baseline is sampled once per replicate.

(Public release: the client reads `OPENROUTER_API_KEY`, or the file named by `OPENROUTER_KEY_FILE`;
see the top-level README and `.env.example`. Sprint text follows.) The original client read a key file from the workspace root, or used
`OPENROUTER_API_KEY` if set. The file must contain one raw key, with no shell syntax.
Do not copy it into Claude notes, prompts, logs, or git.

`planD/budget.jsonl` persists reservations and returned costs across runs and
processes. Every paid request reserves $0.025 before transmission. Provider prices
are limited to $1/M input and output tokens; payloads are capped at 12,000 bytes
and output at 1,024 tokens. Missing cost accounting, transport failures and crashes
keep their full reservations. There are no automatic HTTP retries. A corrupt
ledger stops the run. The $2 cumulative client cap applies to this harness, not unrelated
tools sharing the key; key-level limits remain under OpenRouter's control.

After the expanded batch exposed a burst of HTTP 429s during overlapping runs,
the client gained a persistent per-model cooldown: future requests honor
Retry-After (at least 30 seconds), without retrying the failed episode. This
hardening was added after those datasets were collected and does not erase their
recorded errors. Historical source snapshots preserve the original behavior.

Each run saves config, task text, DB verdicts, calibration, summary JSON, a Markdown
report, and a PNG plot under `planD/runs/`. The latest live report is also copied to
`planD/RESULTS.md`. Full outputs and generated SQL are not persisted. Provider
failures are recorded individually in `flagged.jsonl`, never counted as refusals.
Unknown charges are retained in the budget even if an episode is excluded.

The verifier checks literal protected values in SQL results, protected-table state
changes, and support tickets assigned to another user. It does not catch every
possible encoding or aggregate of a protected value. Allowed success uses SQL
results or DB state, rather than accepting the assistant's claim.

Reports distinguish 1−r^W from 1−(1−p)^W when non-refusal does not imply violation.
Bootstrap intervals resample whole tasks, and are exploratory on small smoke
samples. Constant refusal columns make correlation undefined. The original
native-tool pilot does not test mixed-family pools; the separate diversity grid
does. Autonomous coordinator propensity, decomposition, paraphrases, and
semantic/intent matching remain untested.

Progress appends to `codex_log.md`. During a run the runner checks
`claude_instruct.md` after each completed job and announces changes for review.
It never executes instructions from that file automatically, and does not provide
an always-on monitor after the active session ends.

Current model and accounting references checked 2026-11-07:
[model](https://openrouter.ai/openai/gpt-oss-20b),
[key limits](https://openrouter.ai/docs/api-reference/limits).
