# Synthetic access-control bank v2

## Contents and construction

- 96 plain requests: 48 allowed, 48 forbidden.
- 48 canonical action intents, each with two templated wording variants.
- Twelve families, each with two allowed/two forbidden intents (eight requests).
- Fixed acting principal Alice, user_id=1; six synthetic employee records,
  three dummy service-key records, ten audit entries and two seeded tickets.
- Sources: the local Plan D fake fixture and deterministic construction code;
  no production records or harmful-content benchmark prompts are used.

Requests cover private-field reads, public directories, ticket ownership and
edits/deletes/creation, protected edits, audit actions and dummy service keys.
The typed interface accepts bounded read/update/delete/create operations and
refusal. It does not support arbitrary SQL, expressions, encodings or tool names.

`TASK_BANK.json` contains IDs, family, intent, variant, request, label and canonical
action. `TASK_BANK_AUDIT.json` records the canonical sorted-JSON SHA-256:

`070d2db6c68badd8e2542a4698353c0d17b35a58cb8bdc4e13211189b197afd8`

## Labels and model visibility

“Forbidden” is defined by the explicit fixed role policy in `environment.py`.
Every canonical action is executed against that policy in the label audit.
Allowed canonical actions must also satisfy the task-success verifier.
This is executable consistency checking, not an independent human annotation study.

Workers see the common policy, action schema and rendered request. They do not
receive task IDs, permission labels or canonical answers. Model-produced scopes
can be wrong; invalid arguments and operational failures are recorded separately.
Safe completion requires completing the requested work without a policy violation.

## Splits and dependence

There is no general-purpose train/test split. Both variants enter the live study;
the memory study reverses AB/BA order across trials. The secondary retrieval
diagnostic uses A as candidate bank and B as query texts. The frozen encoder is
not fine-tuned; lexical IDF uses all known task texts without permission labels.
No threshold is claimed to generalize beyond this fixed suite.

The 96 strings are not 96 independent scenarios. Related wording/intent examples
remain grouped in twelve family clusters for the main analysis; memory intervals
resample whole trials. Repeated calls do not create new independent task families.

## Limits and intended use

This bank supports a reproducible toy study of role permissions, post-refusal
routing and negative-memory tradeoffs. It does not model full user consent for
extra role-permitted actions, changing principals/grants, unbounded SQL,
long-horizon workflows, natural adversarial paraphrases, or general misuse
capabilities. Databases reset per request, while refusal memory may persist.

The earlier SQL studies and failed interface preflights are distinct datasets.
Do not pool them as replicas of this task/policy surface. The local handoff
provides sources, per-request outcomes and source snapshots; it never includes
the actual OpenRouter credential.
