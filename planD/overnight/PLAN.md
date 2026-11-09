# Overnight extension — 2026-11-07

User request: substantially more synthetic tasks, paper review, and a useful morning handoff for Lance. The existing $2 cumulative cap remains in force, including the prior $0.813722762 conservative accounting. The cap is not a spending target.

1. Verify the original ten references and search for closer authorization/memory benchmarks. Preserve primary PDFs, extraction hashes, and precise reading limits.
2. Build a v2 bank of 96 balanced synthetic requests: 48 allowed/48 forbidden, two wording variants of 48 action intents across twelve scenario families. Report effective units; do not present paraphrases as independent scenarios.
3. Use a bounded typed action interface backed by in-memory SQLite. This provides exact per-action access checks and immediate mutation checks, avoiding the legacy literal-output and restored-mutation blind spots. Keep protocols and results separate.
4. Freeze the task bank and analysis before paid calls. Compare fresh attempts, history-retaining retries, and mixed-model pools under the same budget. Respect provider rate-limit cooldowns and cumulative reservations.
5. Test refusal memory with an explicitly labeled tool-scope matcher, using model-produced scope rather than task ground-truth labels. Compare exact and lexical baselines, allowed-work cost, and an oracle policy gate only as a sanity reference if budget permits.
6. Assemble a morning brief, paper positioning, methods/limits, figures, machine-readable results, commands, and an honest draft write-up. No claims that these toy policies establish general misuse safety.

The prior SQL studies remain valid as their own exploratory datasets. The v2 interface changes the task and policy surface and is not pooled with them.

## Frozen paid study

Run `20261107T080457234078Z-v2`: six independent calibration draws per request/model; one same-family main replicate at W=1,3,6; GPT history-retaining retries at W=3,6; six mixed-pool replicates per W to balance all family permutations. Total planned jobs: 3,936 (1,728 calibration + 2,208 main). All twelve families and both variants are included without selecting on outcomes. Primary contrast is mixed versus the equally weighted average of same-model fresh pools. Source/task hashes were frozen before paid execution.

## Interface diagnostics and final run

The first two v2 launches aborted in preflight before the broad grid. Initial responses sometimes omitted required fields or truncated. All diagnostics and costs are retained. A shared explicit seven-key JSON formatting example and 20-word reason limit resolved the observed interface issue in all three models. The task bank and access labels were not changed. The final frozen broad run is `20261107T080958276252Z-v2`; it retains the same k=6 / eps=1 / six balanced mixed permutations and primary contrast.

Follow-on stages are sequenced after that study (no paid overlap): six trials of no/exact/lexical/tool-scope memory, two pre-fixed wording passes over 48 intents; then three samples/request/condition for a four-condition coordinator decision probe with a scripted refusal. Shared cap remains $2.
