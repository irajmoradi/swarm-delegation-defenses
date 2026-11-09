"""Finite sequencing for the already authorized overnight studies, sharing the $2 cap."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from ..llm import Budget,CAP,ROOT
from ..run import progress


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study-run',required=True);args=p.parse_args()
    study=ROOT/'runs'/args.study_run
    started=time.monotonic()
    while not (study/'finish.json').exists():
        if time.monotonic()-started>3*3600:raise TimeoutError('Study has not finished in three hours')
        time.sleep(10)
    status=json.loads((study/'finish.json').read_text())['status']
    result={'study':args.study_run,'study_status':status,'stages':[]}
    dest=Path(__file__).parent/'FOLLOW_ON.json'
    if status!='complete':
        result['note']='Follow-on paid studies skipped because the parent study did not complete.'
        dest.write_text(json.dumps(result,indent=2));return
    for module,suffix,minimum in [('memory','-v2-memory',.12),('coordinator','-coordinator',.06)]:
        available=CAP-Budget().total()
        if available<minimum:
            result['stages'].append({'stage':module,'status':'budget_skipped','available_usd':available})
            dest.write_text(json.dumps(result,indent=2));continue
        before={p.name for p in (ROOT/'runs').glob('*'+suffix)}
        progress(f'Overnight sequencer starting {module}; ${available:.4f} conservative headroom. Studies do not overlap.')
        proc=subprocess.run([sys.executable,'-m','planD.overnight.'+module],cwd=ROOT.parent)
        after={p.name for p in (ROOT/'runs').glob('*'+suffix)}
        created=sorted(after-before)
        stage={'stage':module,'returncode':proc.returncode,'run':created[-1] if created else None}
        if stage['run']:
            f=ROOT/'runs'/stage['run']/'finish.json'
            stage['status']=json.loads(f.read_text())['status'] if f.exists() else 'failed_before_finish'
        result['stages'].append(stage);dest.write_text(json.dumps(result,indent=2))
        if proc.returncode:break
    result['budget_after_usd']=Budget().total();dest.write_text(json.dumps(result,indent=2))
    progress('Overnight paid follow-on sequence finished; results in planD/overnight/FOLLOW_ON.json.')


if __name__=='__main__':main()
