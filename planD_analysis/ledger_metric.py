"""Standalone re-implementation of planD/overnight/memory_report.py metrics (same seeds).
Usage: python3 -I ledger_metric.py <run_dir>   (reads episodes.jsonl only; writes nothing)"""
import json,sys
import numpy as np
rows=[json.loads(l) for l in open(sys.argv[1]+'/episodes.jsonl')]
for r in rows:r['safe_success']=bool(r['success'] and not r['violation'])
def trial_stats(rs,field):
    means=[float(np.mean([r[field] for r in rs if r['trial']==t])) for t in sorted({r['trial'] for r in rs})]
    if not means:return None,None
    d=np.random.default_rng(20261126).choice(means,size=(4000,len(means)),replace=True).mean(axis=1)
    return float(np.mean(means)),np.quantile(d,[.025,.975]).tolist()
pct=lambda x:'n/a' if x is None else f'{100*x:.1f}%'
modes=sorted({r['mode'] for r in rows},key=['none','exact','lexical','scope'].index)
trials=sorted({r['trial'] for r in rows})
for m in modes:
    f=[r for r in rows if r['mode']==m and r['kind']=='forbidden'];b=[r for r in rows if r['mode']==m and r['kind']=='benign']
    v,ci=trial_stats(f,'violation');blk,_=trial_stats(b,'ledger_block');ss,_=trial_stats(b,'safe_success')
    perpass=[pct(trial_stats([r for r in f if r['pass_index']==p],'violation')[0]) for p in sorted({r['pass_index'] for r in f})]
    print(f'{m:8s} forbidden_n={len(f)} violation={pct(v)} CI=[{pct(ci[0])}, {pct(ci[1])}] allowed_block={pct(blk)} allowed_success={pct(ss)} per-pass={perpass} calls={sum(len(r["attempts"]) for r in f+b)}')
for m in [x for x in modes if x!='none']:
    for kind,field in [('forbidden','violation'),('benign','ledger_block')]:
        diffs=[]
        for t in trials:
            a=[float(np.mean([r[field] for r in rows if r['mode']==mm and r['trial']==t and r['kind']==kind])) for mm in [m,'none']]
            diffs.append(a[0]-a[1])
        s=np.random.default_rng(20261127).choice(diffs,size=(4000,len(diffs)),replace=True).mean(axis=1)
        q=np.quantile(s,[.025,.975])
        print(f'  {m}-none {field}: {pct(float(np.mean(diffs)))} [{pct(q[0])}, {pct(q[1])}]')
