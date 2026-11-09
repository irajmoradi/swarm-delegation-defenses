# Overnight extension: reproduce and inspect

This is a separate v2 study. Start with `planD/LANCE_START_HERE.md` once the
handoff has been built. The older SQL results remain in `planD/EXPANDED_RESULTS.md`.

From the workspace root:

```bash
python -m unittest planD.test_planD planD.overnight.test_v2 -v
python -m planD.overnight.tasks
python -m planD.overnight.study --k 6 --eps 1 --mixed-reps 6 --workers 6
python -m planD.overnight.memory --trials 6 --w 3 --workers 4
python -m planD.overnight.coordinator --reps 3 --workers 4
```

Paid stages share the persistent cumulative **$2** cap in `planD/llm.py` and the
existing ledger, including earlier unresolved reservations. Run stages sequentially,
not in parallel. Each model is paced and respects a persisted rate-limit cooldown;
failed episodes are not silently retried. Commands above produce new independent
samples and charges; report generation commands below are offline.

The active overnight sequence is `python -m planD.overnight.follow_on --study-run
20261107T080958276252Z-v2`. It waits for that study, then runs memory and the
coordinator probe sequentially if sufficient conservative headroom remains. It
has a finite three-hour wait bound and exits when those stages finish; it is not
a permanent instruction-file monitor.

After the sequence completes, regenerate the handoff without model calls:

```bash
python -m planD.overnight.build_handoff --study-run 20261107T080958276252Z-v2
python -m planD.overnight.demo
python -m planD.overnight.analyze
```

The handoff builder uses the locally available PyMuPDF package (`fitz`) for its PDF.
The demo replays recorded illustrative cases and makes no API calls or database changes.
The analysis command regenerates reports from the handoff's recorded runs and
needs no API key. Precomputed task embeddings let the embedding replay run with
NumPy only; PyTorch/Transformers are needed only to recompute those embeddings.

The optional CPU encoder step is `python -m planD.overnight.embedding_replay
--embed-only`. It anonymously downloads a pinned public generic encoder, uses no
GPU, and makes no OpenRouter requests. This is a secondary counterfactual replay,
not a live embedding-guard experiment or an intent-trained method.
The experiment dependencies remain requests, NumPy and matplotlib. A PDF-capable
reproduction environment can install `PyMuPDF` separately if needed.

## Measurement contract

- `TASK_BANK.json`: 96 frozen requests; 48 action intents; two variants per intent;
  twelve families; 48 allowed/48 forbidden. `TASK_BANK_AUDIT.json` includes its hash.
- `environment.py`: explicit fixed-principal policy, bounded action grammar,
  parameterized SQLite execution and per-action verification. An access-policy
  check labels actual effects; it is not enforced by the executor. Scope guards
  can block before execution when a refusal matches.
- `study.py`: fresh-pool and history-retaining retry comparisons. Calibration
  includes failures; primary rates retain every completed episode. Family-clustered
  intervals keep related wording/intent examples together.
- `memory.py`: all 48 intents appear once per wording pass. AB/BA order is balanced
  across trials. Exact, lexical, and model-produced tool-scope ledgers are compared
  with no memory. Hidden canonical actions and labels never enter a matcher.
- `coordinator.py`: decisions after an identical scripted refusal. The pressure
  condition changes; no database action or live worker delegation executes.
- `report.py`: both a continue-after-nonviolation independence reference and an
  absorbing-error reference, plus complete-case and worst-case failure sensitivity.

## Do not pool unlike protocols

v2 explicitly permits public employee IDs, audit reads and authorized ticket
edits/deletes, and removes arbitrary SQL. That is a policy/interface change from
v1. Comparisons across versions are descriptive, not a causal interface ablation.
The permission metric is a fixed role-based policy, not a full model of consent
for every additional action outside the user's requested work.

Two v2 launches stopped during interface diagnostics. They are preserved as
`20261107T080457234078Z-v2` and `20261107T080627520471Z-v2`. The common output
instruction was then clarified with a seven-key example and a short reason limit.
The task bank and labels were unchanged. The final broad dataset starts at
`20261107T080958276252Z-v2`. Do not combine diagnostic rows with that dataset.

Each live run saves source snapshots before calls. Analysis code snapshots are
also saved by the v2 report generator. Raw model responses/database values are
not needed to audit the action verdicts. The actual API credential stays outside
the handoff archive and model prompts.
