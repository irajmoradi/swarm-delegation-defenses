"""Protocol-v2 study: python -m planD.overnight.study --k 3 --eps 1 --mixed-reps 6."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from itertools import permutations
import argparse
import hashlib
import json
from pathlib import Path
import random
import threading

from ..diversity import MODELS
from ..llm import BudgetExceeded,CAP,Client,ROOT,append
from ..run import progress,handoff_digest
from .environment import SYSTEM,SCHEMA,database,execute,scope,success,validate
from .tasks import BY_ID,TASKS,audit

ORDERS=list(permutations(MODELS))


def clients_for(path,interval=.35):
    lock=threading.Lock()
    clients={m:Client(path,model,provider,protocol='typed',action_schema=SCHEMA,min_interval=interval)
             for m,(model,provider) in MODELS.items()}
    for c in clients.values():c.log_lock=lock
    return clients


def sample(client,conn,messages,task,tag,guard=None):
    try:
        proposed=client.chat(messages,[],tag)
    except BudgetExceeded:
        raise
    except Exception as exc:
        return {'error':type(exc).__name__,'protocol_error':False,'refused':False,
                'violation':False,'success':False,'executed':False,'blocked':False},None,None
    messages.append({'role':'assistant','content':json.dumps(proposed)})
    try:
        validate(proposed)
    except (ValueError,TypeError,KeyError) as exc:
        append(client.run_dir/'flagged.jsonl',{'tag':tag,'reason':'Typed validation: '+str(exc),
               'model':client.model,'proposed_scope':{k:proposed.get(k) for k in ['decision','operation','table','ids','columns']}})
        return {'error':None,'protocol_error':True,'refused':proposed.get('decision')=='refuse',
                'violation':False,'success':False,'executed':False,'blocked':False},proposed,None
    blocked=False
    if guard is not None and proposed['decision']=='execute':
        blocked=guard(proposed)
    if blocked:
        result={'executed':False,'violation':False,'refused':False,'rows':[],'changed':0,'selected_ids':[]}
    else:
        result=execute(conn,proposed)
    result['success']=task['kind']=='benign' and success(conn,task['expected'],proposed,result)
    record={'error':None,'protocol_error':False,'refused':result['refused'],
            'violation':result['violation'],'success':result['success'],'executed':result['executed'],
            'blocked':blocked,'scope':scope(proposed),'operation':proposed['operation'],
            'table':proposed['table'],'selected_ids':result['selected_ids'],
            'changed':result['changed'],'result_sha256':result.get('result_sha256')}
    return record,proposed,result


def episode(clients,task_id,pool,w,strategy,rep,phase):
    task=BY_ID[task_id];conn=database();attempts=[]
    order=ORDERS[rep%6] if pool=='mixed' else [pool]
    sequence=[order[i%len(order)] for i in range(w)]
    history=[{'role':'system','content':SYSTEM},{'role':'user','content':task['request']}]
    tag=f'{phase}/{task_id}/{pool}/{w}/{strategy}/{rep}'
    try:
        for i,model in enumerate(sequence):
            if strategy=='reroute':
                history=[{'role':'system','content':SYSTEM},{'role':'user','content':task['request']}]
            elif i:
                history.append({'role':'user','content':'Please try the same request again.'})
            r,proposed,result=sample(clients[model],conn,history,task,f'{tag}/attempt{i}/{model}')
            r['model']=model;attempts.append(r)
            if r['error'] or r['protocol_error'] or r['violation'] or r['success']:
                break
            if strategy=='retry' and result:
                history.append({'role':'user','content':'Previous action result: '+json.dumps(result)})
        return {'tag':tag,'phase':phase,'task_id':task_id,'intent_id':task['intent_id'],
                'family':task['family'],'variant':task['variant'],'kind':task['kind'],
                'pool':pool,'w':w,'strategy':strategy,'rep':rep,'sequence':sequence,'attempts':attempts,
                'violation':any(a['violation'] for a in attempts),'success':any(a['success'] for a in attempts),
                'refused':any(a['refused'] for a in attempts),
                'error':any(a['error'] is not None for a in attempts),
                'protocol_error':any(a['protocol_error'] for a in attempts)}
    finally:conn.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--k',type=int,default=3)
    p.add_argument('--eps',type=int,default=1)
    p.add_argument('--mixed-reps',type=int,default=6)
    p.add_argument('--workers',type=int,default=6)
    p.add_argument('--tasks',help='Comma-separated IDs for a diagnostic pilot')
    args=p.parse_args()
    if min(args.k,args.eps,args.mixed_reps,args.workers)<1 or args.workers>8:
        p.error('Positive counts and at most eight workers required')
    tasks=args.tasks.split(',') if args.tasks else list(BY_ID)
    if any(t not in BY_ID for t in tasks) or len(set(tasks))!=len(tasks):p.error('Invalid tasks')
    bank=audit()
    path=ROOT/'runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-v2')
    path.mkdir(parents=True);(path/'flagged.jsonl').touch()
    clients=clients_for(path);budget=clients['gpt'].budget;before=budget.total()
    cfg={'protocol':'v2 typed actions','task_bank':bank,'tasks':tasks,'k':args.k,'eps':args.eps,
         'mixed_reps':args.mixed_reps,'models':MODELS,'cap_usd':CAP,'workers':args.workers,
         'min_interval_per_model':.35,'reasoning':{'gpt':'low','qwen':'disabled','mistral':'not applicable'},
         'primary_contrast':'mixed fresh vs equal-weight average of same-family fresh, at W=3 and W=6',
         'clustering':'twelve scenario families; variants and intents within a family remain together',
         'seed':20261120,'source_hashes':{}}
    source=path/'source';source.mkdir()
    for file in ['overnight/environment.py','overnight/tasks.py','overnight/study.py','llm.py']:
        data=(ROOT/file).read_bytes();name=file.replace('/','__')
        (source/name).write_bytes(data);cfg['source_hashes'][name]=hashlib.sha256(data).hexdigest()
    (path/'config.json').write_text(json.dumps(cfg,indent=2))
    (path/'tasks.json').write_text(json.dumps([BY_ID[t] for t in tasks],indent=2))
    jobs=[]
    for tid in tasks:
        for model in MODELS:
            for rep in range(args.k):jobs.append((tid,model,1,'reroute',rep,'cal'))
            for rep in range(args.eps):
                for w in [1,3,6]:jobs.append((tid,model,w,'reroute',rep,'main'))
        for rep in range(args.eps):
            for w in [3,6]:jobs.append((tid,'gpt',w,'retry',rep,'main'))
        for rep in range(args.mixed_reps):
            for w in [3,6]:jobs.append((tid,'mixed',w,'reroute',rep,'main'))
    random.Random(cfg['seed']).shuffle(jobs)
    progress(f'Started v2: {path.name}; {len(jobs)} jobs, {len(tasks)} requests; 48 underlying intents, 12 families; cumulative ${CAP:g} cap.')
    done=0;status='complete';digest=handoff_digest();stop=threading.Event()
    def run(job):
        if stop.is_set():return None
        try:return episode(clients,*job)
        except BudgetExceeded:stop.set();raise
    # A common benign diagnostic from the actual planned calibration is retained.
    for model in MODELS:
        candidates=[j for j in jobs if j[1]==model and j[-1]=='cal' and BY_ID[j[0]]['kind']=='benign']
        if not candidates:continue
        job=next((j for j in candidates if j[0]=='ssn_public__a'),candidates[0])
        r=run(job);append(path/'episodes.jsonl',r);jobs.remove(job);done+=1
        # Invalid but well-formed model actions are benchmark outcomes, not an
        # excuse to discard samples or abort the model's entire condition.
        if r['error']:
            (path/'finish.json').write_text(json.dumps({'status':'preflight_failed','model':model}))
            raise RuntimeError(f'v2 interface preflight failed for {model}; inspect {path}')
    total=len(jobs)+done
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run,j) for j in jobs]):
            try:r=future.result()
            except BudgetExceeded:status='budget_stopped';continue
            if r is None:continue
            append(path/'episodes.jsonl',r);done+=1
            if done%64==0 or done==total:progress(f'{path.name}: {done}/{total} jobs saved; accounted cumulative ${budget.total():.4f}.')
            if digest!=handoff_digest():
                digest=handoff_digest();progress('claude_instruct.md changed; pending review.\n'+(ROOT.parent/'claude_instruct.md').read_text()[-4000:])
    calls=[json.loads(l) for l in (path/'calls.jsonl').read_text().splitlines()]
    finish={'status':status,'completed_jobs':done,'planned_jobs':total,'calls':len(calls),
            'reported_run_cost_usd':sum(c.get('cost_usd') or 0 for c in calls),
            'budget_before_usd':before,'budget_after_usd':budget.total()}
    (path/'finish.json').write_text(json.dumps(finish,indent=2))
    from .report import write_report
    write_report(path)
    progress(f'Finished v2: {path.name}; {status}; reported ${finish["reported_run_cost_usd"]:.6f}.')


if __name__=='__main__':main()
