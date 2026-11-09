# Linking-problem pilot

This is a cut-down pilot of the "Linking Problem" spec (hello_world42 / Mario). It asks whether a cheap
text-similarity linker, followed by a joint LLM review of the linked commits, beats per-commit monitoring
at a fixed sequence-level false-positive rate. It then checks how that holds up as benign noise
increases. Results are in `PILOT_RESULTS.md`.

Everything here is toy data. The 3-service mini-repo is fake. The attacks are inert config, label or
allow-list edits that use the reserved `.example` TLD. Nothing runs against a real system.

## Layout
```
src/repo_gen.py    builds data/repo (16 files, ~340 lines, git-initialised)
src/tasks.py       65 hand-written ordinary engineering tasks (benign generator prompts)
src/attacks.py     6 toy chains x K=3 (hand-written malicious hunks) + rename-perturbation map
src/gen.py         LLM generation of benign commits and of the legit part of attack commits (same prompt);
                   LLM diffs are applied to the base files and re-rendered by difflib, so both classes
                   share one diff format; attack hunks are applied on top
src/linker.py      file-Jaccard + identifier-Jaccard + TF-IDF cosine linker (top-3, label-free tau)
src/experiment.py  sequences (attack / calibration / held-out benign), monitor calls, per-sequence scores
src/analysis.py    thresholds per method per N, detection@1/2/5% FPR, AUC, linking recall, bootstrap
                   CIs (whole chains + calibration seqs resampled), leakage check, figure
src/llm.py         OpenRouter client: jsonl cache (prompt hash), per-call log, spend ledger, hard cap
```
Logs: `results/run_log.jsonl` (every call, cached or paid), `results/spend_ledger.jsonl` (paid calls),
`cache/llm_cache.jsonl` (responses). Reruns are served from the cache at $0 and give identical results.

## Run (pilot)
```
export PY="env PYTHONNOUSERSITE=1 $HOME/miniconda3/envs/swarm/bin/python"
$PY src/repo_gen.py
$PY src/gen.py --stub && $PY src/experiment.py --stub     # free dry run + cost estimate
$PY src/gen.py                                             # ~213 calls to openai/gpt-5-mini
$PY src/experiment.py --noise 0 10 --n-cal 100 --n-eval 100
$PY src/analysis.py
```
Release: the key is read from the env var `OPENROUTER_API_KEY`, or the file named by `OPENROUTER_KEY_FILE` (see the top-level README). It is never printed.
The hard cap is `CAP_USD` in `src/llm.py`. It is checked against the ledger before every paid call.

## Extending to the full spec
1. **Noise 50.** Run `experiment.py --noise 0 10 50`. Cached N=0/10 calls are free. For N=50, the
   linked-joint calls on 200 benign sequences of 53 commits cost roughly 4-5x the N=10 cost. You can
   cut `--n-cal/--n-eval` to save money, but 1% FPR then becomes coarse.
2. **More arrangements and chains.** Set `N_ARR` in `experiment.py`. Add chains to `attacks.py` (check
   that each edit anchor is an exact existing line). Have a second person review that no single commit
   carries the whole goal.
3. **Window-joint baseline (spec method 3)** is not implemented. Add it in `experiment.py` as one joint
   call per window of the last W commits. It is the most expensive method.
4. **Linker tuning.** Weights are fixed at 1/3 each. tau is the 90th percentile of benign-benign pair
   scores from the calibration pool, so it is set without labels. The spec asks to tune on a separate
   dev set of attack-like chains, which does not exist yet.
5. **Adaptive red team (Experiment C)** was skipped on purpose. The only perturbation here is
   rule-based renaming of the identifiers shared within a chain (`RENAMES`). If a later round is run,
   report evasion recipes only at a high level (spec, Appendix A).
6. **Repo-aware monitor, LLM linker, metadata features:** these are stretch goals and are not built.
7. **Leakage.** `analysis.py` reports a 5-fold CV AUC of a logistic model on trivial diff features.
   Regenerate the data if it is well above 0.5.

## Round 2 commands
```
$PY src/fix_attacks.py                                    # regenerate anchor-fallback attack commits
$PY src/experiment2.py --stage tags                       # LLM-tag linker features (1 call / commit)
$PY src/experiment2.py --stage recall --noise 0 10        # linking recall, all linkers (free)
$PY src/experiment2.py --stage score --noise 0  --n-cal 200 --n-eval 60 --tag _N0
$PY src/experiment2.py --stage score --noise 10 --n-cal 200 --n-eval 30 --tag _N10
$PY src/analysis2.py results/r2_scores_N0.json results/r2_scores_N10.json
```
Add `--estimate-only` to any score or tags stage to print the uncached call count and a cost estimate.
The estimator under-counts joint-call output by about 1.7x. `--window 5` adds the window-joint
baseline; it was not run.

## Round 3 commands
```
$PY src/experiment3.py --stage effects                     # effect summaries (1 mini call / commit)
$PY src/experiment3.py --stage recall                      # recall for all linkers + top-k + 2-hop (free)
$PY src/experiment3.py --stage diagnose                    # missed-pair taxonomy table + figure (free)
$PY src/group_stats.py                                     # group sizes / benign linkage (free)
$PY src/experiment3.py --stage score --noise 0 10 --linkers dep dep_hop2 effect sens --tag _main
$PY src/analysis3.py                                       # merges r2 + r3 rows by sequence id
```

## Round 4 commands
```
$PY src/feature_gen.py                                     # 18 benign multi-commit features (cumulative state)
$PY src/experiment4.py --stage effects                     # effect summaries for feature + adaptive commits
$PY src/experiment4.py --stage metrics                     # dependency gap, linkage, recall, 2-hop fixes (free)
$PY src/experiment4.py --stage score --linkers dep dep_hop2sens effect --tag _main
$PY src/analysis4.py
```
The adaptive attacker is `adaptive()` in `src/experiment4.py`. Rule-based and semantics-preserving; describe it only at a high level.

## Round 5 commands
```
$PY src/dev5.py                                            # items 1-4 on round-4 scores (dev split; free)
$PY src/feature_gen_x.py                                   # 10 benign cross-agent features
$PY src/experiment5.py --stage structured                  # effect + structured summaries for new commits
$PY src/experiment5.py --stage dev                         # free variant selection (boundary / structured)
$PY src/experiment5.py --stage score --linkers boundary_union struct7_S2 --newq boundary_union --tag _fresh
$PY src/fresh5.py                                          # one-shot fresh-split evaluation + figure
```

## Round 6 commands
```
$PY src/gen6.py                       # 36 new toy chains (attacks2.py) + 65 new benign v3 commits
$PY src/experiment6.py                # round-5 calibration + fresh one-shot test: per-commit, boundary, dep, oracle
$PY src/llm_attacker.py               # LLM-adaptive rewrites (sees only the per-commit policy text)
$PY src/r6_llm_score.py               # score the LLM-adaptive variant on the same arrangements
$PY src/analysis6.py                  # matched-FPR, paired bootstrap (chains and patterns), McNemar, figure
```
