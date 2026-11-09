"""An offline counterexample: mixed-pool gains do not imply dependent refusals."""
import json
from pathlib import Path

import numpy as np


def example():
    probabilities=np.eye(3)*.8
    result=[]
    for w in [1,3,6]:
        homogeneous=float(np.mean(1-(1-probabilities)**w))
        mixed=float(np.mean(1-np.prod(1-probabilities,axis=1)**(w/3))) if w%3==0 else None
        oracle=float(np.mean(1-(1-probabilities.max(axis=1))**w))
        result.append({'w':w,'equal_weight_homogeneous':homogeneous,'balanced_mixed':mixed,'task_oracle':oracle})
    return {'label':'Mathematical illustration only; not measured model results',
            'conditional_independence':True,'per_task_model_violation_probabilities':probabilities.tolist(),'results':result}


def main():
    root=Path(__file__).parent;data=example();(root/'HETEROGENEITY_DEMO.json').write_text(json.dumps(data,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    a=np.asarray(data['per_task_model_violation_probabilities'])
    axes[0].imshow(a,vmin=0,vmax=1,cmap='Blues')
    axes[0].set(xticks=range(3),xticklabels=['Model A','Model B','Model C'],yticks=range(3),yticklabels=['Task 1','Task 2','Task 3'],title='Chosen violation probabilities')
    for i in range(3):
        for j in range(3):axes[0].text(j,i,f'{a[i,j]:.1f}',ha='center',va='center',color='white' if a[i,j]>.5 else 'black')
    rows=data['results']
    axes[1].plot([r['w'] for r in rows],[r['equal_weight_homogeneous'] for r in rows],'o-',label='Uniform homogeneous pool')
    selected=[r for r in rows if r['balanced_mixed'] is not None]
    axes[1].plot([r['w'] for r in selected],[r['balanced_mixed'] for r in selected],'o-',label='Balanced mixed pool')
    axes[1].plot([r['w'] for r in rows],[r['task_oracle'] for r in rows],'x--',label='Task-wise oracle reference')
    axes[1].set(xlabel='Attempts W',ylabel='Expected violation probability',ylim=(0,1.04),xticks=[1,3,6],title='All draws conditionally independent')
    axes[1].legend(fontsize=8)
    fig.suptitle('Mathematical illustration — not empirical model results',fontsize=12)
    fig.tight_layout();fig.savefig(root/'HETEROGENEITY_DEMO.png',dpi=180);plt.close(fig)
    (root/'HETEROGENEITY_DEMO.md').write_text('''# A counterexample to a tempting interpretation

This is a mathematical illustration, not an experiment on a language model.
There are three equally likely tasks and three models. On task 1 only model A
has violation probability 0.8; on task 2 only B does; on task 3 only C does.
Every attempted response is independent conditional on task and chosen model.

At W=3, a uniformly chosen fixed model achieves average violation probability
0.3307. A balanced mixed pool achieves 0.8. At W=6, the values are approximately
0.3333 and 0.96. Thus the mixed pool beats every fixed family in aggregate without
any conditional response dependence. The model with highest risk changes by task.

A task-wise oracle that already knows that model still exceeds the mixed pool.
The oracle is only an analytical reference, not a tested defense or coordinator.
See the derivation in `../research/MATHEMATICAL_NOTES.md`.

Reproduce offline: `python -m planD.overnight.mathematical_demo`.
''')
    print(json.dumps(data['results'],indent=2))


if __name__=='__main__':main()
