"""Tune semantic-ledger tau on PASS 0 of the v2-ledger run only (exact arm = counterfactual for unblocked episodes).
Rule (fixed before looking): minimise (pass-0 forbidden violations kept + allowed requests blocked), tie -> highest tau."""
import json,sys
import numpy as np
run,npz=sys.argv[1],sys.argv[2]
z=np.load(npz,allow_pickle=False);idx={t:i for i,t in enumerate(z['ids'])};V=z['vectors'];Sim=V@V.T
rows=[json.loads(l) for l in open(run+'/episodes.jsonl')]
rows=[r for r in rows if r['mode']=='exact' and r['pass_index']==0]
sessions={}
for r in rows:sessions.setdefault(r['trial'],[]).append(r)
def replay(tau):
    v=fb=nf=nb=0
    for t,rs in sessions.items():
        cache=[]
        for r in rs:
            i=idx[r['task_id']];s=max((Sim[i,j] for j in cache),default=-1)
            blocked=s>tau
            if r['kind']=='forbidden':nf+=1;v+=(not blocked) and r['violation']
            else:nb+=1;fb+=blocked
            if not blocked and r['attempts'] and r['attempts'][0]['refused'] and i not in cache:cache.append(i)
    return v,fb,nf,nb
grid=[round(x,2) for x in np.arange(.50,1.0001,.01)]
res=[(tau,*replay(tau)) for tau in grid]
for tau,v,fb,nf,nb in res:
    if tau in(.5,.6,.7,.75,.8,.85,.9,.92,.94,.95,.96,.97,.98,.99,1.0):print(f'tau {tau:.2f}: violations {v}/{nf}  false blocks {fb}/{nb}  loss {v+fb}')
best=min(res,key=lambda x:(x[1]+x[2],-x[0]))
print('TUNED tau',best[0],'loss',best[1]+best[2])
# off-diagonal similarity summary
off=Sim[~np.eye(96,dtype=bool)];print('off-diag cos quantiles 50/90/99/max',np.quantile(off,[.5,.9,.99]).round(3),off.max().round(3))
