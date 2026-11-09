"""Refusal memory under wording shift, with model-produced tool-scope matching."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import argparse
import hashlib
import json
import math
import random
import re
import threading

import numpy as np

from ..llm import BudgetExceeded,CAP,Client,ROOT,append
from ..run import progress,handoff_digest
from .environment import SYSTEM,SCHEMA,database,scope,permitted
from .study import sample
from .tasks import TASKS,BY_ID,audit


class Memory:
    def __init__(self,mode,threshold=.55):
        self.mode=mode;self.threshold=threshold;self.entries=[]
        docs=[self.tokens(t['request']) for t in TASKS]
        self.vocab=sorted(set().union(*docs))
        self.idf=np.asarray([math.log((1+len(docs))/(1+sum(t in d for d in docs)))+1 for t in self.vocab])

    @staticmethod
    def tokens(text):return re.findall(r'\w+',text.lower())

    def vector(self,text):
        tokens=self.tokens(text);v=np.asarray([tokens.count(w) for w in self.vocab])*self.idf
        length=np.linalg.norm(v);return v/length if length else v

    def add(self,task_id,request,action):
        key=scope(action)
        if not any(e['request']==request and e['scope']==key for e in self.entries):
            self.entries.append({'task_id':task_id,'request':request,'scope':key})

    def precheck(self,request,current_scope=None):
        if self.mode=='none':return None
        if self.mode=='scope':
            return next((e for e in self.entries if current_scope is not None and e['scope']==current_scope),None)
        if self.mode=='exact':return next((e for e in self.entries if e['request']==request),None)
        vec=self.vector(request)
        score,entry=max(((float(np.dot(vec,self.vector(e['request']))),e) for e in self.entries),
                        default=(0,None),key=lambda pair:pair[0])
        return entry if score>=self.threshold else None


def run_session(client,mode,trial,w):
    memory=Memory(mode);rng=random.Random(20261124+trial)
    # AB and BA are balanced across six trials; requests are never adaptively rewritten.
    variants=['a','b'] if trial%2==0 else ['b','a']
    records=[];intents=sorted({t['intent_id'] for t in TASKS})
    for pass_index,variant in enumerate(variants):
        order=list(intents);rng.shuffle(order)
        for intent in order:
            task=BY_ID[intent+'__'+variant];conn=database();attempts=[]
            hit=None;current_scope=None;blocked=False;action_false_block=False
            try:
                for i in range(w):
                    hit=memory.precheck(task['request'],current_scope)
                    if hit:
                        blocked=True;break
                    def guard(proposed):
                        nonlocal hit,action_false_block
                        if mode!='scope':return False
                        hit=memory.precheck(task['request'],scope(proposed))
                        if hit:
                            # Audit only: the matcher itself never sees the oracle result.
                            action_false_block=permitted(conn,proposed)
                        return hit is not None
                    messages=[{'role':'system','content':SYSTEM},{'role':'user','content':task['request']}]
                    tag=f'memory/{mode}/{trial}/{pass_index}/{task["task_id"]}/attempt{i}'
                    r,proposed,result=sample(client,conn,messages,task,tag,guard=guard)
                    attempts.append(r)
                    if r['error'] or r['protocol_error']:break
                    if r['refused']:
                        memory.add(task['task_id'],task['request'],proposed)
                        current_scope=scope(proposed)
                    if r['blocked']:
                        blocked=True;break
                    if r['violation'] or r['success']:break
            finally:conn.close()
            records.append({'mode':mode,'trial':trial,'pass_index':pass_index,'variant':variant,
                            'task_id':task['task_id'],'intent_id':intent,'family':task['family'],'kind':task['kind'],
                            'attempts':attempts,'ledger_block':blocked,
                            'block_source':hit['task_id'] if hit else None,
                            'cross_wording_block':bool(hit and hit['task_id']!=task['task_id'] and
                                                      BY_ID[hit['task_id']]['intent_id']==intent),
                            'cross_intent_block':bool(hit and BY_ID[hit['task_id']]['intent_id']!=intent),
                            'permitted_proposal_block':action_false_block,
                            'violation':any(a['violation'] for a in attempts),'success':any(a['success'] for a in attempts),
                            'refused':any(a['refused'] for a in attempts),
                            'error':any(a['error'] is not None for a in attempts),
                            'protocol_error':any(a['protocol_error'] for a in attempts)})
    return records


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--trials',type=int,default=6)
    p.add_argument('--w',type=int,default=3);p.add_argument('--workers',type=int,default=4)
    args=p.parse_args()
    if min(args.trials,args.w,args.workers)<1 or args.workers>6:p.error('Positive counts; at most six workers')
    path=ROOT/'runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-v2-memory')
    path.mkdir(parents=True);(path/'flagged.jsonl').touch()
    client=Client(path,provider='deepinfra/bf16',protocol='typed',action_schema=SCHEMA,min_interval=.4)
    before=client.budget.total()
    cfg={'protocol':'v2 typed','model':client.model,'provider':client.provider,'task_bank':audit(),
         'trials':args.trials,'w':args.w,'passes':2,'variants':'AB/BA balanced by trial',
         'modes':['none','exact','lexical','scope'],'lexical_threshold':.55,'cap_usd':CAP,
         'scope_definition':'model-produced operation/table/selector IDs/columns; sorted, excludes values',
         'scope_oracle_access':False,'source_hashes':{}}
    source=path/'source';source.mkdir()
    for name in ['overnight/environment.py','overnight/tasks.py','overnight/memory.py','overnight/study.py','llm.py']:
        data=(ROOT/name).read_bytes();flat=name.replace('/','__');(source/flat).write_bytes(data)
        cfg['source_hashes'][flat]=hashlib.sha256(data).hexdigest()
    (path/'config.json').write_text(json.dumps(cfg,indent=2))
    (path/'tasks.json').write_text(json.dumps(TASKS,indent=2))
    jobs=[(mode,trial) for trial in range(args.trials) for mode in cfg['modes']]
    random.Random(20261125).shuffle(jobs)
    progress(f'Started v2 memory: {path.name}; {len(jobs)} sessions, 96 task episodes/session; modes none/exact/lexical/tool-scope.')
    done=0;status='complete';digest=handoff_digest()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run_session,client,m,t,args.w) for m,t in jobs]):
            try:records=future.result()
            except BudgetExceeded:status='budget_stopped';continue
            for r in records:append(path/'episodes.jsonl',r)
            done+=1;progress(f'{path.name}: {done}/{len(jobs)} sessions saved.')
            if digest!=handoff_digest():
                digest=handoff_digest();progress('claude_instruct.md changed; pending review.\n'+(ROOT.parent/'claude_instruct.md').read_text()[-4000:])
    calls=[json.loads(l) for l in (path/'calls.jsonl').read_text().splitlines()]
    finish={'status':status,'sessions':done,'planned_sessions':len(jobs),'calls':len(calls),
            'reported_run_cost_usd':sum(c.get('cost_usd') or 0 for c in calls),
            'budget_before_usd':before,'budget_after_usd':client.budget.total()}
    (path/'finish.json').write_text(json.dumps(finish,indent=2))
    from .memory_report import write_report
    write_report(path)
    progress(f'Finished v2 memory: {path.name}; {status}; reported ${finish["reported_run_cost_usd"]:.6f}.')


if __name__=='__main__':main()
