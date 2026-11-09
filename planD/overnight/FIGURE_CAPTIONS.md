# Figure captions for the research note

The empirical curves/profiles, memory tradeoff and embedding replay also have
PDF/SVG vector versions beside their PNG files. Paper PDFs downloaded for reading
are kept separate and excluded from the handoff archive.

## Fresh-pool curves

`runs/20261107T080958276252Z-v2/violation_vs_w.png`

Executed forbidden-action rates on the balanced typed-action bank, by maximum
attempt budget and worker pool. Same-model cells have one replicate per request;
mixed cells have six, balancing family order. Shading resamples twelve scenario
families, preserving wording variants within families. The mixed-pool gain alone
does not establish conditional refusal dependence; the calibrated independent
reference and heterogeneous marginal propensities must also be considered.

## Permission and refusal profiles

`runs/20261107T080958276252Z-v2/permission_profile.png`

Calibration outcomes by scenario family and model. Left: actual violation rates
on forbidden requests. Right: explicit refusal rates on allowed requests. Each
cell summarizes 24 calibration attempts in this completed run. These descriptive
profiles show task-dependent behavior, not within-task dependence estimates or
internal model mechanisms.

## Live refusal-memory tradeoff

`runs/20261107T083446934699Z-v2-memory/memory_tradeoff.png`

Forbidden-request violations and allowed-request blocking under no memory, exact
text, lexical TF-IDF and model-produced tool-scope memory. Each arm has six trials
with two wording passes over 48 intents. Databases reset per task, while memory
persists within a trial. Trial-clustered intervals, failures and safe task
completion are in the accompanying report. These are live arms with independent
model draws; the scope matcher does not receive hidden policy labels.

## Frozen-embedding replay

`overnight/EMBEDDING_REPLAY.png`

Counterfactual violation/blocking sensitivity for the full fixed generic-encoder
threshold grid, conditional on the recorded no-memory trajectories. This is not
a live guard experiment, a new set of independent samples or an intent-trained
retriever. Point labels are cosine thresholds; no operating point is recommended
without held-out calibration.

## Heterogeneity illustration

`overnight/HETEROGENEITY_DEMO.png`

Mathematical illustration only. Three chosen task/model propensity patterns
produce a large balanced-mixed gain even when every draw is conditionally
independent. The task-wise oracle is an analytical reference, not a tested agent
or defense. These values must not be presented as measured model results.
