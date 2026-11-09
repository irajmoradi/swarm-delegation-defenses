# Negative-memory context invariants

These are deterministic counterexamples, not measured language-model behavior.
They do not alter or supplement the paid study's outcome counts.

The paid tool-scope matcher is tested only with Alice as the fixed acting user
and a fixed policy. Its key contains the target operation/table/row IDs/columns.
It distinguishes target ownership inside that setting, but does not encode a
changing acting principal or policy version.

| Change after a refusal | Currently allowed? | Scope-only negative cache | Actor + policy-partitioned cache |
|---|---|---|---|
| Alice was denied Bob's SSN; Bob now asks for his own SSN | Yes | Incorrectly blocks | No inherited block |
| Alice was denied row 2; an authorized policy update grants her that row | Yes | Incorrectly blocks | No inherited block |

The script asserts the old denial and new permission and then evaluates the
cache keys. Actor/policy metadata in this illustration is trusted context, not
an assertion supplied by the requester or a model. Partitioning a cache is not
an authorization decision: an actual executor still needs current permission
checks. A refusal-only cache cannot prevent the first forbidden action.

Implications for future experiments:

1. Treat `(acting principal, policy version, operation, resource scope)` as a
   candidate context key, and invalidate stale negative entries when permissions
   change. Test this rather than claiming the fixed-role study covers it.
2. Model-produced selectors can be wrong; record parsing and invalid-action rates.
3. Empty/all-row selectors and explicit ID lists can refer to the same objects
   but differ syntactically. The current matcher does not normalize every alias.
4. Values are excluded only because permissions in this toy policy do not depend
   on value content. Other policies may require additional features.

Reproduce without model calls:

```bash
python -m planD.overnight.cache_invariants
```
