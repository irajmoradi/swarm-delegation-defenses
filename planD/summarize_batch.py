"""Create one reviewable batch overview without pooling incompatible protocols."""
import argparse
from datetime import datetime, timezone
import json

from .llm import Budget, CAP, ROOT


def read_json(path):
    return json.loads(path.read_text())


def jsonl(path):
    return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', required=True)
    parser.add_argument('--diversity', required=True)
    parser.add_argument('--ledger', required=True)
    args = parser.parse_args()
    paths = {kind: ROOT/'runs'/getattr(args,kind) for kind in ['pilot','diversity','ledger']}
    summaries = {kind:read_json(path/'summary.json') for kind,path in paths.items()}
    if any(s['finish']['status']!='complete' for s in summaries.values()):
        raise ValueError('All selected experiment stages must be complete.')
    all_calls = {}
    for path in (ROOT/'runs').glob('*/calls.jsonl'):
        for record in jsonl(path):
            all_calls[record['id']] = record
    latest = {}
    for r in jsonl(ROOT/'budget.jsonl'):
        latest[r['id']] = r
    unknown = [r for r in latest.values() if r['event']=='reserve']
    reported = sum(c.get('cost_usd') or 0 for c in all_calls.values())
    stages = {}
    for kind,path in paths.items():
        rs = jsonl(path/'episodes.jsonl')
        calls = jsonl(path/'calls.jsonl')
        if kind=='pilot':
            main = [r for r in rs if not r['panel']]
            calibration = sum(len(r['attempts']) for r in rs if r['panel'])
        elif kind=='diversity':
            main = [r for r in rs if r['phase']=='main']
            calibration = sum(len(r['attempts']) for r in rs if r['phase']=='cal')
        else:
            main, calibration = rs, 0
        stages[kind] = {'run':path.name,'main_task_episodes':len(main),'calibration_draws':calibration,
                        'calls':len(calls),'reported_cost_usd':sum(c.get('cost_usd') or 0 for c in calls),
                        'operational_flags':len(jsonl(path/'flagged.jsonl')),
                        'violations_on_allowed_requests':sum(r['violation'] for r in main if r['kind']=='benign')}
    data = {'created_utc':datetime.now(timezone.utc).isoformat(),'cap_usd':CAP,
            'cumulative_accounted_usd':Budget().total(),'cumulative_reported_usd':reported,
            'cumulative_logged_calls':len(all_calls),'unknown_charge_reservations':len(unknown),
            'cumulative_request_attempts':len(latest),
            'stages':stages,'diversity_cells':summaries['diversity']['cells'],
            'ledger_cells':summaries['ledger']['cells'],
            'note':'Stages are reported separately; pilot and diversity use different action protocols.'}
    (ROOT/'batch_summary.json').write_text(json.dumps(data,indent=2))
    pct=lambda value:f'{100*value:.1f}%'
    div = summaries['diversity']['cells']
    mem = summaries['ledger']['cells']
    lines=['# Plan D: expanded experiment results','',
           f'Authorized cumulative cap: **${CAP:.2f}**. Reported cumulative model charges: '
           f'**${reported:.6f}** across **{len(latest):,} request attempts** ({len(all_calls):,} logged completion records). '
           f'Conservative budget accounting: ${data["cumulative_accounted_usd"]:.6f}; '
           f'{len(unknown)} unresolved charge reservations. These totals include smoke, diagnostic and superseded runs.','',
           'All tasks use synthetic records and explicit toy database access rules. Model-generated actions are verified from SQL results and database state.','',
           '## Completed stages','',
           '| Stage | Main task episodes | Calibration draws | API calls | Reported stage cost | Operational flags |',
           '|---|---:|---:|---:|---:|---:|']
    for kind,s in stages.items():
        lines.append(f'| {kind} | {s["main_task_episodes"]:,} | {s["calibration_draws"]:,} | '
                     f'{s["calls"]:,} | ${s["reported_cost_usd"]:.6f} | {s["operational_flags"]} |')
    lines += ['', 'The native-tool pilot, JSON-action diversity grid, and separate matched-task memory experiment '
              'are not pooled into a single violation estimate.','',
              '## Model diversity and repeated attempts','',
              '| Family/pool | W=1 fresh | W=3 fresh | W=6 fresh | W=3 retry | W=6 retry |',
              '|---|---:|---:|---:|---:|---:|']
    for pool in ['gpt','qwen','mistral','mixed']:
        values=[]
        for strategy,w in [('reroute',1),('reroute',3),('reroute',6),('retry',3),('retry',6)]:
            cell=next((c for c in div if c['pool']==pool and c['strategy']==strategy and c['w']==w and c['ledger']=='none'),None)
            values.append(pct(cell['violation_rate']) if cell else '—')
        lines.append(f'| {pool} | '+ ' | '.join(values)+' |')
    lines += ['', 'Rates are forbidden-task episodes with at least one observed violation. Each fresh-pool '
              'cell has 72 forbidden episodes across 12 tasks; the mixed W=3/6 pools use all three model families. '
              'Mixed order rotates through six permutations. Complete task-bootstrap intervals and paired '
              'contrasts are in the diversity report.','']
    mixed_highest=[]
    for w in [3,6]:
        selected=[c for c in div if c['w']==w and c['strategy']=='reroute' and c['ledger']=='none']
        mix=next(c for c in selected if c['pool']=='mixed')
        same=[c['violation_rate'] for c in selected if c['pool']!='mixed']
        mixed_highest.append(mix['violation_rate']>max(same))
    if all(mixed_highest):
        lines.append('Mixed pools have the highest point estimates at both attempt budgets in this dataset; wide task-level intervals and model differences limit the inference.')
    else:
        lines.append('Mixed pools are not consistently worse than every same-family pool in this dataset. The broad claim that model diversity always produces the largest violation rate is not established.')
    lines += ['', '## Refusal memory across requests','',
              '| Memory | Forbidden-request violation | Allowed success | Allowed requests blocked by ledger |',
              '|---|---:|---:|---:|']
    for c in mem:
        lines.append(f'| {c["mode"]} | {pct(c["violation_rate"])} | {pct(c["allowed_success_rate"])} | {pct(c["false_block_rate"])} |')
    lines += ['', 'Each memory arm has 144 forbidden and 144 allowed task episodes, grouped into six independent '
              'trials. Exact memory shares refusals for identical requests. Lexical memory uses TF-IDF cosine '
              'with a fixed 0.55 threshold, not an embedding or intent-trained model. Similar wording can confuse '
              'permissions for user_id=1 and user_id=2. Trial-bootstrap intervals and paired differences are '
              'in the memory report.','',
              '## Evidence and limits','',
              f'- Observed violations on allowed requests in the selected main datasets: {sum(s["violations_on_allowed_requests"] for s in stages.values())}.',
              '- These are exploratory synthetic experiments. Few unique tasks, six diversity repetitions, and six memory trials limit generalization. Nominal intervals are not adjusted for multiple comparisons.',
              '- Each model uses a pinned DeepInfra endpoint without fallbacks; sizes, quantization, and reasoning settings still differ. The earlier native-tool pilot varies providers and is kept separate.',
              '- The verifier covers protected literal SQL results and state mutations, including unauthorized ticket ownership. It does not cover arbitrary encodings, aggregates, or changes restored before a final snapshot.',
              '- Operational failures are recorded separately. The diversity/memory primary rates retain completed episodes including failures; the pilot uses complete-case rates.',
              '- The initial Llama protocol diagnostics and the first memory run with an ambiguous ID-reading control are preserved but excluded from final comparisons. Their costs still count against $2.',
              '- Autonomous coordinator pressure, decomposition, paraphrase adaptation, embeddings, and intent-trained defenses remain untested.','',
              '## Artifacts','',
              f'- Native-tool pilot: `planD/runs/{paths["pilot"].name}/RESULTS.md`.',
              f'- Diversity: `planD/runs/{paths["diversity"].name}/RESULTS.md`; plot `violation_vs_w.png`.',
              f'- Corrected memory experiment: `planD/runs/{paths["ledger"].name}/RESULTS.md`; plot `ledger_tradeoff.png`.',
              '- Each run retains configurations, per-episode verdicts, output hashes, token/cost records, individual flags, and machine-readable statistics. Main experiment source snapshots are hash-verified.',
              '- Commands and methodology: `planD/README.md` and `planD/EXPERIMENT_DESIGN.md`.', '']
    (ROOT/'EXPANDED_RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps({k:data[k] for k in ['cumulative_reported_usd','cumulative_accounted_usd','cumulative_logged_calls','unknown_charge_reservations']},indent=2))


if __name__=='__main__':
    main()
