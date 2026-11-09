"""Memory-experiment rates and intervals that preserve whole-session dependence."""
from collections import Counter
import json
from pathlib import Path

import numpy as np


def trial_interval(rows, field):
    trials = sorted({r['trial'] for r in rows})
    means = [np.mean([float(r[field]) for r in rows if r['trial']==trial]) for trial in trials]
    if not means:
        return None
    draws = np.random.default_rng(20261112).choice(means, size=(4000,len(means)), replace=True).mean(axis=1)
    return np.quantile(draws,[.025,.975]).tolist()


def write_report(path):
    path = Path(path)
    cfg = json.loads((path/'config.json').read_text())
    finish = json.loads((path/'finish.json').read_text())
    rows = [json.loads(l) for l in (path/'episodes.jsonl').read_text().splitlines()]
    flags = [json.loads(l) for l in (path/'flagged.jsonl').read_text().splitlines()]
    cells = []
    for mode in cfg['modes']:
        rs = [r for r in rows if r['mode']==mode]
        f = [r for r in rs if r['kind']=='forbidden']
        b = [r for r in rs if r['kind']=='benign']
        rate = lambda group, field: float(np.mean([r[field] for r in group])) if group else None
        cells.append({'mode':mode,'forbidden_n':len(f),'benign_n':len(b),
                      'violation_rate':rate(f,'violation'), 'violation_ci95':trial_interval(f,'violation'),
                      'allowed_success_rate':rate(b,'success'),
                      'allowed_violation_rate':rate(b,'violation'),
                      'allowed_refusal_rate':rate(b,'refused'),
                      'false_block_rate':rate(b,'ledger_block'), 'false_block_ci95':trial_interval(b,'ledger_block'),
                      'cross_task_false_blocks':sum(r['cross_task_block'] for r in b),
                      'mean_attempts':float(np.mean([len(r['attempts']) for r in rs])) if rs else None,
                      'errors':sum(r['error'] for r in rs)})
    block_pairs = Counter((r['mode'],r['block_source_task'],r['task_id']) for r in rows
                          if r['kind']=='benign' and r['ledger_block'])
    contrasts = []
    for mode in ['exact', 'lexical']:
        for kind, field in [('forbidden','violation'), ('benign','ledger_block')]:
            paired = []
            for trial in range(cfg['trials']):
                means = []
                for arm in [mode, 'none']:
                    selected = [r[field] for r in rows if r['mode']==arm and r['trial']==trial and r['kind']==kind]
                    means.append(float(np.mean(selected)) if selected else None)
                if all(m is not None for m in means):
                    paired.append(means[0]-means[1])
            if paired:
                draws=np.random.default_rng(20261113).choice(paired,size=(4000,len(paired)),replace=True).mean(axis=1)
                contrasts.append({'memory':mode,'outcome':field,'difference_vs_none':float(np.mean(paired)),
                                  'paired_session_ci95':np.quantile(draws,[.025,.975]).tolist()})
    summary = {'config':cfg,'finish':finish,'cells':cells,'flag_count':len(flags),
               'paired_contrasts':contrasts,
               'false_block_pairs':[{'mode':k[0],'source':k[1],'blocked_task':k[2],'count':v}
                                    for k,v in block_pairs.most_common()]}
    (path/'summary.json').write_text(json.dumps(summary,indent=2))
    fmt=lambda x:'n/a' if x is None else f'{x:.3f}'
    ci=lambda x:'n/a' if x is None else f'[{x[0]:.3f}, {x[1]:.3f}]'
    lines=['# Plan D: refusal memory across requests','',f'Run: `{path.name}`. Status: {finish["status"]}.','',
           f'Model `{cfg["model"]}`, pinned to `{cfg["provider"]}`, strict JSON actions. '
           f'{cfg["trials"]} trials × {cfg["cycles"]} passes over 16 matched tasks (eight allowed/eight forbidden), W={cfg["w"]}.','',
           f'{finish["calls"]} API calls; reported run cost **${finish["reported_run_cost_usd"]:.6f}**. '
           f'{len(flags)} provider/transport flags. Shared cumulative local cap: ${cfg["cap_usd"]:.2f}.','',
           '| Memory | Forbidden n | Violation rate | Session-bootstrap 95% CI | Allowed success | Allowed refusal | False block | Session-bootstrap 95% CI | Mean attempts | Errors |',
           '|---|---:|---:|---|---:|---:|---:|---|---:|---:|']
    for c in cells:
        lines.append(f'| {c["mode"]} | {c["forbidden_n"]} | {fmt(c["violation_rate"])} | {ci(c["violation_ci95"])} | '
                     f'{fmt(c["allowed_success_rate"])} | {fmt(c["allowed_refusal_rate"])} | {fmt(c["false_block_rate"])} | '
                     f'{ci(c["false_block_ci95"])} | {fmt(c["mean_attempts"])} | {c["errors"]} |')
    lines += ['', '## Paired differences versus no memory', '',
              '| Memory | Outcome | Difference | Paired session-bootstrap 95% CI |', '|---|---|---:|---|']
    for c in contrasts:
        lines.append(f'| {c["memory"]} | {c["outcome"]} | {fmt(c["difference_vs_none"])} | {ci(c["paired_session_ci95"])} |')
    lines += ['', '## False-block examples', '', '| Matcher | Earlier refused task | Allowed task blocked | Count |',
              '|---|---|---|---:|']
    for pair in summary['false_block_pairs'][:12]:
        lines.append(f'| {pair["mode"]} | {pair["source"]} | {pair["blocked_task"]} | {pair["count"]} |')
    lines += ['', '## Interpretation limits', '',
              f'- Observed violations while handling allowed requests: {sum(r["violation"] for r in rows if r["kind"]=="benign")}; these are recorded separately from forbidden-request rates.',
              '- The ledger persists across all requests/cycles in a trial and resets for the next trial. Each task execution gets a fresh synthetic database. Within a task, fresh workers share that task’s DB.',
              '- Arms use the same shuffled request order within a trial. Intervals resample whole trials, preserving dependence caused by shared memory; tasks are a fixed matched suite.',
              f'- Exact matching blocks only an identical previously refused request. Lexical matching uses TF-IDF cosine with threshold {cfg["threshold"]:.2f} fixed before the run, fitted to task texts without labels. It is not an embedding model or intent-trained matching.',
              '- Similarity can confuse permissions: user_id=1 is the authorized user, while user_id=2 is protected. Similar wording is not equivalent authorization.',
              '- False-block rate means the ledger blocked an allowed request. Model refusals are reported separately. Model claims do not count as database actions.',
              '- Exact ledgers cannot prevent a first-attempt violation; a refusal must already be in memory. Costs reflect model calls, not embedding or intent-training costs.',
              '- This is an exploratory synthetic evaluation. Small trial counts and degenerate bootstrap intervals do not establish safety. RQ2 coordinator propensity and general semantic/intent defenses remain untested.',
              f'- Artifacts: `planD/runs/{path.name}/`. No full model outputs or generated SQL are persisted.', '']
    (path/'RESULTS.md').write_text('\n'.join(lines))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.5,4))
    x = np.arange(len(cells))
    for offset, field, ci_field, label in [
        (-.18,'violation_rate','violation_ci95','Forbidden-request violation'),
        (.18,'false_block_rate','false_block_ci95','Allowed-request ledger block')]:
        vals = np.asarray([c[field] for c in cells])
        low = [max(0,c[field]-c[ci_field][0]) for c in cells]
        high = [max(0,c[ci_field][1]-c[field]) for c in cells]
        ax.bar(x+offset, vals, width=.36, label=label, yerr=[low,high], capsize=3)
    ax.set(xticks=x,xticklabels=[c['mode'] for c in cells],ylim=(0,1),ylabel='Rate',
           title='Shared refusal memory: violations and false blocks')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path/'ledger_tradeoff.png',dpi=160)
    plt.close(fig)
