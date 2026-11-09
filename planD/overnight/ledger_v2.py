"""v2 typed protocol + exact-match refusal ledger, v1-ledger design.

python -m planD.overnight.ledger_v2 --trials 6 --passes 3 --w 3 --workers 4

Each trial repeats the SAME wording for every pass (even trial -> variant a, odd -> b), so an
exact ledger can match refusals from earlier passes (as in the v1 ledger's repeated cycles).
Reuses planD.overnight.memory.Memory and study.sample unchanged.

Side effects are limited to: a new planD/runs/<id>-v2-ledger/ directory, plus the shared
planD/budget.jsonl and planD/rate_limits.json written by llm.Client. It does not append to
codex_log.md, does not poll claude_instruct.md, and does not call memory_report.write_report
(which would overwrite overnight/MEMORY_RESULTS.md). Analyse offline from episodes.jsonl.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import argparse,hashlib,json,random

from ..llm import BudgetExceeded,CAP,Client,ROOT,append
from .environment import SYSTEM,SCHEMA,database
from .memory import Memory
from .study import sample
from .tasks import TASKS,BY_ID,audit

MODES={'none','exact'}


def say(message):
    print(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')+': '+message,flush=True)


def run_session(client,mode,trial,w,passes):
    memory=Memory(mode);rng=random.Random(20261124+trial)       # same seed scheme as memory.py
    variant='a' if trial%2==0 else 'b'                          # one wording per trial, repeated
    records=[];intents=sorted({t['intent_id'] for t in TASKS})
    for pass_index in range(passes):
        order=list(intents);rng.shuffle(order)
        for intent in order:
            task=BY_ID[intent+'__'+variant];conn=database();attempts=[];hit=None;blocked=False
            try:
                for i in range(w):
                    hit=memory.precheck(task['request'])
                    if hit:blocked=True;break
                    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':task['request']}]
                    r,proposed,_=sample(client,conn,messages,task,
                                        f'memory/{mode}/{trial}/{pass_index}/{task["task_id"]}/attempt{i}')
                    attempts.append(r)
                    if r['error'] or r['protocol_error']:break
                    if r['refused']:memory.add(task['task_id'],task['request'],proposed)
                    if r['violation'] or r['success']:break
            finally:conn.close()
            records.append({'mode':mode,'trial':trial,'pass_index':pass_index,'variant':variant,
                            'task_id':task['task_id'],'intent_id':intent,'family':task['family'],'kind':task['kind'],
                            'attempts':attempts,'ledger_block':blocked,'block_source':hit['task_id'] if hit else None,
                            'cross_pass_block':bool(hit and not attempts and pass_index>0),
                            'violation':any(a['violation'] for a in attempts),'success':any(a['success'] for a in attempts),
                            'refused':any(a['refused'] for a in attempts),
                            'error':any(a['error'] is not None for a in attempts),
                            'protocol_error':any(a['protocol_error'] for a in attempts)})
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--trials',type=int,default=6);p.add_argument('--passes',type=int,default=3)
    p.add_argument('--w',type=int,default=3);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--modes',default='none,exact')
    a=p.parse_args();modes=a.modes.split(',')
    if min(a.trials,a.passes,a.w,a.workers)<1 or a.workers>6 or not set(modes)<=MODES or len(set(modes))!=len(modes):
        p.error('Positive counts, at most six workers, modes from none,exact')
    path=ROOT/'runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-v2-ledger')
    path.mkdir(parents=True);(path/'flagged.jsonl').touch()
    client=Client(path,provider='deepinfra/bf16',protocol='typed',action_schema=SCHEMA,min_interval=.4)
    before=client.budget.total()
    cfg={'protocol':'v2 typed','experiment':'exact refusal ledger, repeated identical wording (v1-ledger design)',
         'model':client.model,'provider':client.provider,'task_bank':audit(),'trials':a.trials,'w':a.w,
         'passes':a.passes,'variants':'one wording per trial, repeated each pass: even trial=a, odd trial=b',
         'modes':modes,'cap_usd':CAP,'source_hashes':{}}
    src=path/'source';src.mkdir()
    for name in ['overnight/ledger_v2.py','overnight/environment.py','overnight/tasks.py',
                 'overnight/memory.py','overnight/study.py','llm.py']:
        data=(ROOT/name).read_bytes();flat=name.replace('/','__');(src/flat).write_bytes(data)
        cfg['source_hashes'][flat]=hashlib.sha256(data).hexdigest()
    (path/'config.json').write_text(json.dumps(cfg,indent=2))
    jobs=[(m,t) for t in range(a.trials) for m in modes];random.Random(20261125).shuffle(jobs)
    say(f'Started v2 ledger: {path.name}; {len(jobs)} sessions x {48*a.passes} episodes.')
    done=0;status='complete'
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        for fut in as_completed([pool.submit(run_session,client,m,t,a.w,a.passes) for m,t in jobs]):
            try:recs=fut.result()
            except BudgetExceeded:status='budget_stopped';continue
            for r in recs:append(path/'episodes.jsonl',r)
            done+=1;say(f'{path.name}: {done}/{len(jobs)} sessions saved.')
    calls=[json.loads(l) for l in (path/'calls.jsonl').read_text().splitlines()] if (path/'calls.jsonl').exists() else []
    finish={'status':status,'sessions':done,'planned_sessions':len(jobs),'calls':len(calls),
            'reported_run_cost_usd':sum(c.get('cost_usd') or 0 for c in calls),
            'budget_before_usd':before,'budget_after_usd':client.budget.total()}
    (path/'finish.json').write_text(json.dumps(finish,indent=2))
    say(f'Finished v2 ledger: {path.name}; {status}; reported ${finish["reported_run_cost_usd"]:.6f}.')


if __name__=='__main__':main()
